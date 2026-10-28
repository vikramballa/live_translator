/**
 * API tests against the real local Postgres (DATABASE_URL), with LiveKit and
 * the agent replaced by fakes.
 */
import { afterAll, beforeEach, describe, expect, test } from "bun:test";
import { createApp, type Deps } from "../src/app.ts";
import { sql } from "../src/db.ts";
import { RateLimiter } from "../src/rateLimit.ts";
import { liveSeats, RESERVATION_MS } from "../src/rooms.ts";

let connected = new Map<string, Set<string>>();
const summoned: string[] = [];
const deps: Deps = {
  connected: async (id) => connected.get(id) ?? new Set(),
  ensureRoom: async () => {},
  token: async (room, identity, lang) => `token:${room}:${identity}:${lang}`,
  summonAgent: async (id) => {
    summoned.push(id);
    return true;
  },
};
const app = createApp(deps);
const created: string[] = [];

async function newRoom(): Promise<string> {
  const res = await app.request("/api/rooms", { method: "POST" });
  expect(res.status).toBe(201);
  const body = (await res.json()) as { roomId: string };
  created.push(body.roomId);
  return body.roomId;
}

function join(roomId: string, body: object, headers: Record<string, string> = {}) {
  return app.request(`/api/rooms/${roomId}/join`, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

type Joined = { identity: string; seatKey: string; token: string };

beforeEach(() => {
  connected = new Map();
});

afterAll(async () => {
  for (const id of created) await sql`DELETE FROM rooms WHERE id = ${id}`;
  await sql.close();
});

describe("rooms", () => {
  test("create returns a 22-char unguessable id", async () => {
    const id = await newRoom();
    expect(id).toMatch(/^[A-Za-z0-9_-]{22}$/);
  });

  test("two people join, third is refused", async () => {
    const id = await newRoom();
    const a = await join(id, { lang: "te" });
    expect(a.status).toBe(200);
    const aBody = (await a.json()) as {
      identity: string;
      partnerLang: string | null;
      token: string;
    };
    expect(aBody.partnerLang).toBeNull();
    expect(aBody.token).toContain(":te");

    const b = await join(id, { lang: "en" });
    expect(b.status).toBe(200);
    expect(((await b.json()) as { partnerLang: string }).partnerLang).toBe("te");

    const c = await join(id, { lang: "en" });
    expect(c.status).toBe(409);
    expect(summoned).toContain(id);
  });

  test("unsupported language pair is refused before the call", async () => {
    const id = await newRoom();
    expect((await join(id, { lang: "hi" })).status).toBe(200);
    const res = await join(id, { lang: "zh" }); // hi↔zh is not a v1 pair
    expect(res.status).toBe(422);
    expect(((await res.json()) as { error: string }).error).toBe("unsupported_pair");
  });

  test("a browser can rejoin with its seat key without taking a second seat", async () => {
    const id = await newRoom();
    const a = (await (await join(id, { lang: "te" })).json()) as Joined;
    await join(id, { lang: "en" });
    const again = await join(id, { lang: "te", seatKey: a.seatKey });
    expect(again.status).toBe(200);
    expect(((await again.json()) as Joined).identity).toBe(a.identity);
  });
  test("a stale, never-connected seat is freed", async () => {
    const id = await newRoom();
    await join(id, { lang: "te" });
    await join(id, { lang: "en" });
    await sql`UPDATE room_seats SET issued_at = now() - interval '10 minutes' WHERE room_id = ${id}`;
    expect((await join(id, { lang: "en" })).status).toBe(200);
  });

  test("a connected seat is never freed", async () => {
    const id = await newRoom();
    const a = (await (await join(id, { lang: "te" })).json()) as { identity: string };
    const b = (await (await join(id, { lang: "en" })).json()) as { identity: string };
    await sql`UPDATE room_seats SET issued_at = now() - interval '10 minutes' WHERE room_id = ${id}`;
    connected.set(id, new Set([a.identity, b.identity]));
    expect((await join(id, { lang: "en" })).status).toBe(409);
  });

  test("expired rooms are gone", async () => {
    const id = await newRoom();
    await sql`UPDATE rooms SET expires_at = now() - interval '1 minute' WHERE id = ${id}`;
    expect((await join(id, { lang: "te" })).status).toBe(410);
    expect((await app.request(`/api/rooms/${id}`)).status).toBe(410);
  });

  test("room info shows languages, never names", async () => {
    const id = await newRoom();
    await join(id, { lang: "te", name: "Ravi" });
    const info = (await (await app.request(`/api/rooms/${id}`)).json()) as Record<string, unknown>;
    expect(info.langs).toEqual(["te"]);
    expect(JSON.stringify(info)).not.toContain("Ravi");
  });

  test("bad input is rejected", async () => {
    const id = await newRoom();
    expect((await join(id, { lang: "fr" })).status).toBe(400);
    expect((await join("not-a-room", { lang: "te" })).status).toBe(404);
    expect((await join("AAAAAAAAAAAAAAAAAAAAAA", { lang: "te" })).status).toBe(404);
  });

  test("concurrent joins never exceed two seats", async () => {
    const id = await newRoom();
    const results = await Promise.all(
      Array.from({ length: 6 }, (_, i) => join(id, { lang: i % 2 ? "te" : "en" })),
    );
    const ok = results.filter((r) => r.status === 200).length;
    expect(ok).toBe(2);
    const [{ n }] = await sql`SELECT count(*)::int AS n FROM room_seats WHERE room_id = ${id}`;
    expect(n).toBe(2);
  });
});

describe("security", () => {
  test("the partner cannot take over a seat with its (public) identity", async () => {
    const id = await newRoom();
    const a = (await (await join(id, { lang: "te" })).json()) as Joined;
    const b = (await (await join(id, { lang: "en" })).json()) as Joined;
    connected.set(id, new Set([a.identity, b.identity]));
    // The old API accepted { identity } and handed out a token for it.
    expect((await join(id, { lang: "te", identity: a.identity })).status).toBe(409);
    // A seat key belongs to one seat: B's key gives B's seat back, never A's.
    const again = (await (await join(id, { lang: "en", seatKey: b.seatKey })).json()) as Joined;
    expect(again.identity).toBe(b.identity);
    const forged = await join(id, { lang: "te", seatKey: "A".repeat(32) });
    expect(forged.status).toBe(409);
  });

  test("seat keys are stored hashed", async () => {
    const id = await newRoom();
    const a = (await (await join(id, { lang: "te" })).json()) as Joined;
    const [row] = await sql`SELECT key_hash FROM room_seats WHERE room_id = ${id}`;
    expect(row.key_hash).toMatch(/^[0-9a-f]{64}$/);
    expect(row.key_hash).not.toContain(a.seatKey);
  });

  test("a spoofed X-Forwarded-For does not escape the rate limit", async () => {
    const limited = createApp(deps);
    process.env.TRUST_PROXY = "1";
    try {
      const statuses: number[] = [];
      for (let i = 0; i < 31; i++) {
        const res = await limited.request("/api/rooms", {
          method: "POST",
          // The client's own header first, then the address Caddy appended.
          headers: { "x-forwarded-for": `10.0.0.${i}, 203.0.113.7` },
        });
        if (res.status === 201) created.push(((await res.json()) as { roomId: string }).roomId);
        statuses.push(res.status);
      }
      expect(statuses.filter((s) => s === 201)).toHaveLength(30);
      expect(statuses.at(-1)).toBe(429);
    } finally {
      delete process.env.TRUST_PROXY;
    }
  });

  test("large request bodies are refused", async () => {
    const id = await newRoom();
    expect((await join(id, { lang: "te", pad: "x".repeat(100_000) })).status).toBe(400);
  });

  test("responses carry a Content-Security-Policy", async () => {
    const csp = (await app.request("/api/health")).headers.get("content-security-policy") ?? "";
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("ws://127.0.0.1:7880");
  });
});

describe("units", () => {
  test("rate limiter", () => {
    let t = 0;
    const rl = new RateLimiter(2, 1000, () => t);
    expect(rl.take("a")).toBe(true);
    expect(rl.take("a")).toBe(true);
    expect(rl.take("a")).toBe(false);
    expect(rl.take("b")).toBe(true);
    t = 1001;
    expect(rl.take("a")).toBe(true);
  });

  test("liveSeats keeps connected and recent seats", () => {
    const now = Date.now();
    const old = new Date(now - RESERVATION_MS - 1);
    const seats = [
      { identity: "u1", lang: "te" as const, issued_at: old },
      { identity: "u2", lang: "en" as const, issued_at: old },
      { identity: "u3", lang: "en" as const, issued_at: new Date(now) },
    ];
    expect(liveSeats(seats, new Set(["u1"]), now).map((s) => s.identity)).toEqual(["u1", "u3"]);
  });
});
