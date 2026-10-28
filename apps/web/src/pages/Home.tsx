import { LANGS, LANGUAGES, type Lang } from "@lt/contracts";
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
        <img src="/icon.svg" alt="" className="mx-auto mb-4 size-16" />
        <h1 className="text-3xl font-bold tracking-tight">Live Translator</h1>
        <p className="text-indic mt-2 text-lg text-[var(--muted)]">{t.tagline}</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {LANGS.map((l) => LANGUAGES[l].native).join(" · ")}
        </p>
      </header>

      <section aria-labelledby="choose" className="flex flex-col gap-3">
        <h2 id="choose" className="text-indic text-center text-xl font-semibold">
          {t.chooseLanguage}
        </h2>
        <LanguageTiles value={lang} onChange={setLang} />
      </section>

      {error && <Banner tone="error">{error}</Banner>}

      <div className="mt-auto flex flex-col gap-3">
        <PrimaryButton onClick={start} disabled={busy}>
          {busy ? <Spinner /> : <span className="text-indic">📞 {t.startCall}</span>}
        </PrimaryButton>
        <p className="text-indic text-center text-sm text-[var(--muted)]">🔒 {t.privacy}</p>
      </div>
    </main>
  );
}
