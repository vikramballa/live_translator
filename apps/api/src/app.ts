import {
  type ApiError,
  type ApiErrorCode,
  JoinRequest,
  type JoinResponse,
  RoomId,
} from "@lt/contracts";
import { type Context, Hono } from "hono";
import { bodyLimit } from "hono/body-limit";
import { getConnInfo, serveStatic } from "hono/bun";
import { secureHeaders } from "hono/secure-headers";
import { env } from "./env.ts";
import * as lk from "./livekit.ts";
import { RateLimiter } from "./rateLimit.ts";
import * as rooms from "./rooms.ts";

export type Deps = {
  connected: (roomId: string) => Promise<Set<string>>;
  ensureRoom: (roomId: string) => Promise<void>;
  token: typeof lk.participantToken;
  summonAgent: (roomId: string) => Promise<boolean>;
};

const liveDeps: Deps = {
  connected: lk.connectedIdentities,
  ensureRoom: lk.ensureRoom,
  token: lk.participantToken,
  summonAgent: lk.summonAgent,
};

const STATUS: Record<ApiErrorCode, 400 | 404 | 409 | 410 | 422 | 429 | 500> = {
  bad_request: 400,
  not_found: 404,
  full: 409,
  expired: 410,
  unsupported_pair: 422,
  rate_limited: 429,
  internal: 500,
};

function fail(c: Context, error: ApiErrorCode, message?: string) {
  return c.json<ApiError>({ error, message }, STATUS[error]);
}

function clientIp(c: Context): string {
  if (process.env.TRUST_PROXY === "1") {
    // The proxy (Caddy) appends the address it saw, so only the last entry is
    // trustworthy; earlier ones are whatever the client sent.
    const fwd = c.req.header("x-forwarded-for")?.split(",").at(-1)?.trim();
    if (fwd) return fwd;
  }
  try {
    return getConnInfo(c).remote.address ?? "unknown";
  } catch {
    return "unknown";
  }
}

/** Origins the browser may connect to: this site and LiveKit (WebSocket + its HTTP checks). */
function connectSources(): string[] {
  const lk = new URL(env.LIVEKIT_PUBLIC_URL ?? env.LIVEKIT_URL);
  const http = new URL(lk);
  http.protocol = lk.protocol === "wss:" ? "https:" : "http:";
  return ["'self'", lk.origin, http.origin];
}

export function createApp(deps: Deps = liveDeps) {
  const createLimiter = new RateLimiter(30, 3600_000); // rooms per IP per hour
  const joinLimiter = new RateLimiter(120, 3600_000);
  const infoLimiter = new RateLimiter(600, 3600_000);

  const app = new Hono();
  app.use(
    "*",
    secureHeaders({
      permissionsPolicy: { microphone: ["self"] },
      contentSecurityPolicy: {
        defaultSrc: ["'self'"],
        connectSrc: connectSources(),
        imgSrc: ["'self'", "data:"], // QR code
        mediaSrc: ["'self'", "blob:"],
        objectSrc: ["'none'"],
        baseUri: ["'none'"],
        frameAncestors: ["'none'"],
        formAction: ["'self'"],
      },
    }),
  );
  // Requests are a few dozen bytes; refuse anything large before parsing it.
  app.use("/api/*", bodyLimit({ maxSize: 4096, onError: (c) => fail(c, "bad_request") }));

  app.get("/api/health", (c) => c.json({ ok: true }));

  app.post("/api/rooms", async (c) => {
    if (!createLimiter.take(clientIp(c))) return fail(c, "rate_limited");
    return c.json(await rooms.createRoom(), 201);
  });

  app.get("/api/rooms/:id", async (c) => {
    if (!infoLimiter.take(clientIp(c))) return fail(c, "rate_limited");
    const id = RoomId.safeParse(c.req.param("id"));
    if (!id.success) return fail(c, "not_found");
    const info = await rooms.roomInfo(id.data, () => deps.connected(id.data));
    if (info === "not_found" || info === "expired") return fail(c, info);
    return c.json(info);
  });

  app.post("/api/rooms/:id/join", async (c) => {
    if (!joinLimiter.take(clientIp(c))) return fail(c, "rate_limited");
    const id = RoomId.safeParse(c.req.param("id"));
    if (!id.success) return fail(c, "not_found");
    const body = JoinRequest.safeParse(await c.req.json().catch(() => null));
    if (!body.success) return fail(c, "bad_request");

    const seat = await rooms.takeSeat(id.data, body.data, await deps.connected(id.data));
    if (!seat.ok) return fail(c, seat.error);

    await deps.ensureRoom(id.data);
    const token = await deps.token(
      id.data,
      seat.identity,
      body.data.lang,
      body.data.name,
      seat.expiresAt,
    );
    // Do not block the response on the agent; it joins within a second or two.
    void deps.summonAgent(id.data);
    return c.json<JoinResponse>({
      token,
      livekitUrl: env.LIVEKIT_PUBLIC_URL ?? env.LIVEKIT_URL,
      identity: seat.identity,
      seatKey: seat.seatKey,
      partnerLang: seat.partnerLang,
    });
  });

  app.onError((err, c) => {
    console.error("unhandled error:", err.message);
    return fail(c, "internal");
  });

  // Production: serve the built web app (single process behind Caddy).
  if (env.WEB_DIST) {
    app.use("/assets/*", serveStatic({ root: env.WEB_DIST }));
    app.use("*", serveStatic({ root: env.WEB_DIST }));
    app.get("*", serveStatic({ path: `${env.WEB_DIST}/index.html` }));
  }
  return app;
}
