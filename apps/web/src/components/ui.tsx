import type { ButtonHTMLAttributes, ReactNode } from "react";

export function PrimaryButton({
  children,
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return (
    <button
      type="button"
      {...rest}
      className={`w-full rounded-2xl bg-brand-700 px-6 py-4 text-xl font-semibold text-white shadow-lg transition hover:bg-brand-800 active:scale-[0.99] disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  );
}

export function Spinner() {
  return (
    <span
      aria-hidden
      className="inline-block size-5 animate-spin rounded-full border-2 border-current border-t-transparent align-middle"
    />
  );
}

export function Banner({
  tone,
  children,
}: {
  tone: "info" | "warn" | "error";
  children: ReactNode;
}) {
  const tones = {
    info: "bg-brand-50 text-brand-800 dark:bg-brand-800/30 dark:text-brand-100",
    warn: "bg-amber-50 text-amber-900 dark:bg-amber-900/30 dark:text-amber-100",
    error: "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-100",
  };
  return (
    <div role="status" className={`text-indic rounded-xl px-4 py-3 text-base ${tones[tone]}`}>
      {children}
    </div>
  );
}
