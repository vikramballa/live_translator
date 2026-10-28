import { type JoinResponse, LANGUAGES, type Lang } from "@lt/contracts";
import { useEffect, useRef, useState } from "react";
import type { Strings } from "../i18n.ts";
import { navigate } from "../router.ts";
import { storage } from "../storage.ts";
import { type CallState, type Message, useCall } from "../useCall.ts";
import { ShareCard } from "./ShareCard.tsx";
import { Banner, PrimaryButton, SecondaryButton } from "./ui.tsx";

type Props = {
  roomId: string;
  lang: Lang;
  join: JoinResponse;
  t: Strings;
  /** Join the same room again (after leaving or a failed connection). */
  onRejoin: () => void;
};

export function CallView({ roomId, lang, join, t, onRejoin }: Props) {
  const [volume, setVolume] = useState(storage.originalVolume);
  const { state, send, toggleMute, retryMic, leave, dismissNotice } = useCall(join, volume);
  const [askSent, setAskSent] = useState(false);
  const url = `${location.origin}/r/${roomId}`;
  const inCall = state.connection !== "ended" && state.connection !== "error";

  useEffect(() => {
    storage.setOriginalVolume(volume);
  }, [volume]);
  useEffect(() => {
    if (!state.notice) return;
    const id = setTimeout(dismissNotice, 8000);
    return () => clearTimeout(id);
  }, [state.notice, dismissNotice]);
  useEffect(() => {
    if (!askSent) return;
    const id = setTimeout(() => setAskSent(false), 3000);
    return () => clearTimeout(id);
  }, [askSent]);

  // Closing the tab mid-conversation by accident drops the call: ask first.
  const talking = inCall && state.partnerPresent;
  useEffect(() => {
    if (!talking) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    addEventListener("beforeunload", warn);
    return () => removeEventListener("beforeunload", warn);
  }, [talking]);

  if (state.connection === "ended") {
    return (
      <main className="flex flex-1 flex-col justify-center gap-4 px-5" lang={lang}>
        <div className="mb-2 text-center">
          <span className="text-5xl" aria-hidden>
            👋
          </span>
          <h1 className="text-indic mt-3 text-2xl font-semibold">{t.callEnded}</h1>
        </div>
        <FactsBar facts={state.facts} t={t} framed />
        <PrimaryButton onClick={onRejoin}>
          <span className="text-indic">🔄 {t.rejoin}</span>
        </PrimaryButton>
        <SecondaryButton onClick={() => navigate("/")}>
          <span className="text-indic">{t.newCall}</span>
        </SecondaryButton>
      </main>
    );
  }

  const ready = state.partnerPresent && state.agent === "ready";
  const showShare = !state.partnerPresent && !state.messages.length;

  return (
    <main className="flex h-full flex-col" lang={lang}>
      <StatusBar state={state} t={t} myLang={lang} partnerLang={join.partnerLang} />

      {(state.connection === "error" ||
        state.connection === "mic_denied" ||
        state.notice === "didnt_understand" ||
        askSent) && (
        <div className="flex flex-col gap-2 px-4 pt-3">
          {state.connection === "error" && (
            <Banner tone="error" action={{ label: t.tryAgain, onClick: onRejoin }}>
              {t.connectFailed}
            </Banner>
          )}
          {state.connection === "mic_denied" && (
            <Banner tone="error" action={{ label: t.tryAgain, onClick: retryMic }}>
              🎙️ {t.micDenied}
            </Banner>
          )}
          {state.notice === "didnt_understand" && <Banner tone="warn">🔁 {t.askedRepeat}</Banner>}
          {askSent && <Banner tone="info">✓ {t.askSent}</Banner>}
        </div>
      )}

      {showShare ? (
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <ShareCard url={url} t={t} />
        </div>
      ) : (
        <Transcript state={state} t={t} ready={ready} />
      )}

      <FactsBar facts={state.facts} t={t} />
      <Controls
        state={state}
        t={t}
        ready={ready}
        volume={volume}
        onVolume={setVolume}
        onMute={toggleMute}
        onRepeat={() => send({ type: "repeat" })}
        onDidntUnderstand={() => {
          send({ type: "didnt_understand" });
          setAskSent(true);
        }}
        onLeave={leave}
      />
    </main>
  );
}

