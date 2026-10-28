import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";
import type { Strings } from "../i18n.ts";

/** Shown while waiting for the other person: link, WhatsApp, copy, QR code. */
export function ShareCard({ url, t }: { url: string; t: Strings }) {
  const [qr, setQr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const link = useRef<HTMLParagraphElement>(null);
  const canShare = typeof navigator.share === "function";

  useEffect(() => {
    QRCode.toDataURL(url, { margin: 1, width: 220, errorCorrectionLevel: "M" })
      .then(setQr)
      .catch(() => setQr(null));
  }, [url]);

  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(id);
  }, [copied]);

  const message = `${t.inviteText} ${url}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      // Clipboard blocked: select the link so it can be copied by hand.
      const el = link.current;
      if (el) getSelection()?.selectAllChildren(el);
    }
  }

  async function share() {
    try {
      await navigator.share({ text: message, url });
    } catch {
      /* cancelled */
    }
  }

  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 shadow-sm">
      <h2 className="text-indic text-lg font-semibold">📨 {t.shareTitle}</h2>
      <p
        ref={link}
        className="rounded-lg bg-[var(--bg)] px-3 py-2 font-mono text-sm break-all select-all"
      >
        {url}
      </p>
      <div className="grid grid-cols-2 gap-2">
        <a
          href={`https://wa.me/?text=${encodeURIComponent(message)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center rounded-xl bg-[#25D366] px-4 py-3 text-lg font-semibold text-white transition hover:brightness-95 focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-[#25D366] active:scale-[0.98]"
        >
          WhatsApp
        </a>
        <button
          type="button"
          onClick={copy}
          aria-live="polite"
          className={`text-indic rounded-xl border-2 px-4 py-3 text-lg font-semibold transition focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-brand-500 active:scale-[0.98] ${copied ? "border-emerald-600 bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-100" : "border-brand-600 text-brand-700 dark:text-brand-100"}`}
        >
          {copied ? `✓ ${t.copied}` : t.copy}
        </button>
      </div>
      {canShare && (
        <button
          type="button"
          onClick={share}
          className="text-indic rounded-xl bg-[var(--bg)] px-4 py-2 text-base font-semibold transition focus-visible:outline-4 focus-visible:outline-brand-500 active:scale-[0.98]"
        >
          ↗ {t.shareTitle}
        </button>
      )}
      {qr && (
        <figure className="flex flex-col items-center gap-1 pt-1">
          <img
            src={qr}
            alt=""
            className="size-44 rounded-lg bg-white p-1 ring-1 ring-[var(--line)]"
          />
          <figcaption className="text-indic text-sm text-[var(--muted)]">{t.scanQr}</figcaption>
        </figure>
      )}
    </section>
  );
}
