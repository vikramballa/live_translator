import { AGENT_IDENTITY, type Lang } from "@lt/contracts";
import { AccessToken, RoomServiceClient, TrackSource } from "livekit-server-sdk";
import { env } from "./env.ts";

const httpUrl = env.LIVEKIT_URL.replace(/^ws/, "http");
const rooms = new RoomServiceClient(httpUrl, env.LIVEKIT_API_KEY, env.LIVEKIT_API_SECRET);

/** Identities of humans currently connected to a LiveKit room. */
export async function connectedIdentities(roomId: string): Promise<Set<string>> {
  try {
    const people = await rooms.listParticipants(roomId);
    return new Set(people.map((p) => p.identity).filter((id) => id !== AGENT_IDENTITY));
  } catch {
    return new Set(); // room not created yet
  }
}

/** Create the LiveKit room with a hard cap: two people plus the translator. */
export async function ensureRoom(roomId: string): Promise<void> {
  await rooms.createRoom({ name: roomId, maxParticipants: 3, emptyTimeout: 10 * 60 });
}

const MAX_TOKEN_S = 6 * 3600;

export async function participantToken(
  roomId: string,
  identity: string,
  lang: Lang,
  name: string | undefined,
  roomExpiresAt: Date,
): Promise<string> {
  // Never valid longer than the room link itself.
  const untilExpiry = Math.floor((roomExpiresAt.getTime() - Date.now()) / 1000);
  const at = new AccessToken(env.LIVEKIT_API_KEY, env.LIVEKIT_API_SECRET, {
    identity,
    name: name || undefined,
    metadata: JSON.stringify({ lang }),
    ttl: Math.max(60, Math.min(MAX_TOKEN_S, untilExpiry)),
  });
  at.addGrant({
    roomJoin: true,
    room: roomId,
    canPublish: true,
    canPublishSources: [TrackSource.MICROPHONE],
    canSubscribe: true,
    canPublishData: true,
    canUpdateOwnMetadata: false,
  });
  return at.toJwt();
}

/** Ask the translator agent to join. Failures are logged, not fatal. */
export async function summonAgent(roomId: string): Promise<boolean> {
  try {
    const res = await fetch(`${env.AGENT_URL}/rooms/${encodeURIComponent(roomId)}/join`, {
      method: "POST",
      headers: { "x-agent-secret": env.AGENT_SHARED_SECRET },
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch (err) {
    console.error(`agent unreachable at ${env.AGENT_URL}:`, (err as Error).message);
    return false;
  }
}
