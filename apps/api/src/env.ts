import { z } from "zod";

const Env = z.object({
  PORT: z.coerce.number().default(3000),
  HOST: z.string().default("127.0.0.1"),
  DATABASE_URL: z.string().default("postgres://127.0.0.1:5432/live_translator"),
  LIVEKIT_URL: z.string().default("ws://127.0.0.1:7880"),
  /** URL browsers use to reach LiveKit (differs from LIVEKIT_URL behind a proxy). */
  LIVEKIT_PUBLIC_URL: z.string().optional(),
  LIVEKIT_API_KEY: z.string().default("devkey"),
  LIVEKIT_API_SECRET: z.string().default("secret"),
  AGENT_URL: z.string().default("http://127.0.0.1:8765"),
  AGENT_SHARED_SECRET: z.string().default(""),
  ROOM_TTL_HOURS: z.coerce.number().default(24),
  /** Serve the built web app from this directory (production, single process). */
  WEB_DIST: z.string().optional(),
  NODE_ENV: z.string().default("development"),
});

export const env = Env.parse(process.env);

if (env.NODE_ENV === "production") {
  if (env.LIVEKIT_API_SECRET.length < 32 || env.AGENT_SHARED_SECRET.length < 16) {
    throw new Error("Refusing to start in production with development secrets");
  }
}
