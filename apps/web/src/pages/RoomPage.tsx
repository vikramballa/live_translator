import {
  type ApiErrorCode,
  type JoinResponse,
  LANGS,
  LANGUAGES,
  type Lang,
  partnersOf,
  type RoomInfo,
} from "@lt/contracts";
import { useCallback, useEffect, useState } from "react";
import { api, RequestError } from "../api.ts";
import { CallView } from "../components/CallView.tsx";
import { LanguageTiles } from "../components/LanguageTiles.tsx";
import { Banner, PrimaryButton, SecondaryButton, Spinner } from "../components/ui.tsx";
import { format, STRINGS } from "../i18n.ts";
import { navigate } from "../router.ts";
import { browserLang, storage } from "../storage.ts";

type Phase =
  | { kind: "loading" }
  | { kind: "error"; code: ApiErrorCode }
  | { kind: "choose"; info: RoomInfo }
  | { kind: "joining"; info: RoomInfo }
  | { kind: "call"; info: RoomInfo; join: JoinResponse };

export function RoomPage({ roomId }: { roomId: string }) {
  const [lang, setLang] = useState<Lang>(() => storage.lang() ?? browserLang());
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const t = STRINGS[lang];

  const load = useCallback(() => {
    setPhase({ kind: "loading" });
    api
      .room(roomId)
      .then((info) => setPhase({ kind: "choose", info }))
      .catch((e) =>
        setPhase({ kind: "error", code: e instanceof RequestError ? e.code : "internal" }),
      );
  }, [roomId]);

  useEffect(load, [load]);

  async function join(info: RoomInfo) {
    storage.setLang(lang);
    setPhase({ kind: "joining", info });
    try {
      const res = await api.join(roomId, { lang, seatKey: storage.seatKey(roomId) });
      storage.setSeatKey(roomId, res.seatKey);
      setPhase({ kind: "call", info, join: res });
    } catch (e) {
      setPhase({ kind: "error", code: e instanceof RequestError ? e.code : "internal" });
    }
  }

  if (phase.kind === "call") {
    const { info } = phase;
    // A new token remounts the call, so a rejoin starts from a clean state.
    return (
      <CallView
        key={phase.join.token}
        roomId={roomId}
        lang={lang}
        join={phase.join}
        t={t}
        onRejoin={() => join(info)}
      />
    );
  }

  if (phase.kind === "loading") {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-3" lang={lang}>
        <span className="text-brand-700 dark:text-brand-100">
          <Spinner />
        </span>
        <p className="text-indic text-[var(--muted)]" role="status">
          {t.connecting}
        </p>
      </main>
    );
  }

  if (phase.kind === "error") {
    const message =
      {
        not_found: t.roomNotFound,
        expired: t.roomExpired,
        full: t.roomFull,
        unsupported_pair: t.notSupported,
      }[phase.code as string] ?? t.errorGeneric;
    // Temporary problems can be retried; a dead link can only lead to a new call.
    const retryable = phase.code === "internal" || phase.code === "rate_limited";
    return (
      <main className="flex flex-1 flex-col justify-center gap-4 px-5" lang={lang}>
        <Banner tone="error">{message}</Banner>
        {retryable && (
          <PrimaryButton onClick={load}>
            <span className="text-indic">{t.tryAgain}</span>
          </PrimaryButton>
        )}
        {retryable ? (
          <SecondaryButton onClick={() => navigate("/")}>
            <span className="text-indic">{t.newCall}</span>
          </SecondaryButton>
        ) : (
          <PrimaryButton onClick={() => navigate("/")}>
            <span className="text-indic">{t.newCall}</span>
          </PrimaryButton>
        )}
      </main>
    );
  }

  const info = phase.info;
  // Someone is already here: only languages that can pair with theirs are offered.
  const partnerLang = info.langs[0] ?? null;
  const allowed = partnerLang ? [partnerLang, ...partnersOf(partnerLang)] : [...LANGS];
  const disabled = LANGS.filter((l) => !allowed.includes(l));
  const chosenOk = allowed.includes(lang);

  return (
    <main className="flex flex-1 flex-col gap-5 px-5 pt-8 pb-8" lang={lang}>
      <header className="text-center">
        <img src="/icon.svg" alt="" className="mx-auto mb-3 size-12 drop-shadow-md" />
        <h1 className="text-2xl font-bold">Live Translator</h1>
        {partnerLang && (
          <>
            <p className="text-indic mt-2 text-lg font-medium">{t.invited}</p>
            <p className="text-indic mt-2 inline-block rounded-full bg-brand-50 px-4 py-1 text-base text-brand-800 dark:bg-brand-800/30 dark:text-brand-100">
              {format(t.partnerSpeaks, { lang: LANGUAGES[partnerLang].native })}
            </p>
          </>
        )}
      </header>
      <h2 className="text-indic text-center text-xl font-semibold">{t.chooseLanguage}</h2>
      <LanguageTiles value={chosenOk ? lang : null} onChange={setLang} disabled={disabled} />
      {info.full && <Banner tone="warn">{t.roomFull}</Banner>}
      <p className="text-indic text-center text-sm text-[var(--muted)]">🎧 {t.headphonesTip}</p>
      <div className="mt-auto">
        <PrimaryButton
          onClick={() => join(info)}
          disabled={!chosenOk || info.full || phase.kind === "joining"}
          aria-busy={phase.kind === "joining"}
        >
          {phase.kind === "joining" ? (
            <Spinner />
          ) : (
            <span className="text-indic">🎙️ {t.joinCall}</span>
          )}
        </PrimaryButton>
      </div>
    </main>
  );
}
