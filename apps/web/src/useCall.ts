import {
  AGENT_IDENTITY,
  AgentEvent,
  type ControlMessage,
  type JoinResponse,
  type KeyFact,
  type Lang,
  TOPIC_CONTROL,
  TOPIC_EVENTS,
  translationTrackName,
} from "@lt/contracts";
import {
  type Participant,
  type RemoteAudioTrack,
  type RemoteParticipant,
  type RemoteTrack,
  type RemoteTrackPublication,
  Room,
  RoomEvent,
  Track,
} from "livekit-client";
import { useCallback, useEffect, useRef, useState } from "react";

export type AgentState =
  | "offline"
  | "waiting"
  | "loading"
  | "ready"
  | "unsupported"
  | "same_language";
export type Connection =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "ended"
  | "mic_denied"
  | "error";

export type Message = {
  key: string;
  mine: boolean;
  seq: number;
  srcLang?: Lang;
  tgtLang?: Lang;
  srcText?: string;
  tgtText?: string;
  facts: KeyFact[];
  flags: string[];
  failed?: boolean;
  at: number;
};

export type CallState = {
  connection: Connection;
  agent: AgentState;
  partnerPresent: boolean;
  partnerLeft: boolean;
  messages: Message[];
  partials: Record<string, string>; // "me" | "them" → live text
  speaking: { me: boolean; them: boolean };
  facts: KeyFact[];
  notice: "didnt_understand" | null;
  muted: boolean;
};

const initial: CallState = {
  connection: "connecting",
  agent: "offline",
  partnerPresent: false,
  partnerLeft: false,
  messages: [],
  partials: {},
  speaking: { me: false, them: false },
  facts: [],
  notice: null,
  muted: false,
};

const decoder = new TextDecoder();
const encoder = new TextEncoder();

