"""One utterance, end to end: audio → text → facts → translation → checks.

This module is free of LiveKit so it can be driven from WAV files (CLI,
tests, benchmarks) exactly as in a call.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field

import numpy as np

from pipeline_core.facts import KeyFact, facts_from
from pipeline_core.indic_text import clean_asr_text
from pipeline_core.numbers import itn
from pipeline_core.quality import check_translation
from pipeline_core.repair import repair_currency, repair_numbers
from pipeline_core.tts_text import normalize_for_tts, split_for_speech, split_sentences

from .engines import asr_for, mt_route, punctuator_for

log = logging.getLogger(__name__)


@dataclass
class Timings:
    asr_ms: float = 0.0
    mt_ms: float = 0.0


@dataclass
class UtteranceResult:
    src_lang: str
    tgt_lang: str
    src_text: str  # recognised text with numbers as digits (shown to the speaker)
    tgt_text: str  # translation (shown to the listener)
    facts: list[KeyFact]
    issues: list[str]  # quality-check and repair codes (metrics only; never contain text)
    tts_sentences: list[str] = field(default_factory=list)
    timings: Timings = field(default_factory=Timings)

    def caption_payload(self) -> dict:
        return {
            "srcLang": self.src_lang,
            "tgtLang": self.tgt_lang,
            "srcText": self.src_text,
            "tgtText": self.tgt_text,
            "facts": [asdict(f) for f in self.facts],
            "flags": self.issues,
        }


def recognise(audio: np.ndarray, lang: str) -> str:
    """Recognised words without added punctuation (fast; also used for live captions)."""
    return clean_asr_text(asr_for(lang).transcribe(audio, lang), lang)


def punctuate(text: str, lang: str) -> str:
    """Add sentence ends if the ASR engine gives none, so MT and TTS work per sentence."""
    p = punctuator_for(lang)
    return p.punctuate(text) if p and text else text


def _run_route(route: list, segments: list[str]) -> list[str]:
    for engine, a, b in route:
        segments = engine.translate(segments, a, b)
    return segments


def _acceptable(src: str, src_lang: str, out: str, tgt_lang: str) -> bool:
    """No critical issue: numbers and units intact, right script, no loop, not empty."""
    return check_translation(src, src_lang, out, tgt_lang).ok


def translate_text(text: str, src: str, tgt: str) -> str:
    # Sentence by sentence (as one batch): seq2seq models such as Marian often
    # drop everything after the first sentence of a multi-sentence input.
    sources = split_sentences(text, min_chars=4) or [text]
    outputs = _run_route(mt_route(src, tgt), sources)
    # Bounded fallback: a sentence with a critical issue (e.g. a lost number) gets
    # one retry by the second route, kept only if that retry has no critical issue.
    pairs = zip(sources, outputs, strict=True)
    bad = [i for i, (s, o) in enumerate(pairs) if not _acceptable(s, src, o, tgt)]
    fallback = mt_route(src, tgt, fallback=True)
    if bad and fallback:
        retried = _run_route(fallback, [sources[i] for i in bad])
        kept = 0
        for i, out in zip(bad, retried, strict=True):
            if _acceptable(sources[i], src, out, tgt):
                outputs[i] = out
                kept += 1
        log.info("mt fallback %s>%s: %d sentence(s) retried, %d fixed", src, tgt, len(bad), kept)
    outputs = [_keep_sentence_end(s, o.strip(), tgt) for s, o in zip(sources, outputs, strict=True)]
    return ("" if tgt == "zh" else " ").join(o for o in outputs if o)


_ENDS = ".!?।。！？"
_FULL_STOP = {"hi": "।", "zh": "。"}


def _keep_sentence_end(src: str, out: str, tgt: str) -> str:
    """MT sometimes drops the final full stop; without it captions run together
    ("50 యువాన్ నేను …") and TTS does not pause between sentences."""
    if out and src.rstrip()[-1:] in _ENDS and out[-1] not in _ENDS:
        return out + _FULL_STOP.get(tgt, ".")
    return out


def process_text(raw: str, src: str, tgt: str, timings: Timings | None = None) -> UtteranceResult | None:
    """Text-side pipeline (after ASR). Returns None for empty input."""
    timings = timings or Timings()
    raw = raw.strip()
    if not raw:
        return None
    norm = itn(raw, src)
    facts = facts_from(norm, src)

    t0 = time.perf_counter()
    tgt_text = translate_text(norm.text, src, tgt)
    timings.mt_ms = (time.perf_counter() - t0) * 1000

    report = check_translation(norm.text, src, tgt_text, tgt)
    repairs: list[str] = []
    if "number_missing" in report.codes:
        fixed = repair_numbers(norm.text, src, tgt_text, tgt)
        if fixed is not None:
            tgt_text = fixed
            repairs.append("number_repaired")
            report = check_translation(norm.text, src, tgt_text, tgt)
    fixed = repair_currency(facts, tgt_text, tgt)
    if fixed is not None:
        tgt_text = fixed
        repairs.append("currency_repaired")

    sentences = split_for_speech(normalize_for_tts(tgt_text, tgt)) if tgt_text.strip() else []
    return UtteranceResult(
        src_lang=src, tgt_lang=tgt, src_text=norm.text, tgt_text=tgt_text, facts=facts,
        issues=report.codes + repairs, tts_sentences=sentences, timings=timings,
    )


def process_audio(audio: np.ndarray, src: str, tgt: str) -> UtteranceResult | None:
    timings = Timings()
    t0 = time.perf_counter()
    raw = punctuate(recognise(audio, src), src)
    timings.asr_ms = (time.perf_counter() - t0) * 1000
    return process_text(raw, src, tgt, timings)
