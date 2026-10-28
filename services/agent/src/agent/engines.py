"""Model engines: speech recognition (ASR) and machine translation (MT).

Every engine is synchronous and thread-safe for inference; the agent calls
them from a thread pool so the event loop never blocks. Models load lazily
on first use (or at start-up with PRELOAD_MODELS=1) and are shared by all
rooms.
"""

from __future__ import annotations

import gc
import json
import logging
import threading
import time
from collections.abc import Callable, Iterable
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Protocol

import numpy as np

from .settings import PINNED_REVISIONS, ct2_path, int8_path, languages, routes, settings

log = logging.getLogger(__name__)


class ASR(Protocol):
    def transcribe(self, audio: np.ndarray, lang: str) -> str: ...


class MT(Protocol):
    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]: ...


def _snapshot(repo: str, allow: list[str] | None = None) -> str:
    from huggingface_hub import snapshot_download

    # Never download during a call; `translator-cli download` fetches everything up front.
    return snapshot_download(repo_id=repo, allow_patterns=allow, local_files_only=True,
                             revision=PINNED_REVISIONS.get(repo))


def _torch_threads() -> None:
    import torch

    torch.set_num_threads(settings().threads_per_model)


# --- Speech recognition ------------------------------------------------------


class ParakeetASR:
    """NVIDIA Parakeet-TDT-0.6B-v3 (CC-BY-4.0) via onnx-asr. English (and 24 EU languages)."""

    def __init__(self, repo: str, quantization: str | None) -> None:
        import onnx_asr
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = settings().threads_per_model
        # CPU provider on every machine so the Mac measures what the Contabo server will do.
        self.model = onnx_asr.load_model(
            "nemo-parakeet-tdt-0.6b-v3", _snapshot(repo), quantization=quantization,
            sess_options=opts, providers=["CPUExecutionProvider"],
        )

    def transcribe(self, audio: np.ndarray, lang: str) -> str:  # noqa: ARG002 - one ASR interface
        return str(self.model.recognize(audio.astype(np.float32), sample_rate=16000)).strip()


class WhisperASR:
    """Whisper via faster-whisper / CTranslate2 (MIT). Used for Mandarin."""

    # Nudges Whisper towards Simplified Chinese with punctuation. Keep it free of
    # full-width punctuation: an earlier prompt with "，" in it made Whisper turbo
    # write stray "Ｂ" and "４" where "？" and "，" belonged.
    _PROMPTS: ClassVar[dict[str, str]] = {"zh": "以下是普通话的句子。"}

    def __init__(self, repo: str, compute_type: str) -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            _snapshot(repo), device="cpu", compute_type=compute_type,
            cpu_threads=settings().threads_per_model,
        )

    def transcribe(self, audio: np.ndarray, lang: str) -> str:
        segments, _info = self.model.transcribe(
            audio.astype(np.float32), language=lang, beam_size=2,
            condition_on_previous_text=False, without_timestamps=True, vad_filter=False,
            initial_prompt=self._PROMPTS.get(lang),
        )
        return "".join(s.text for s in segments).strip()


class MLXWhisperASR:
    """Whisper on the Apple-silicon GPU via MLX (MIT). Mac development profile only."""

    def __init__(self, repo: str) -> None:
        import mlx_whisper

        self.mlx_whisper = mlx_whisper
        self.path = _snapshot(repo)
        self._lock = threading.Lock()  # one GPU stream; serialise calls

    def transcribe(self, audio: np.ndarray, lang: str) -> str:
        with self._lock:
            out = self.mlx_whisper.transcribe(
                audio.astype(np.float32), path_or_hf_repo=self.path, language=lang,
                condition_on_previous_text=False, initial_prompt=WhisperASR._PROMPTS.get(lang),
                verbose=None,
            )
        return str(out.get("text", "")).strip()

    def close(self) -> None:
        """mlx_whisper keeps the model in a module-level holder; drop it so memory is freed."""
        from mlx_whisper.transcribe import ModelHolder

        ModelHolder.model = ModelHolder.model_path = None


