import {
  type ApiErrorCode,
  type CreateRoomResponse,
  isSupportedPair,
  type JoinRequest,
  type Lang,
  type RoomInfo,
} from "@lt/contracts";
import { sql } from "./db.ts";
import { env } from "./env.ts";
import { hashSeatKey, newIdentity, newRoomId, newSeatKey } from "./ids.ts";

/** A seat given out but not yet connected stays reserved this long. */
export const RESERVATION_MS = 90_000;
const MAX_SEATS = 2;

type Seat = { identity: string; lang: Lang; issued_at: Date; key_hash?: string | null };

type SeatResult =
  | { ok: true; identity: string; seatKey: string; partnerLang: Lang | null; expiresAt: Date }
  | { ok: false; error: ApiErrorCode };

export async function createRoom(): Promise<CreateRoomResponse> {
  const roomId = newRoomId();
  const expires = new Date(Date.now() + env.ROOM_TTL_HOURS * 3600_000);
  await sql`INSERT INTO rooms (id, expires_at) VALUES (${roomId}, ${expires})`;
  return { roomId, expiresAt: expires.toISOString() };
}

/** Seats still in use: connected to LiveKit, or recently issued. */
export function liveSeats(seats: Seat[], connected: Set<string>, now = Date.now()): Seat[] {
  return seats.filter(
    (s) => connected.has(s.identity) || now - new Date(s.issued_at).getTime() < RESERVATION_MS,
  );
}

/** `connected` is only called for a live room, so unknown ids never reach LiveKit. */
export async function roomInfo(
  roomId: string,
  connected: () => Promise<Set<string>>,
): Promise<RoomInfo | "not_found" | "expired"> {
  const [room] = await sql`SELECT id, expires_at FROM rooms WHERE id = ${roomId}`;
  if (!room) return "not_found";
  if (new Date(room.expires_at) <= new Date()) return "expired";
  const seats: Seat[] =
    await sql`SELECT identity, lang, issued_at FROM room_seats WHERE room_id = ${roomId}`;
  const live = liveSeats(seats, await connected());
  return {
    roomId,
    expiresAt: new Date(room.expires_at).toISOString(),
    langs: live.map((s) => s.lang),
    full: live.length >= MAX_SEATS,
  };
}

/**
 * Give the caller a seat. Runs in one transaction with the room row locked,
 * so two people joining at the same instant cannot create a third seat.
 * `connected` (identities in the LiveKit room) is fetched before the call.
 */
export async function takeSeat(
  roomId: string,
  req: JoinRequest,
  connected: Set<string>,
): Promise<SeatResult> {
  return sql.begin(async (tx) => {
    const [room] = await tx`SELECT id, expires_at FROM rooms WHERE id = ${roomId} FOR UPDATE`;
    if (!room) return { ok: false, error: "not_found" } as const;
    if (new Date(room.expires_at) <= new Date()) return { ok: false, error: "expired" } as const;

    const seats: Seat[] =
      await tx`SELECT identity, lang, issued_at, key_hash FROM room_seats WHERE room_id = ${roomId}`;
    const live = liveSeats(seats, connected);
    for (const stale of seats.filter((s) => !live.includes(s))) {
      await tx`DELETE FROM room_seats WHERE room_id = ${roomId} AND identity = ${stale.identity}`;
    }

    // A browser that already holds a seat (page reload) proves it with its seat key
    // and keeps its identity. The identity alone is not enough: the partner sees it.
    const keyHash = req.seatKey ? hashSeatKey(req.seatKey) : null;
    const own = keyHash ? live.find((s) => s.key_hash === keyHash) : undefined;
    const identity = own?.identity ?? newIdentity();
    const seatKey = own && req.seatKey ? req.seatKey : newSeatKey();
    const others = live.filter((s) => s.identity !== identity);
    if (others.length >= MAX_SEATS) return { ok: false, error: "full" } as const;

    const partner = others[0];
    if (partner && partner.lang !== req.lang && !isSupportedPair(partner.lang, req.lang)) {
      return { ok: false, error: "unsupported_pair" } as const;
    }

    await tx`INSERT INTO room_seats (room_id, identity, lang, key_hash)
             VALUES (${roomId}, ${identity}, ${req.lang}, ${hashSeatKey(seatKey)})
             ON CONFLICT (room_id, identity) DO UPDATE SET lang = EXCLUDED.lang, issued_at = now()`;
    return {
      ok: true,
      identity,
      seatKey,
      partnerLang: partner?.lang ?? null,
      expiresAt: new Date(room.expires_at),
    } as const;
  });
}

export async function deleteExpiredRooms(): Promise<number> {
  const rows = await sql`DELETE FROM rooms WHERE expires_at < now() RETURNING id`;
  return rows.length;
}
