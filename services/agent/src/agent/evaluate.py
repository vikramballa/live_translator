"""Run an eval set and score it.

Two modes:

* call (default): every sentence is spoken (synthesised) into a LiveKit room
  by a bot, the agent translates it as in a real call, and a second bot
  records the caption and the time to first translated audio (SE2FA).
  Needs `bun run dev`.
* ``--offline``: the same audio goes straight through ``translator.process_audio``
  (no LiveKit, no codec), for fast A/B tests of models. Reports ASR+MT time
  instead of SE2FA.

Scores per direction:

* ASR error: word error rate (te/hi/en) or character error rate (zh) of what
  the agent heard vs. what was said, after numbers are normalised to digits;
* numbers kept: every expected number appears in the translation;
* negation kept: a "not" in the source is still a "not" in the translation;
* flagged: captions the agent itself marked "check this".

Meaning is not scored automatically; a person reviews the saved outputs.

    uv run translator-cli eval --set ../../eval/sets/smoke-v0.json [--offline] [--only te-en]
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
import unicodedata
from collections.abc import Awaitable, Callable
from pathlib import Path

import numpy as np

from pipeline_core.numbers import itn
from pipeline_core.quality import has_negation

from .settings import REPO_ROOT

# (src, tgt, text) → {"caption": dict | None, "latency_ms": float | None}
Runner = Callable[[str, str, str], Awaitable[dict]]


def _strip_punct(text: str) -> str:
    # Not a regex like [^\w\s]: \w excludes Indic vowel signs (category M).
    return "".join(" " if unicodedata.category(c)[0] in "PS" else c for c in text)


def _norm_tokens(text: str, lang: str) -> list[str]:
    text = _strip_punct(itn(text, lang).text.lower())
    if lang == "zh":
        return [c for c in text if not c.isspace()]
    return text.split()


def _edit_distance(a: list[str], b: list[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def error_rate(ref: str, hyp: str, lang: str) -> tuple[int, int]:
    """(edits, reference length): WER for te/hi/en, CER for zh."""
    r, h = _norm_tokens(ref, lang), _norm_tokens(hyp, lang)
    return _edit_distance(r, h), len(r)


def numbers_in(text: str, lang: str) -> set[str]:
    return {n.value for n in itn(text, lang).numbers}


async def _call_runner() -> tuple[Runner, Callable[[], Awaitable[None]]]:
    from . import e2e

    async def run(src: str, tgt: str, text: str) -> dict:
        r = await e2e.run(src, tgt, text)
        return {"caption": r.get("caption"), "latency_ms": r.get("se2fa_ms")}

    async def close() -> None:
        return None

    return run, close


async def _offline_runner() -> tuple[Runner, Callable[[], Awaitable[None]]]:
    from . import translator
    from .audio import int16_to_float, resample
    from .tts_client import TTSClient

    tts = TTSClient()
    await tts.start()
    loop = asyncio.get_running_loop()

    async def run(src: str, tgt: str, text: str) -> dict:
        pcm, sr = await tts.synth(text, src)
        audio = resample(int16_to_float(pcm), sr, 16_000)
        t0 = time.perf_counter()
        r = await loop.run_in_executor(None, translator.process_audio, audio, src, tgt)
        ms = (time.perf_counter() - t0) * 1000
        return {"caption": r.caption_payload() if r else None, "latency_ms": ms}

    return run, tts.close


async def run_set(set_path: Path, only: str | None = None, offline: bool = False) -> Path:
    data = json.loads(set_path.read_text())
    run, close = await (_offline_runner() if offline else _call_runner())
    rows = []
    try:
        for src, tgt in data["directions"]:
            if only and f"{src}-{tgt}" != only:
                continue
            # One unscored run first: model loading must not count as latency.
            await run(src, tgt, data["sentences"][src][0]["text"])
            for item in data["sentences"][src]:
                try:
                    r = await run(src, tgt, item["text"])
                except Exception as e:  # record and keep going
                    r = {"caption": None, "latency_ms": None, "error": f"{type(e).__name__}: {e}"}
                rows.append(_score(item, src, tgt, r))
                print(f"{item['id']} {src}>{tgt}  {rows[-1]['latency_ms'] or 0:5.0f} ms  "
                      f"heard: {rows[-1]['heard']}\n      → {rows[-1]['translation']}", flush=True)
    finally:
        await close()
    out_dir = REPO_ROOT / "eval" / "results" / time.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = ("-offline" if offline else "") + (f"-{only}" if only else "")
    out_path = out_dir / f"{set_path.stem}{suffix}.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print_summary(rows, "ASR+MT" if offline else "SE2FA")
    print(f"\nsaved {out_path}")
    return out_path


def _score(item: dict, src: str, tgt: str, r: dict) -> dict:
    cap = r.get("caption") or {}
    heard, out = cap.get("srcText", ""), cap.get("tgtText", "")
    edits, n = error_rate(item["text"], heard, src)
    expected = item.get("numbers", [])
    negation = bool(item.get("negation"))
    return {
        "id": item["id"], "src": src, "tgt": tgt, "said": item["text"], "gloss": item["gloss"],
        "heard": heard, "translation": out, "flags": cap.get("flags", []),
        "facts": [f["display"] for f in cap.get("facts", [])],
        "asr_edits": edits, "asr_ref_len": n,
        "numbers_expected": expected,
        "numbers_heard": sorted(set(expected) & numbers_in(heard, src)),
        "numbers_kept": sorted(set(expected) & numbers_in(out, tgt)),
        "negation": negation,
        "negation_kept": negation and has_negation(out, tgt),
        "latency_ms": r.get("latency_ms"), "error": r.get("error"),
    }


def _pct(a: int, b: int) -> str:
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "-"


def print_summary(rows: list[dict], latency_name: str) -> None:
    print(f"\n{'direction':10} {'ASR error':>10} {'numbers kept':>14} {'negation kept':>14} "
          f"{'flagged':>8} {latency_name + ' p50':>11} {'p95':>7}")
    for d in dict.fromkeys((r["src"], r["tgt"]) for r in rows):
        rs = [r for r in rows if (r["src"], r["tgt"]) == d]
        edits, ref = sum(r["asr_edits"] for r in rs), sum(r["asr_ref_len"] for r in rs)
        n_exp = sum(len(r["numbers_expected"]) for r in rs)
        n_kept = sum(len(r["numbers_kept"]) for r in rs)
        neg = [r for r in rs if r["negation"]]
        lat = [r["latency_ms"] for r in rs if r["latency_ms"] is not None]
        p50 = f"{statistics.median(lat) / 1000:.2f}s" if lat else "-"
        p95 = f"{float(np.percentile(lat, 95)) / 1000:.2f}s" if lat else "-"
        flagged = sum(1 for r in rs if set(r["flags"]) & {"number_missing", "unit_changed"})
        print(f"{d[0] + '→' + d[1]:10} {100 * edits / max(ref, 1):9.1f}% {_pct(n_kept, n_exp):>14} "
              f"{_pct(sum(r['negation_kept'] for r in neg), len(neg)):>14} {flagged:>8} {p50:>11} {p95:>7}")
