import type { Lang } from "@lt/contracts";
import { useState } from "react";
import { api } from "../api.ts";
import { LanguageTiles } from "../components/LanguageTiles.tsx";
import { Banner, PrimaryButton, Spinner } from "../components/ui.tsx";
import { STRINGS } from "../i18n.ts";
import { navigate } from "../router.ts";
import { browserLang, storage } from "../storage.ts";

export function Home() {
  const [lang, setLang] = useState<Lang>(() => storage.lang() ?? browserLang());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = STRINGS[lang];

  function choose(l: Lang) {
    setLang(l);
    setError(null);
  }

  async function start() {
    setBusy(true);
    setError(null);
    storage.setLang(lang);
    try {
      const room = await api.createRoom();
      navigate(`/r/${room.roomId}`);
    } catch {
      setError(t.errorGeneric);
      setBusy(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col gap-6 px-5 pt-10 pb-8" lang={lang}>
      <header className="text-center">
        <img src="/icon.svg" alt="" className="mx-auto mb-4 size-16 drop-shadow-md" />
        <h1 className="text-3xl font-bold tracking-tight">Live Translator</h1>
        <p className="text-indic mt-2 text-lg text-[var(--muted)]">{t.tagline}</p>
      </header>

      <section aria-labelledby="choose" className="flex flex-col gap-3">
        <h2 id="choose" className="text-indic text-center text-xl font-semibold">
          {t.chooseLanguage}
        </h2>
        <LanguageTiles value={lang} onChange={choose} />
      </section>

      <section
        aria-labelledby="how"
        className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3"
      >
        <h2
          id="how"
          className="text-indic mb-2 text-sm font-semibold tracking-wide text-[var(--muted)] uppercase"
        >
          {t.howTitle}
        </h2>
        <ol className="flex flex-col gap-2">
          {[t.step1, t.step2, t.step3].map((step, i) => (
            <li key={step} className="text-indic flex items-start gap-3 text-base">
              <span
                aria-hidden
                className="grid size-7 shrink-0 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-800 dark:bg-brand-800/50 dark:text-brand-100"
              >
                {i + 1}
              </span>
              <span className="pt-0.5">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      {error && (
        <Banner tone="error" action={{ label: t.tryAgain, onClick: start }}>
          {error}
        </Banner>
      )}

      <div className="mt-auto flex flex-col gap-3">
        <PrimaryButton onClick={start} disabled={busy} aria-busy={busy}>
          {busy ? <Spinner /> : <span className="text-indic">📞 {t.startCall}</span>}
        </PrimaryButton>
        <p className="text-indic text-center text-sm text-[var(--muted)]">🔒 {t.privacy}</p>
      </div>
    </main>
  );
}
