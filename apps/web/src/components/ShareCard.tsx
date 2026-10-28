import QRCode from "qrcode";
import { useEffect, useState } from "react";
import type { Strings } from "../i18n.ts";

/** Shown while waiting for the other person: link, WhatsApp, copy, QR code. */
export function ShareCard({ url, t }: { url: string; t: Strings }) {
  const [qr, setQr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    QRCode.toDataURL(url, { margin: 1, width: 220, errorCorrectionLevel: "M" })
      .then(setQr)
      .catch(() => setQr(null));
  }, [url]);

  const message = `${t.inviteText} ${url}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard blocked: the link is visible to copy by hand */
    }
  }

  async function share() {
    if (navigator.share) {
      try {
        await navigator.share({ text: message, url });
        return;
      } catch {
        /* cancelled */
      }
    }
    open(`https://wa.me/?text=${encodeURIComponent(message)}`, "_blank", "noopener");
  }

  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4">
      <h2 className="text-indic text-lg font-semibold">{t.shareTitle}</h2>
      <p className="break-all rounded-lg bg-[var(--bg)] px-3 py-2 font-mono text-sm select-all">
        {url}
      </p>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={share}
          className="rounded-xl bg-[#25D366] px-4 py-3 text-lg font-semibold text-white"
        >
          WhatsApp
        </button>
        <button
          type="button"
          onClick={copy}
          className="text-indic rounded-xl border-2 border-brand-600 px-4 py-3 text-lg font-semibold text-brand-700 dark:text-brand-100"
        >
          {copied ? t.copied : t.copy}
        </button>
      </div>
      {qr && (
        <figure className="flex flex-col items-center gap-1">
          <img src={qr} alt="" className="size-44 rounded-lg bg-white p-1" />
          <figcaption className="text-indic text-sm text-[var(--muted)]">{t.scanQr}</figcaption>
        </figure>
      )}
    </section>
  );
}