class IndicConformerASR:
    """AI4Bharat IndicConformer-600M multilingual (MIT). Telugu and Hindi.

    The repo ships a TorchScript preprocessor, an ONNX encoder and a CTC head
    shared by 22 languages, plus per-language vocabularies and logit masks.
    We load those files directly instead of the repo's ``trust_remote_code``
    wrapper: that wrapper only loads by repo id and opens the RNNT heads of
    all 22 languages. Greedy CTC decoding, as in the reference code.
    """

    def __init__(self, repo: str, decoding: str) -> None:
        import onnxruntime as ort
        import torch

        if decoding != "ctc":
            raise ValueError(f"IndicConformer: only ctc decoding is supported, got {decoding!r}")
        _torch_threads()
        self.torch = torch
        root = Path(_snapshot(repo))
        assets = root / "assets"
        self.blank = int(json.loads((root / "config.json").read_text())["BLANK_ID"])
        self.vocab: dict[str, list[str]] = json.loads((assets / "vocab.json").read_text())
        masks = json.loads((assets / "language_masks.json").read_text())
        self.masks = {lang: np.asarray(m, dtype=bool) for lang, m in masks.items()}
        self.preprocessor = torch.jit.load(str(assets / "preprocessor.ts"), map_location="cpu").eval()
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = settings().threads_per_model
        cpu = ["CPUExecutionProvider"]
        self.encoder = ort.InferenceSession(str(assets / "encoder.onnx"), opts, providers=cpu)
        self.ctc = ort.InferenceSession(str(assets / "ctc_decoder.onnx"), opts, providers=cpu)
        self._lock = threading.Lock()

    def transcribe(self, audio: np.ndarray, lang: str) -> str:
        wav = self.torch.from_numpy(audio.astype(np.float32)).unsqueeze(0)
        with self._lock, self.torch.inference_mode():
            feats, length = self.preprocessor(input_signal=wav, length=self.torch.tensor([wav.shape[-1]]))
            enc, _ = self.encoder.run(
                ["outputs", "encoded_lengths"],
                {"audio_signal": feats.numpy(), "length": length.numpy()},
            )
            logits = self.ctc.run(["logprobs"], {"encoder_output": enc})[0]
        # argmax over this language's sub-vocabulary; softmax doesn't change it
        ids = logits[0][:, self.masks[lang]].argmax(axis=-1)
        keep = np.r_[True, ids[1:] != ids[:-1]]  # collapse repeats
        vocab = self.vocab[lang]
        return "".join(vocab[i] for i in ids[keep] if i != self.blank).replace("▁", " ").strip()


class Punctuator:
    """Punctuation + sentence boundaries for ASR output that has none (IndicConformer).

    1-800-BAD-CODE/xlm-roberta_punctuation_fullstop_truecase (Apache-2.0, 47
    languages incl. te/hi). One ONNX graph predicts, per subword, punctuation
    after it and whether a sentence ends there. Without sentence ends, two
    spoken sentences reach MT as one run-on sentence.
    """

    def __init__(self, repo: str) -> None:
        import onnxruntime as ort
        import yaml
        from sentencepiece import SentencePieceProcessor

        root = Path(_snapshot(repo, ["model.onnx", "sp.model", "config.yaml"]))
        # int8 copy built by `translator-cli download`: same output, 2.4x faster, 0.8 GB less RAM.
        onnx_path = int8_path(repo)
        if not onnx_path.exists():
            log.warning("int8 punctuation model missing; using fp32 (run translator-cli download)")
            onnx_path = root / "model.onnx"
        cfg = yaml.safe_load((root / "config.yaml").read_text())
        self.post_labels: list[str] = cfg["post_labels"]
        self.max_len = int(cfg["max_length"])
        self.sp = SentencePieceProcessor(model_file=str(root / "sp.model"))
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = settings().threads_per_model
        cpu = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(str(onnx_path), opts, providers=cpu)

    def punctuate(self, text: str) -> str:
        """Return ``text`` with punctuation added. Existing words are never changed."""
        ids = self.sp.encode_as_ids(text)[: self.max_len - 2]
        if not ids:
            return text
        inp = np.array([[self.sp.bos_id(), *ids, self.sp.eos_id()]], dtype=np.int64)
        _pre, post, _cap, sbd = self.session.run(None, {"input_ids": inp})
        out: list[str] = []
        for k, tok_id in enumerate(ids, start=1):
            piece = self.sp.id_to_piece(tok_id)
            if piece.startswith("▁") and out:
                out.append(" ")
            out.append(piece.lstrip("▁"))
            label = self.post_labels[int(post[0][k])]
            if sbd[0][k] and label not in (".", "?", "।", "。", "？"):
                label = "."  # a sentence boundary needs a mark our splitter sees
            if label not in ("<NULL>", "<ACRONYM>"):
                out.append(label)
        return "".join(out).strip()


# --- Translation -------------------------------------------------------------


