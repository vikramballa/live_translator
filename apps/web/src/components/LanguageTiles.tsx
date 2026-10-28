import { LANGS, LANGUAGES, type Lang } from "@lt/contracts";

type Props = {
  value: Lang | null;
  onChange: (lang: Lang) => void;
  /** Languages that cannot be chosen (e.g. no route to the partner's language). */
  disabled?: Lang[];
};

/** Four big tiles, each written in its own script, so anyone can find theirs. */
export function LanguageTiles({ value, onChange, disabled = [] }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {LANGS.map((lang) => {
        const info = LANGUAGES[lang];
        const selected = value === lang;
        const off = disabled.includes(lang);
        return (
          <button
            key={lang}
            type="button"
            aria-pressed={selected}
            disabled={off}
            lang={lang}
            onClick={() => onChange(lang)}
            className={[
              "flex min-h-24 flex-col items-center justify-center rounded-2xl border-2 px-3 py-4 transition",
              "focus-visible:outline-4 focus-visible:outline-brand-500",
              selected
                ? "border-brand-600 bg-brand-50 text-brand-800 shadow-md dark:bg-brand-800/30 dark:text-brand-100"
                : "border-[var(--line)] bg-[var(--surface)] hover:border-brand-500",
              off ? "cursor-not-allowed opacity-35" : "",
            ].join(" ")}
          >
            <span className="text-indic text-3xl font-semibold">{info.native}</span>
            {info.native !== info.name && (
              <span className="mt-1 text-sm text-[var(--muted)]">{info.name}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