export function useCall(join: JoinResponse | null, originalVolume: number) {
  const [state, setState] = useState<CallState>(initial);
  const roomRef = useRef<Room | null>(null);
  const audioHost = useRef<HTMLDivElement | null>(null);
  const originalTrack = useRef<RemoteAudioTrack | null>(null);
  const volumeRef = useRef(originalVolume);

  const patch = useCallback((fn: (s: CallState) => Partial<CallState>) => {
    setState((s) => ({ ...s, ...fn(s) }));
  }, []);

  useEffect(() => {
    if (!join) return;
    const me = join.identity;
    const room = new Room({
      adaptiveStream: false,
      dynacast: false,
      audioCaptureDefaults: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    roomRef.current = room;
    const host = document.createElement("div");
    host.hidden = true;
    document.body.appendChild(host);
    audioHost.current = host;

    const wanted = (pub: RemoteTrackPublication, p: RemoteParticipant) =>
      pub.kind === Track.Kind.Audio &&
      (p.identity === AGENT_IDENTITY
        ? pub.trackName === translationTrackName(me) // only my translation
        : true); // the partner's original voice

    const consider = (pub: RemoteTrackPublication, p: RemoteParticipant) => {
      if (wanted(pub, p) && !pub.isSubscribed) pub.setSubscribed(true);
    };

    const syncPresence = () => {
      const humans = [...room.remoteParticipants.values()].filter(
        (p) => p.identity !== AGENT_IDENTITY,
      );
      const agentHere = room.remoteParticipants.has(AGENT_IDENTITY);
      patch((s) => ({
        partnerPresent: humans.length > 0,
        partnerLeft:
          s.partnerPresent && humans.length === 0 ? true : humans.length ? false : s.partnerLeft,
        agent: agentHere ? (s.agent === "offline" ? "waiting" : s.agent) : "offline",
      }));
    };

    room
      .on(RoomEvent.TrackPublished, consider)
      .on(RoomEvent.TrackSubscribed, (track: RemoteTrack, _pub, p: RemoteParticipant) => {
        if (track.kind !== Track.Kind.Audio) return;
        const el = track.attach();
        host.appendChild(el);
        if (p.identity !== AGENT_IDENTITY) {
          originalTrack.current = track as RemoteAudioTrack;
          (track as RemoteAudioTrack).setVolume(volumeRef.current);
        }
      })
      .on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
        for (const el of track.detach()) el.remove();
      })
      .on(RoomEvent.ParticipantConnected, syncPresence)
      .on(RoomEvent.ParticipantDisconnected, syncPresence)
      .on(RoomEvent.Reconnecting, () => patch(() => ({ connection: "reconnecting" })))
      .on(RoomEvent.Reconnected, () => patch(() => ({ connection: "connected" })))
      .on(RoomEvent.Disconnected, () =>
        patch((s) => ({ connection: s.connection === "mic_denied" ? s.connection : "ended" })),
      )
      .on(
        RoomEvent.DataReceived,
        (payload: Uint8Array, from?: Participant, _k?: unknown, topic?: string) => {
          // Only the translator may send captions and Key-Facts; the partner can
          // publish data too and must not be able to forge them.
          if (topic !== TOPIC_EVENTS || from?.identity !== AGENT_IDENTITY) return;
          let parsed: AgentEvent;
          try {
            parsed = AgentEvent.parse(JSON.parse(decoder.decode(payload)));
          } catch {
            return;
          }
          handleEvent(parsed, me, patch);
        },
      );

    (async () => {
      try {
        await room.connect(join.livekitUrl, join.token, { autoSubscribe: false });
        for (const p of room.remoteParticipants.values()) {
          for (const pub of p.trackPublications.values()) consider(pub, p);
        }
        syncPresence();
        patch(() => ({ connection: "connected" }));
        await room.startAudio();
        try {
          await room.localParticipant.setMicrophoneEnabled(true);
        } catch {
          patch(() => ({ connection: "mic_denied" }));
        }
      } catch {
        patch(() => ({ connection: "error" }));
      }
    })();

    return () => {
      room.disconnect();
      host.remove();
      roomRef.current = null;
    };
  }, [join, patch]);

  useEffect(() => {
    volumeRef.current = originalVolume;
    originalTrack.current?.setVolume(originalVolume);
  }, [originalVolume]);

  const send = useCallback((msg: ControlMessage) => {
    const room = roomRef.current;
    if (!room) return;
    void room.localParticipant.publishData(encoder.encode(JSON.stringify(msg)), {
      reliable: true,
      topic: TOPIC_CONTROL,
      destinationIdentities: [AGENT_IDENTITY],
    });
  }, []);

  const toggleMute = useCallback(async () => {
    const room = roomRef.current;
    if (!room) return;
    const wasOn = room.localParticipant.isMicrophoneEnabled;
    try {
      await room.localParticipant.setMicrophoneEnabled(!wasOn);
      patch(() => ({ muted: wasOn }));
    } catch {
      patch(() => ({ connection: "mic_denied" }));
    }
  }, [patch]);

  /** Ask for the microphone again, e.g. after the person allowed it in settings. */
  const retryMic = useCallback(async () => {
    const room = roomRef.current;
    if (!room) return;
    try {
      await room.localParticipant.setMicrophoneEnabled(true);
      patch(() => ({ connection: "connected", muted: false }));
    } catch {
      patch(() => ({ connection: "mic_denied" }));
    }
  }, [patch]);

  const leave = useCallback(() => {
    roomRef.current?.disconnect();
    patch(() => ({ connection: "ended" }));
  }, [patch]);

  const dismissNotice = useCallback(() => patch(() => ({ notice: null })), [patch]);

  // Keep the screen on during a call so captions stay readable.
  const live = state.connection !== "ended" && state.connection !== "error";
  useEffect(() => {
    if (!live || !("wakeLock" in navigator)) return;
    let lock: WakeLockSentinel | null = null;
    let cancelled = false;
    const acquire = () => {
      if (document.visibilityState !== "visible") return;
      navigator.wakeLock
        .request("screen")
        .then((l) => {
          if (cancelled) void l.release();
          else lock = l;
        })
        .catch(() => {
          /* not allowed (battery saver, iframe): the screen may dim */
        });
    };
    acquire();
    document.addEventListener("visibilitychange", acquire);
    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", acquire);
      void lock?.release();
    };
  }, [live]);

  return { state, send, toggleMute, retryMic, leave, dismissNotice };
}

function handleEvent(
  ev: AgentEvent,
  me: string,
  patch: (fn: (s: CallState) => Partial<CallState>) => void,
) {
  switch (ev.type) {
    case "state":
      patch(() => ({ agent: ev.state }));
      break;
    case "speaking": {
      const who = ev.identity === me ? "me" : "them";
      patch((s) => ({
        speaking: { ...s.speaking, [who]: ev.active },
        partials: ev.active ? s.partials : { ...s.partials, [who]: "" },
      }));
      break;
    }
    case "partial": {
      const who = ev.identity === me ? "me" : "them";
      patch((s) => ({ partials: { ...s.partials, [who]: ev.text } }));
      break;
    }
    case "caption": {
      const mine = ev.identity === me;
      const who = mine ? "me" : "them";
      const msg: Message = {
        key: `${ev.identity}:${ev.seq}`,
        mine,
        seq: ev.seq,
        srcLang: ev.srcLang,
        tgtLang: ev.tgtLang,
        srcText: ev.srcText,
        tgtText: ev.tgtText,
        facts: ev.facts ?? [],
        flags: ev.flags ?? [],
        failed: ev.error || ev.empty,
        at: Date.now(),
      };
      patch((s) => {
        const facts = [...s.facts];
        for (const f of msg.facts) {
          if (!facts.some((x) => x.display === f.display)) facts.push(f);
        }
        return {
          messages: [...s.messages.filter((m) => m.key !== msg.key), msg].slice(-200),
          partials: { ...s.partials, [who]: "" },
          facts: facts.slice(-12),
        };
      });
      break;
    }
    case "notice":
      patch(() => ({ notice: ev.kind }));
      break;
  }
}