class IndicTrans2MT:
    """AI4Bharat IndicTrans2 distilled models (MIT)."""

    def __init__(self, repo: str) -> None:
        import torch
        from IndicTransToolkit.processor import IndicProcessor
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        _torch_threads()
        self.torch = torch
        path = _snapshot(repo)
        self.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(path, trust_remote_code=True).eval()
        # The repo's remote code reads and returns legacy tuple KV caches; transformers
        # >= 4.5x passes a Cache object instead (AttributeError). Declaring the model
        # legacy-only keeps the KV cache: 2.3x faster than use_cache=False, identical output.
        type(self.model)._supports_default_dynamic_cache = classmethod(lambda _cls: False)
        self.ip = IndicProcessor(inference=True)
        self._lock = threading.Lock()

    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]:
        codes = languages()["languages"]
        s, t = codes[src]["indictrans"], codes[tgt]["indictrans"]
        with self._lock:  # IndicProcessor keeps per-batch placeholder state
            batch = self.ip.preprocess_batch(texts, src_lang=s, tgt_lang=t)
            inputs = self.tokenizer(batch, truncation=True, padding="longest", return_tensors="pt",
                                    return_attention_mask=True)
            with self.torch.inference_mode():
                out = self.model.generate(**inputs, use_cache=True, min_length=0, max_length=256,
                                          num_beams=4, num_return_sequences=1)
            decoded = self.tokenizer.batch_decode(out, skip_special_tokens=True,
                                                  clean_up_tokenization_spaces=True)
            return self.ip.postprocess_batch(decoded, lang=t)


class OpusMT:
    """Helsinki-NLP Opus-MT Marian models (Apache-2.0 / CC-BY-4.0). One model per direction."""

    def __init__(self, repo: str) -> None:
        import torch
        from transformers import MarianMTModel, MarianTokenizer

        _torch_threads()
        self.torch = torch
        path = _snapshot(repo)
        self.tokenizer = MarianTokenizer.from_pretrained(path)
        self.model = MarianMTModel.from_pretrained(path).eval()

    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]:  # noqa: ARG002 - one MT interface
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        with self.torch.inference_mode():
            out = self.model.generate(**inputs, num_beams=4, max_new_tokens=256)
        return [t.strip() for t in self.tokenizer.batch_decode(out, skip_special_tokens=True)]


class M2M100MT:
    """Meta M2M100 (MIT), run by CTranslate2 from the float32 conversion that
    `translator-cli download` makes (the int8 conversion changed meanings).

    The routes use greedy decoding (beam=1): about half the time of beam=4
    per sentence on an M4, with output at least as good on the smoke set.
    """

    def __init__(self, repo: str, beam: int) -> None:
        import ctranslate2
        from transformers import M2M100Tokenizer

        self.beam = beam
        self.tokenizer = M2M100Tokenizer.from_pretrained(_snapshot(repo))
        self.translator = ctranslate2.Translator(
            str(ct2_path(repo)), device="cpu", compute_type="float32",
            intra_threads=settings().threads_per_model,
        )
        self._lock = threading.Lock()  # the tokenizer's src_lang is shared state

    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]:
        tok = self.tokenizer
        with self._lock:
            tok.src_lang = src
            pieces = [tok.convert_ids_to_tokens(tok.encode(t)) for t in texts]
        results = self.translator.translate_batch(
            pieces, target_prefix=[[tok.lang_code_to_token[tgt]]] * len(texts),
            beam_size=self.beam, max_decoding_length=256,
        )
        # hypotheses start with the target-language token
        return [tok.decode(tok.convert_tokens_to_ids(r.hypotheses[0][1:]), skip_special_tokens=True).strip()
                for r in results]


# --- Model registry ----------------------------------------------------------

_load_lock = threading.Lock()
_loaded: dict[str, Any] = {}


def _get[T](key: str, factory: Callable[[], T]) -> T:
    """Load a model once and share it between every room."""
    if key in _loaded:
        return _loaded[key]
    with _load_lock:
        if key not in _loaded:
            t0 = time.perf_counter()
            _loaded[key] = factory()
            log.info("loaded %s in %.1fs", key, time.perf_counter() - t0)
    return _loaded[key]


def loaded_models() -> list[str]:
    return sorted(_loaded)


def _asr_key(lang: str) -> str:
    spec = routes()["asr"][lang]
    return f"asr:{spec['engine']}:{spec['model']}"


def _mt_key(step: dict) -> str:
    return f"mt:{step['engine']}:{step['model']}"


def asr_for(lang: str) -> ASR:
    spec = routes()["asr"][lang]
    engine = spec["engine"]
    key = _asr_key(lang)
    if engine == "parakeet":
        return _get(key, lambda: ParakeetASR(spec["model"], spec.get("quantization")))
    if engine == "whisper":
        return _get(key, lambda: WhisperASR(spec["model"], spec.get("compute_type", "int8")))
    if engine == "mlx_whisper":
        return _get(key, lambda: MLXWhisperASR(spec["model"]))
    if engine == "indic_conformer":
        return _get(key, lambda: IndicConformerASR(spec["model"], spec.get("decoding", "ctc")))
    raise ValueError(f"unknown ASR engine {engine}")


