"""Command-line tools for the translator (run from services/agent).

    uv run translator-cli download [--only-open]
    uv run translator-cli translate --src te --tgt en --text "ఐదు వందల రూపాయలు"
    uv run translator-cli translate --src en --tgt te --wav sample.wav [--say out.wav]
    uv run translator-cli bench --src en --tgt zh --wav a.wav --wav b.wav --runs 5
    uv run translator-cli e2e --src en --tgt te --text "The price is 500 rupees."
    uv run translator-cli eval --set ../../eval/sets/smoke-v0.json [--offline]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
import wave
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .settings import languages


def _load_wav(path: str) -> np.ndarray:
    from .audio import int16_to_float, resample

    with wave.open(path) as w:
        if w.getsampwidth() != 2:
            raise SystemExit(f"{path}: only 16-bit PCM WAV is supported")
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() > 1:
            pcm = pcm.reshape(-1, w.getnchannels()).mean(axis=1).astype(np.int16)
        return resample(int16_to_float(pcm), w.getframerate(), 16_000)


def _write_wav(path: str, pcm: np.ndarray, sr: int) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.astype("<i2").tobytes())


def cmd_translate(args: argparse.Namespace) -> None:
    from . import translator

    if args.wav:
        result = translator.process_audio(_load_wav(args.wav), args.src, args.tgt)
    else:
        result = translator.process_text(args.text, args.src, args.tgt)
    if result is None:
        print("(nothing recognised)")
        return
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    if args.say:
        asyncio.run(_say(result.tts_sentences, args.tgt, args.say))


async def _say(sentences: list[str], lang: str, path: str) -> None:
    from .tts_client import TTSClient

    tts = TTSClient()
    await tts.start()
    parts, sr = [], 24000
    for s in sentences:
        pcm, sr = await tts.synth(s, lang)
        parts.append(pcm)
    await tts.close()
    _write_wav(path, np.concatenate(parts) if parts else np.zeros(0, np.int16), sr)
    print(f"wrote {path}", file=sys.stderr)


def cmd_bench(args: argparse.Namespace) -> None:
    from . import translator

    audios = [_load_wav(p) for p in args.wav]
    translator.process_audio(audios[0], args.src, args.tgt)  # warm-up (model load)
    asr, mt, total = [], [], []
    for _ in range(args.runs):
        for a in audios:
            t0 = time.perf_counter()
            r = translator.process_audio(a, args.src, args.tgt)
            total.append((time.perf_counter() - t0) * 1000)
            if r:
                asr.append(r.timings.asr_ms)
                mt.append(r.timings.mt_ms)

    def pct(xs: list[float], q: float) -> float:
        return float(np.percentile(xs, q)) if xs else float("nan")

    for name, xs in (("asr", asr), ("mt", mt), ("asr+mt", total)):
        print(f"{name:7s} p50={pct(xs, 50):7.0f}ms  p95={pct(xs, 95):7.0f}ms  "
              f"mean={statistics.fmean(xs) if xs else float('nan'):7.0f}ms  n={len(xs)}")


def main() -> None:
    langs = list(languages()["languages"])
    p = argparse.ArgumentParser(prog="translator-cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="download all models into models/")
    d.add_argument("--only-open", action="store_true", help="skip gated ai4bharat models")

    t = sub.add_parser("translate", help="translate one sentence (text or WAV)")
    t.add_argument("--src", required=True, choices=langs)
    t.add_argument("--tgt", required=True, choices=langs)
    g = t.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--wav")
    t.add_argument("--say", metavar="OUT.wav", help="also synthesise the translation")

    b = sub.add_parser("bench", help="latency of ASR+MT over WAV files")
    b.add_argument("--src", required=True, choices=langs)
    b.add_argument("--tgt", required=True, choices=langs)
    b.add_argument("--wav", required=True, action="append")
    b.add_argument("--runs", type=int, default=3)

    e = sub.add_parser("e2e", help="headless two-bot call through LiveKit and the agent")
    e.add_argument("--src", required=True, choices=langs)
    e.add_argument("--tgt", required=True, choices=langs)
    e.add_argument("--text", required=True, help="sentence the speaker bot says (synthesised)")

    v = sub.add_parser("eval", help="run an eval set through real calls and score it")
    v.add_argument("--set", required=True, help="eval set JSON, e.g. eval/sets/smoke-v0.json")
    v.add_argument("--only", help="one direction, e.g. te-en")
    v.add_argument("--offline", action="store_true", help="no LiveKit: audio straight into the pipeline")

    args = p.parse_args()
    if args.cmd == "download":
        from .download import download

        download(include_gated=not args.only_open)
    elif args.cmd == "translate":
        cmd_translate(args)
    elif args.cmd == "bench":
        cmd_bench(args)
    elif args.cmd == "e2e":
        from .e2e import run

        print(json.dumps(asyncio.run(run(args.src, args.tgt, args.text)), ensure_ascii=False, indent=2))
    elif args.cmd == "eval":
        from .evaluate import run_set

        asyncio.run(run_set(Path(args.set).resolve(), args.only, args.offline))


if __name__ == "__main__":
    main()

