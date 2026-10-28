"""Text-to-speech worker: a separate program, driven over stdin/stdout.

Protocol (one request at a time):

    stdin : one JSON line  {"id": "...", "lang": "te", "text": "...", "speed": 1.0}
    stdout: one JSON line  {"id": "...", "sample_rate": 22050, "bytes": N, "error": null}
            followed by exactly N bytes of 16-bit little-endian mono PCM.

On start-up it prints {"ready": true, "langs": [...]}. Logs go to stderr only,
because stdout carries audio.

Engines (all open weights, see docs/licences/REGISTER.md):
  * Piper (Telugu voices trained on IndicVoices-R, CC-BY-4.0)
  * Kokoro-82M (Apache-2.0) for English, Hindi and Mandarin
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Protocol

import numpy as np

log = logging.getLogger("tts-worker")


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "config" / "languages.json").exists():
            return parent
    raise RuntimeError("repo root not found")


ROOT = _repo_root()
MODELS = Path(os.environ.get("MODELS_DIR", ROOT / "models"))
WARMUP_TEXT = {"te": "నమస్తే", "hi": "नमस्ते", "en": "Hello.", "zh": "你好。"}


class Engine(Protocol):
    sample_rate: int

    def synth(self, text: str, speed: float) -> np.ndarray: ...  # int16 mono


class PiperEngine:
    def __init__(self, voice: str) -> None:
        from piper import PiperVoice

        path = MODELS / "piper" / f"{voice}.onnx"
        self.voice = PiperVoice.load(path)
        self.sample_rate = self.voice.config.sample_rate

    def synth(self, text: str, speed: float) -> np.ndarray:
        from piper import SynthesisConfig

        cfg = SynthesisConfig(length_scale=1.0 / max(0.5, min(speed, 2.0)))
        chunks = [c.audio_int16_array for c in self.voice.synthesize(text, syn_config=cfg)]
        return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int16)


_KOKORO = None


def _kokoro():
    global _KOKORO
    if _KOKORO is None:
        from kokoro_onnx import Kokoro

        _KOKORO = Kokoro(
            str(MODELS / "kokoro" / "kokoro-v1.0.onnx"), str(MODELS / "kokoro" / "voices-v1.0.bin")
        )
    return _KOKORO


class KokoroEngine:
    sample_rate = 24000

    def __init__(self, voice: str, lang: str) -> None:
        self.voice = voice
        self.lang = lang
        self.k = _kokoro()
        self.g2p = None
        if lang == "zh":
            from misaki import zh

            self.g2p = zh.ZHG2P()

    def synth(self, text: str, speed: float) -> np.ndarray:
        if self.g2p is not None:
            phonemes, _ = self.g2p(text)
            samples, _sr = self.k.create(phonemes, voice=self.voice, speed=speed, is_phonemes=True)
        else:
            samples, _sr = self.k.create(text, voice=self.voice, speed=speed, lang=self.lang)
        return (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)


def build_engine(spec: dict) -> Engine:
    if spec["engine"] == "piper":
        return PiperEngine(spec["voice"])
    if spec["engine"] == "kokoro":
        return KokoroEngine(spec["voice"], spec["lang"])
    raise ValueError(f"unknown TTS engine {spec['engine']}")


def load_routes() -> dict:
    generated = ROOT / "config" / "routes.generated.json"
    path = generated if generated.exists() else ROOT / "config" / "routes.bootstrap.json"
    return json.loads(path.read_text())["tts"]


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[tts] %(message)s")
    specs = load_routes()
    engines: dict[str, Engine] = {}
    out = sys.stdout.buffer

    def write_header(obj: dict) -> None:
        out.write((json.dumps(obj) + "\n").encode())

    # Warm up the requested voices so the first real sentence is fast.
    for lang in filter(None, os.environ.get("TTS_PRELOAD", "").split(",")):
        if lang in specs:
            engines[lang] = build_engine(specs[lang])
            engines[lang].synth(WARMUP_TEXT.get(lang, "ok"), 1.0)
    write_header({"ready": True, "langs": sorted(specs)})
    out.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            lang = req["lang"]
            if lang not in engines:
                t0 = time.perf_counter()
                engines[lang] = build_engine(specs[lang])
                log.info("loaded %s voice in %.1fs", lang, time.perf_counter() - t0)
            eng = engines[lang]
            pcm = eng.synth(req["text"], float(req.get("speed", 1.0)))
            data = pcm.astype("<i2").tobytes()
            write_header({"id": req_id, "sample_rate": eng.sample_rate, "bytes": len(data),
                          "error": None})
            out.write(data)
        except Exception as e:
            log.exception("synthesis failed")
            write_header({"id": req_id, "sample_rate": 0, "bytes": 0, "error": f"{type(e).__name__}: {e}"})
        out.flush()


if __name__ == "__main__":
    main()