function StatusBar({
  state,
  t,
  myLang,
  partnerLang,
}: {
  state: CallState;
  t: Strings;
  myLang: Lang;
  partnerLang: Lang | null;
}) {
  let text = t.connecting;
  let tone = "bg-slate-400";
  if (state.connection === "reconnecting") {
    text = t.reconnecting;
    tone = "bg-amber-400 animate-pulse";
  } else if (state.connection === "error") {
    text = t.errorGeneric;
    tone = "bg-red-500";
  } else if (state.connection === "connected" || state.connection === "mic_denied") {
    tone = "bg-amber-400";
    if (!state.partnerPresent) text = state.partnerLeft ? t.leftCall : t.waitingPartner;
    else if (state.agent === "offline") text = t.translatorOffline;
    else if (state.agent === "loading" || state.agent === "waiting") text = t.loadingTranslator;
    else if (state.agent === "unsupported") text = t.notSupported;
    else if (state.agent === "same_language") text = t.sameLanguage;
    else {
      text = t.ready;
      tone = "bg-emerald-500";
    }
  }
  return (
    <header className="flex items-center gap-3 border-b border-[var(--line)] bg-[var(--surface)] px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
      <span className={`size-3 shrink-0 rounded-full ${tone}`} aria-hidden />
      <p
        className="text-indic min-w-0 flex-1 text-base leading-snug font-medium"
        aria-live="polite"
      >
        {text}
      </p>
      {partnerLang && (
        <span
          className="text-indic shrink-0 rounded-full bg-[var(--bg)] px-3 py-1 text-sm whitespace-nowrap ring-1 ring-[var(--line)]"
          title={`${t.you}: ${LANGUAGES[myLang].native} · ${t.them}: ${LANGUAGES[partnerLang].native}`}
        >
          {LANGUAGES[myLang].native} ⇄ {LANGUAGES[partnerLang].native}
        </span>
      )}
    </header>
  );
}

