/**
 * Shared contracts between the web app, the Bun API and (by convention) the
 * Python agent. Languages and enabled pairs come from config/languages.json,
 * the single source of truth that the agent also reads.
 */
import { z } from "zod";
import languagesConfig from "../../../config/languages.json" with { type: "json" };

// No `new Function` code generation: the site's Content-Security-Policy forbids
// it, and Zod's probe for it would show up as a policy violation.
z.config({ jitless: true });

export const LANGS = ["te", "hi", "en", "zh"] as const;
export const Lang = z.enum(LANGS);
export type Lang = z.infer<typeof Lang>;

export type LanguageInfo = { name: string; native: string; script: string };
export const LANGUAGES: Record<Lang, LanguageInfo> = languagesConfig.languages;

export const PAIRS: ReadonlyArray<readonly [Lang, Lang]> = languagesConfig.pairs.map(
  ([a, b]) => [Lang.parse(a), Lang.parse(b)] as const,
);

/** True when a call between these two languages is supported in v1. */
export function isSupportedPair(a: Lang, b: Lang): boolean {
  return PAIRS.some(([x, y]) => (x === a && y === b) || (x === b && y === a));
}

/** Languages someone speaking `lang` can be paired with. */
export function partnersOf(lang: Lang): Lang[] {
  return PAIRS.flatMap(([x, y]) => (x === lang ? [y] : y === lang ? [x] : []));
}

// --- REST API ---

/** Room ids are 128-bit random, base64url (22 chars). The id *is* the secret link. */
export const RoomId = z.string().regex(/^[A-Za-z0-9_-]{22}$/);
/** Participant identities are random but not secret: LiveKit shows them to the partner. */
export const Identity = z.string().regex(/^u_[A-Za-z0-9_-]{16}$/);
/** Secret a browser keeps to reclaim its own seat after a reload (only its hash is stored). */
export const SeatKey = z.string().regex(/^[A-Za-z0-9_-]{32}$/);

export const CreateRoomResponse = z.object({ roomId: RoomId, expiresAt: z.string() });
export type CreateRoomResponse = z.infer<typeof CreateRoomResponse>;

export const RoomInfo = z.object({
  roomId: RoomId,
  expiresAt: z.string(),
  /** Languages of people already holding a seat (never names). */
  langs: z.array(Lang),
  full: z.boolean(),
});
export type RoomInfo = z.infer<typeof RoomInfo>;

export const JoinRequest = z.object({
  lang: Lang,
  name: z.string().trim().max(40).optional(),
  seatKey: SeatKey.optional(),
});
export type JoinRequest = z.infer<typeof JoinRequest>;

export const JoinResponse = z.object({
  token: z.string(),
  livekitUrl: z.string(),
  identity: Identity,
  seatKey: SeatKey,
  partnerLang: Lang.nullable(),
});
export type JoinResponse = z.infer<typeof JoinResponse>;

export const ApiErrorCode = z.enum([
  "not_found",
  "expired",
  "full",
  "unsupported_pair",
  "bad_request",
  "rate_limited",
  "internal",
]);
export type ApiErrorCode = z.infer<typeof ApiErrorCode>;
export const ApiError = z.object({ error: ApiErrorCode, message: z.string().optional() });
export type ApiError = z.infer<typeof ApiError>;

// --- Data channel (agent <-> browsers) ---

export const AGENT_IDENTITY = "translator";
export const TOPIC_EVENTS = "lt.events"; // agent → browsers
export const TOPIC_CONTROL = "lt.control"; // browsers → agent
/** The agent publishes one translated track per listener, named for them. */
export const translationTrackName = (identity: string) => `tr:${identity}`;

export const KeyFact = z.object({
  kind: z.enum(["money", "percent", "phone", "quantity", "number"]),
  value: z.string(),
  unit: z.string().nullable(),
  display: z.string(),
});
export type KeyFact = z.infer<typeof KeyFact>;

export const AgentEvent = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("state"),
    state: z.enum(["waiting", "loading", "ready", "unsupported", "same_language"]),
    langs: z.array(Lang).optional(),
  }),
  z.object({ type: z.literal("speaking"), identity: z.string(), active: z.boolean() }),
  z.object({
    type: z.literal("partial"),
    identity: z.string(),
    seq: z.number(),
    lang: Lang,
    text: z.string(),
  }),
  z.object({
    type: z.literal("caption"),
    identity: z.string(),
    seq: z.number(),
    empty: z.boolean().optional(),
    error: z.boolean().optional(),
    srcLang: Lang.optional(),
    tgtLang: Lang.optional(),
    srcText: z.string().optional(),
    tgtText: z.string().optional(),
    facts: z.array(KeyFact).optional(),
    flags: z.array(z.string()).optional(),
  }),
  z.object({ type: z.literal("notice"), kind: z.enum(["didnt_understand"]) }),
]);
export type AgentEvent = z.infer<typeof AgentEvent>;

export const ControlMessage = z.discriminatedUnion("type", [
  z.object({ type: z.literal("repeat") }),
  z.object({ type: z.literal("didnt_understand") }),
  z.object({ type: z.literal("speech_rate"), value: z.number().min(0.7).max(1.3) }),
]);
export type ControlMessage = z.infer<typeof ControlMessage>;
