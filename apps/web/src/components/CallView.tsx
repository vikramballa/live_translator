import { type JoinResponse, LANGUAGES, type Lang } from "@lt/contracts";
import { useEffect, useRef, useState } from "react";
import type { Strings } from "../i18n.ts";
import { navigate } from "../router.ts";
import { storage } from "../storage.ts";
import { type CallState, type Message, useCall } from "../useCall.ts";
import { ShareCard } from "./ShareCard.tsx";
import { Banner, PrimaryButton } from "./ui.tsx";

type Props = { roomId: string; lang: Lang; join: JoinResponse; t: Strings };

export function CallView({ roomId, lang, join, t }: Props) {
  const [volume, setVolume] = useState(storage.originalVolume);
  const { state, send, toggleMute, leave, dismissNotice } = useCall(join, volume);
  const url = `${location.origin}/r/${roomId}`;

  useEffect(() => storage.setOriginalVolume(volume), [volume]);
  useEffect(() => {
    if (!state.notice) return;
    const id = setTimeout(dismissNotice, 8000);
    return () => clearTimeout(id);
  }, [state.notice, dismissNotice]);

  if (state.connection === "ended") {
    return (
      <main className="flex flex-1 flex-col justify-center gap-6 px-5" lang={lang}>
        <p className="text-indic text-center text-2xl font-semibold">{t.callEnded}</p>
        <FactsBar facts={state.facts} t={t} />
        <PrimaryButton onClick={() => navigate("/")}>
          <span className="text-indic">{t.newCall}</span>
        </PrimaryButton>
      </main>
    );
  }

  return (
    <main className="flex h-full flex-col" lang={lang}>
      <StatusBar state={state} t={t} partnerLang={join.partnerLang} />

      {state.connection === "mic_denied" && (
        <div className="px-4 pt-3">
          <Banner tone="error">{t.micDenied}</Banner>
        </div>
      )}
      {state.notice === "didnt_understand" && (
        <div className="px-4 pt-3">
          <Banner tone="warn">🔁 {t.askedRepeat}</Banner>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-3">
        {!state.partnerPresent && !state.messages.length ? (
          <ShareCard url={url} t={t} />
        ) : (
          <Transcript state={state} t={t} />
        )}
      </div>

      <FactsBar facts={state.facts} t={t} />
      <Controls
        state={state}
        t={t}
        volume={volume}
        onVolume={setVolume}
        onMute={toggleMute}
        onRepeat={() => send({ type: "repeat" })}
        onDidntUnderstand={() => send({ type: "didnt_understand" })}
        onLeave={leave}
      />
    </main>
  );
}

function StatusBar({
  state,
  t,
  partnerLang,
}: {
  state: CallState;
  t: Strings;
  partnerLang: Lang | null;
}) {
  let text = t.connecting;
  let tone = "bg-slate-400";
  if (state.connection === "connected" || state.connection === "mic_denied") {
    if (!state.partnerPresent) text = state.partnerLeft ? t.leftCall : t.waitingPartner;
    else if (state.agent === "offline") text = t.translatorOffline;
    else if (state.agent === "loading" || state.agent === "waiting") text = t.loadingTranslator;
    else if (state.agent === "unsupported") text = t.notSupported;
    else if (state.agent === "same_language") text = t.sameLanguage;
    else {
      text = t.ready;
      tone = "bg-emerald-500";
    }
    if (tone !== "bg-emerald-500") tone = "bg-amber-400";
  }
  return (
    <header className="flex items-center gap-3 border-b border-[var(--line)] bg-[var(--surface)] px-4 py-3">
      <span className={`size-3 shrink-0 rounded-full ${tone}`} aria-hidden />
      <p className="text-indic flex-1 text-base font-medium" aria-live="polite">
        {text}
      </p>
      {partnerLang && (
        <span className="text-indic rounded-full bg-[var(--bg)] px-3 py-1 text-sm">
          {t.them}: {LANGUAGES[partnerLang].native}
        </span>
      )}
    </header>
  );
}

function Transcript({ state, t }: { state: CallState; t: Strings }) {
  const end = useRef<HTMLDivElement>(null);
  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on every new line
  useEffect(
    () => end.current?.scrollIntoView({ behavior: "smooth", block: "end" }),
    [state.messages.length, state.partials.me, state.partials.them],
  );
  return (
    <ol className="flex flex-col gap-3" aria-live="polite">
      {state.messages.map((m) => (
        <Bubble key={m.key} m={m} t={t} />
      ))}
      {(state.speaking.them || state.partials.them) && (
        <li className="text-indic max-w-[85%] self-start rounded-2xl bg-[var(--theirs)] px-4 py-2 text-[var(--muted)] shadow-sm">
          <span className="speaking-ring mr-2 inline-block size-2 rounded-full bg-brand-500" />
          {state.partials.them || t.speaking}
        </li>
      )}
      {(state.speaking.me || state.partials.me) && (
        <li className="text-indic max-w-[85%] self-end rounded-2xl bg-[var(--mine)] px-4 py-2 opacity-70">
          {state.partials.me || t.speaking}
        </li>
      )}
      <div ref={end} />
    </ol>
  );
}

function Bubble({ m, t }: { m: Message; t: Strings }) {
  const flagged = m.flags.includes("number_missing") || m.flags.includes("unit_changed");
  if (m.failed) {
    return (
      <li
        className={`text-indic max-w-[85%] rounded-2xl px-4 py-2 text-sm text-[var(--muted)] italic ${m.mine ? "self-end" : "self-start"}`}
      >
        {t.notHeard}
      </li>
    );
  }
  if (m.mine) {
    // My words (as recognised), and what the other person heard.
    return (
      <li className="max-w-[85%] self-end rounded-2xl rounded-br-sm bg-[var(--mine)] px-4 py-2 shadow-sm">
        <p className="text-indic text-lg" lang={m.srcLang}>
          {m.srcText}
        </p>
        {m.tgtText && (
          <p
            className="text-indic mt-1 border-t border-black/10 pt-1 text-sm text-[var(--muted)]"
            lang={m.tgtLang}
          >
            {t.theyHeard}: {m.tgtText}
          </p>
        )}
      </li>
    );
  }
  // Their words, translated into my language (big), with the original (small).
  return (
    <li className="max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-[var(--theirs)] px-4 py-2 shadow-sm">
      <p className="text-indic text-xl font-medium" lang={m.tgtLang}>
        {m.tgtText}
      </p>
      {m.srcText && (
        <p className="text-indic mt-1 text-sm text-[var(--muted)]" lang={m.srcLang}>
          {t.original}: {m.srcText}
        </p>
      )}
      {flagged && (
        <p className="text-indic mt-1 text-sm font-semibold text-amber-600">⚠️ {t.checkNumber}</p>
      )}
    </li>
  );
}

function FactsBar({ facts, t }: { facts: CallState["facts"]; t: Strings }) {
  if (!facts.length) return null;
  return (
    <section
      aria-label={t.keyFacts}
      className="border-t border-[var(--line)] bg-[var(--surface)] px-4 py-2"
    >
      <h2 className="text-indic mb-1 text-xs font-semibold tracking-wide text-[var(--muted)] uppercase">
        {t.keyFacts}
      </h2>
      <ul className="flex flex-wrap gap-2">
        {facts.map((f) => (
          <li
            key={f.display}
            className="rounded-full bg-amber-100 px-3 py-1 font-mono text-base font-semibold text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
          >
            {f.kind === "phone" ? "📞 " : ""}
            {f.display}
          </li>
        ))}
      </ul>
    </section>
  );
}

type ControlsProps = {
  state: CallState;
  t: Strings;
  volume: number;
  onVolume: (v: number) => void;
  onMute: () => void;
  onRepeat: () => void;
  onDidntUnderstand: () => void;
  onLeave: () => void;
};

function Controls(p: ControlsProps) {
  const { state, t } = p;
  const btn =
    "text-indic flex flex-col items-center justify-center gap-1 rounded-2xl px-2 py-3 text-sm font-semibold transition active:scale-95";
  return (
    <footer className="flex flex-col gap-3 border-t border-[var(--line)] bg-[var(--surface)] px-4 pt-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <label className="text-indic flex items-center gap-3 text-sm text-[var(--muted)]">
        <span className="shrink-0">{t.originalVoice}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={p.volume}
          onChange={(e) => p.onVolume(Number(e.target.value))}
          className="flex-1 accent-brand-600"
        />
      </label>
      <div className="grid grid-cols-4 gap-2">
        <button
          type="button"
          onClick={p.onMute}
          aria-pressed={state.muted}
          className={`${btn} ${state.muted ? "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-100" : "bg-[var(--bg)]"} ${state.speaking.me && !state.muted ? "speaking-ring" : ""}`}
        >
          <span className="text-2xl" aria-hidden>
            {state.muted ? "🔇" : "🎙️"}
          </span>
          {state.muted ? t.unmute : t.mute}
        </button>
        <button type="button" onClick={p.onRepeat} className={`${btn} bg-[var(--bg)]`}>
          <span className="text-2xl" aria-hidden>
            🔁
          </span>
          {t.repeat}
        </button>
        <button type="button" onClick={p.onDidntUnderstand} className={`${btn} bg-[var(--bg)]`}>
          <span className="text-2xl" aria-hidden>
            ❓
          </span>
          {t.didntUnderstand}
        </button>
        <button type="button" onClick={p.onLeave} className={`${btn} bg-red-600 text-white`}>
          <span className="text-2xl" aria-hidden>
            📵
          </span>
          {t.endCall}
        </button>
      </div>
    </footer>
  );
}
