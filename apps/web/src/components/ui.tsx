import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode };

const buttonBase =
  "flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl px-6 py-4 text-xl font-semibold transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-brand-500";

export function PrimaryButton({ children, className = "", ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      {...rest}
      className={`${buttonBase} bg-brand-700 text-white shadow-lg shadow-brand-700/20 hover:bg-brand-800 ${className}`}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      {...rest}
      className={`${buttonBase} border-2 border-brand-600 bg-[var(--surface)] text-brand-700 hover:bg-brand-50 dark:text-brand-100 dark:hover:bg-brand-800/30 ${className}`}
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
  action,
}: {
  tone: "info" | "warn" | "error";
  children: ReactNode;
  /** Optional button shown under the message (e.g. "Try again"). */
  action?: { label: string; onClick: () => void };
}) {
  const tones = {
    info: "bg-brand-50 text-brand-800 ring-brand-100 dark:bg-brand-800/30 dark:text-brand-100 dark:ring-brand-800",
    warn: "bg-amber-50 text-amber-900 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-100 dark:ring-amber-900",
    error:
      "bg-red-50 text-red-800 ring-red-200 dark:bg-red-900/30 dark:text-red-100 dark:ring-red-900",
  };
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`text-indic flex flex-col gap-2 rounded-xl px-4 py-3 text-base ring-1 ${tones[tone]}`}
    >
      <div>{children}</div>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="self-start rounded-lg bg-current/10 px-3 py-1.5 text-sm font-semibold underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-current"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