def punctuator_for(lang: str) -> Punctuator | None:
    """Punctuation model for languages whose ASR outputs bare words, else None."""
    repo = routes()["asr"][lang].get("punctuation")
    return _get(f"punct:{repo}", lambda: Punctuator(repo)) if repo else None


def _mt_engine(step: dict) -> MT:
    key = _mt_key(step)
    engine = step["engine"]
    if engine == "indictrans2":
        return _get(key, lambda: IndicTrans2MT(step["model"]))
    if engine == "opus_mt":
        return _get(key, lambda: OpusMT(step["model"]))
    if engine == "m2m100":
        return _get(key, lambda: M2M100MT(step["model"], step.get("beam", 4)))
    raise ValueError(f"unknown MT engine {engine}")


@cache
def mt_route(src: str, tgt: str, fallback: bool = False) -> list[tuple[MT, str, str]]:
    """Steps to translate src→tgt as (engine, from_lang, to_lang); pivots have 2 steps.

    ``fallback=True`` returns the second-choice route, or [] if there is none.
    """
    steps = routes()["mt_fallback" if fallback else "mt"].get(f"{src}>{tgt}")
    if fallback and not steps:
        return []
    if not steps:
        raise ValueError(f"no translation route for {src}>{tgt}")
    chain = []
    cur = src
    for i, step in enumerate(steps):
        to = step.get("to", tgt) if i < len(steps) - 1 else tgt
        chain.append((_mt_engine(step), cur, to))
        cur = to
    return chain


_WARMUP_TEXT = {
    "te": "నమస్కారం, మీరు ఎలా ఉన్నారు?",
    "hi": "नमस्ते, आप कैसे हैं?",
    "en": "Hello, how are you?",
    "zh": "你好，你怎么样？",
}
_warmed: set[str] = set()


def _route_steps(langs: set[str]) -> Iterable[tuple[str, str, bool, list[dict]]]:
    """(src, tgt, fallback, steps) for every route between two of ``langs``."""
    r = routes()
    for fallback, section in ((False, "mt"), (True, "mt_fallback")):
        for key, steps in r[section].items():
            s, t = key.split(">")
            if s in langs and t in langs:
                yield s, t, fallback, steps


def needed_keys(langs: Iterable[str]) -> set[str]:
    """Registry keys of every model that calls between ``langs`` use."""
    langs = set(langs)
    keys = {_asr_key(lg) for lg in langs}
    keys |= {f"punct:{p}" for lg in langs if (p := routes()["asr"][lg].get("punctuation"))}
    keys |= {_mt_key(step) for *_, steps in _route_steps(langs) for step in steps}
    return keys


def release_unused(langs: Iterable[str]) -> None:
    """Unload models no active call needs (on a 16 GB Mac, holding every language's
    models made macOS swap and slowed calls 3x)."""
    keep = needed_keys(langs)
    with _load_lock:
        dropped = [k for k in _loaded if k not in keep]
        for k in dropped:
            if close := getattr(_loaded.pop(k), "close", None):
                close()
        _warmed.difference_update({w for w in _warmed if w.split("|")[0] in dropped})
    if dropped:
        mt_route.cache_clear()
        gc.collect()
        log.info("released %d model(s): %s", len(dropped), ", ".join(dropped))


def _warm(key: str, fn: Callable[[], object]) -> None:
    """Run a model twice, once per process. The first calls into PyTorch or ONNX
    Runtime are slow (allocator, kernel selection): a cold IndicTrans2 call took
    1.5-3 s, a warm one 0.2 s."""
    if key in _warmed:
        return
    for _ in range(2):
        fn()
    _warmed.add(key)


def preload(langs: list[str]) -> None:
    """Load and warm every model needed for the given languages, while the call shows 'loading'."""
    # Warm-up keys are "<registry key>|<detail>" so release_unused can forget them.
    for lang in langs:
        asr = asr_for(lang)
        silence = np.zeros(16000, np.float32)
        _warm(f"{_asr_key(lang)}|{lang}", lambda a=asr, lg=lang, x=silence: a.transcribe(x, lg))
        if (p := punctuator_for(lang)) is not None:
            repo = routes()["asr"][lang]["punctuation"]
            _warm(f"punct:{repo}|{lang}", lambda p=p, lg=lang: p.punctuate(_WARMUP_TEXT[lg]))
    for s, t, fallback, steps in _route_steps(set(langs)):
        for step, (engine, a, b) in zip(steps, mt_route(s, t, fallback=fallback), strict=True):
            text = _WARMUP_TEXT.get(a, _WARMUP_TEXT["en"])
            _warm(f"{_mt_key(step)}|{a}>{b}", lambda e=engine, x=text, a=a, b=b: e.translate([x], a, b))
