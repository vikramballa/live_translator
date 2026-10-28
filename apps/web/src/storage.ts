/** Small, failure-tolerant wrappers: storage may be blocked (private mode). */
import { Lang, SeatKey } from "@lt/contracts";

function get(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function set(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

export const storage = {
  lang(): Lang | null {
    const v = Lang.safeParse(get("lt.lang"));
    return v.success ? v.data : null;
  },
  setLang(l: Lang) {
    set("lt.lang", l);
  },
  /** Secret that lets this browser take back its seat after a reload. */
  seatKey(roomId: string): string | undefined {
    const v = SeatKey.safeParse(get(`lt.seat.${roomId}`));
    return v.success ? v.data : undefined;
  },
  setSeatKey(roomId: string, key: string) {
    set(`lt.seat.${roomId}`, key);
  },
  originalVolume(): number {
    const v = Number(get("lt.origVol"));
    return Number.isFinite(v) && get("lt.origVol") !== null ? Math.min(1, Math.max(0, v)) : 0.15;
  },
  setOriginalVolume(v: number) {
    set("lt.origVol", String(v));
  },
};

/** Best guess of the person's language from the browser, before they choose. */
export function browserLang(): Lang {
  for (const tag of navigator.languages ?? [navigator.language]) {
    const base = tag.toLowerCase().split("-")[0];
    const parsed = Lang.safeParse(base);
    if (parsed.success) return parsed.data;
  }
  return "en";
}