function Transcript({ state, t, ready }: { state: CallState; t: Strings; ready: boolean }) {
  const scroller = useRef<HTMLDivElement>(null);
  // Follow new lines only while the person is at the bottom; if they scrolled
  // up to re-read something, leave them there.
  const stuck = useRef(true);
  const onScroll = () => {
    const el = scroller.current;
    if (el) stuck.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };
  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on every new line
  useEffect(() => {
    const el = scroller.current;
    if (el && stuck.current) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [state.messages.length, state.partials.me, state.partials.them]);

  const themLive = state.speaking.them || !!state.partials.them;
  const meLive = state.speaking.me || !!state.partials.me;
  const empty = !state.messages.length && !themLive && !meLive;

  return (
    <div ref={scroller} onScroll={onScroll} className="flex-1 overflow-y-auto px-4 py-3">
      {empty ? (
        <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
          <span
            aria-hidden
            className={`grid size-20 place-items-center rounded-full bg-brand-100 text-4xl dark:bg-brand-800/40 ${ready ? "speaking-ring" : ""}`}
          >
            🎙️
          </span>
          <p className="text-indic text-lg text-[var(--muted)]">
            {ready ? t.readyHint : t.loadingTranslator}
          </p>
          <p className="text-indic text-sm text-[var(--muted)]">🎧 {t.headphonesTip}</p>
        </div>
      ) : (
        <ol className="flex flex-col gap-3" aria-live="polite">
          {state.messages.map((m) => (
            <Bubble key={m.key} m={m} t={t} />
          ))}
          {themLive && (
            <li
              aria-hidden
              className="text-indic max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-[var(--theirs)] px-4 py-2 text-[var(--muted)] shadow-sm ring-1 ring-[var(--line)]"
            >
              <span className="speaking-ring mr-2 inline-block size-2 rounded-full bg-brand-500" />
              {state.partials.them || t.speaking}
            </li>
          )}
          {meLive && (
            <li
              aria-hidden
              className="text-indic max-w-[85%] self-end rounded-2xl rounded-br-sm bg-[var(--mine)] px-4 py-2 opacity-70"
            >
              {state.partials.me || t.speaking}
            </li>
          )}
        </ol>
      )}
    </div>
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
        <span className="sr-only">{t.you}: </span>
        <p className="text-indic text-lg" lang={m.srcLang}>
          {m.srcText}
        </p>
        {m.tgtText && (
          <p
            className="text-indic mt-1 border-t border-current/10 pt-1 text-sm text-[var(--muted)]"
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
    <li
      className={`max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-[var(--theirs)] px-4 py-2 shadow-sm ring-1 ${flagged ? "ring-amber-400" : "ring-[var(--line)]"}`}
    >
      <span className="sr-only">{t.them}: </span>
      <p className="text-indic text-xl font-medium" lang={m.tgtLang}>
        {m.tgtText}
      </p>
      {m.srcText && (
        <p className="text-indic mt-1 text-sm text-[var(--muted)]" lang={m.srcLang}>
          {t.original}: {m.srcText}
        </p>
      )}
      {flagged && (
        <p className="text-indic mt-1 text-sm font-semibold text-amber-700 dark:text-amber-300">
          ⚠️ {t.checkNumber}
        </p>
      )}
    </li>
  );
}

function FactsBar({
  facts,
  t,
  framed = false,
}: {
  facts: CallState["facts"];
  t: Strings;
  /** A standalone card (call-ended screen) instead of a strip above the controls. */
  framed?: boolean;
}) {
  const [copied, setCopied] = useState<string | null>(null);
  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(null), 1500);
    return () => clearTimeout(id);
  }, [copied]);

  if (!facts.length) return null;

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(text);
    } catch {
      /* clipboard blocked: the value is on screen to copy by hand */
    }
  }

  return (
    <section
      aria-label={t.keyFacts}
      className={`border-[var(--line)] bg-[var(--surface)] px-4 py-2 ${framed ? "rounded-2xl border py-3" : "border-t"}`}
    >
      <h2 className="text-indic mb-1 text-xs font-semibold tracking-wide text-[var(--muted)] uppercase">
        {t.keyFacts}
      </h2>
      <ul className="flex flex-wrap gap-2">
        {facts.map((f) => (
          <li key={f.display}>
            <button
              type="button"
              onClick={() => copy(f.display)}
              title={t.copy}
              className="rounded-full bg-amber-100 px-3 py-1 font-mono text-base font-semibold text-amber-900 transition hover:bg-amber-200 focus-visible:outline-2 focus-visible:outline-amber-500 active:scale-95 dark:bg-amber-900/40 dark:text-amber-100"
            >
              {copied === f.display ? (
                <span className="text-indic font-sans">✓ {t.copied}</span>
              ) : (
                <>
                  {f.kind === "phone" ? "📞 " : ""}
                  {f.display}
                </>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

type ControlsProps = {
  state: CallState;
  t: Strings;
  /** Partner here and translator ready: Repeat / Didn't understand do something. */
  ready: boolean;
  volume: number;
  onVolume: (v: number) => void;
  onMute: () => void;
  onRepeat: () => void;
  onDidntUnderstand: () => void;
  onLeave: () => void;
};

function Controls(p: ControlsProps) {
  const { state, t } = p;
  // Ending is final for this call, so a stray tap only arms the button.
  const [confirmEnd, setConfirmEnd] = useState(false);
  useEffect(() => {
    if (!confirmEnd) return;
    const id = setTimeout(() => setConfirmEnd(false), 3000);
    return () => clearTimeout(id);
  }, [confirmEnd]);

  const btn =
    "text-indic flex min-h-20 flex-col items-center justify-center gap-1 rounded-2xl px-2 py-3 text-sm leading-tight font-semibold transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100 focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-brand-500";
  return (
    <footer className="flex flex-col gap-3 border-t border-[var(--line)] bg-[var(--surface)] px-4 pt-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <label className="text-indic flex items-center gap-3 text-sm text-[var(--muted)]">
        <span className="shrink-0">🔉 {t.originalVoice}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={p.volume}
          onChange={(e) => p.onVolume(Number(e.target.value))}
          aria-valuetext={`${Math.round(p.volume * 100)}%`}
          className="flex-1 accent-brand-600"
        />
        <span className="w-10 shrink-0 text-right tabular-nums" aria-hidden>
          {Math.round(p.volume * 100)}%
        </span>
      </label>
      <div className="grid grid-cols-4 gap-2">
        <button
          type="button"
          onClick={p.onMute}
          aria-pressed={state.muted}
          disabled={state.connection === "mic_denied"}
          className={`${btn} ${state.muted ? "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-100" : "bg-[var(--bg)]"} ${state.speaking.me && !state.muted ? "speaking-ring" : ""}`}
        >
          <span className="text-2xl" aria-hidden>
            {state.muted ? "🔇" : "🎙️"}
          </span>
          {state.muted ? t.unmute : t.mute}
        </button>
        <button
          type="button"
          onClick={p.onRepeat}
          disabled={!p.ready}
          className={`${btn} bg-[var(--bg)]`}
        >
          <span className="text-2xl" aria-hidden>
            🔁
          </span>
          {t.repeat}
        </button>
        <button
          type="button"
          onClick={p.onDidntUnderstand}
          disabled={!p.ready}
          className={`${btn} bg-[var(--bg)]`}
        >
          <span className="text-2xl" aria-hidden>
            ❓
          </span>
          {t.didntUnderstand}
        </button>
        <button
          type="button"
          onClick={() => (confirmEnd ? p.onLeave() : setConfirmEnd(true))}
          className={`${btn} text-white ${confirmEnd ? "bg-red-800 ring-4 ring-red-300 dark:ring-red-900" : "bg-red-600 hover:bg-red-700"}`}
        >
          <span className="text-2xl" aria-hidden>
            📵
          </span>
          {confirmEnd ? t.confirmEnd : t.endCall}
        </button>
      </div>
    </footer>
  );
}
