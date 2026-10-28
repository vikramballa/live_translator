"""Download every model the routes need into ``models/``.

Usage: ``uv run translator-cli download [--only-open]``

``--only-open`` skips the AI4Bharat repositories, which are MIT-licensed but
"gated" on Hugging Face (free login + one click to accept the terms).
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from .settings import MODELS_DIR, PINNED_REVISIONS, PROFILE, ct2_path, int8_path, routes

GATED_PREFIX = "ai4bharat/"

SILERO = ("onnx-community/silero-vad", ["onnx/model.onnx", "LICENSE"])
KOKORO_RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
KOKORO_FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
# The app runs the int8 punctuation model and the CTranslate2 copy of M2M100.
# Their full-size originals (1 GB and 1.8 GB) are fetched only to build those
# copies, so a machine that already has them never downloads the originals again.
PUNCT_FILES = ["sp.model", "config.yaml", "README.md"]
M2M100_TOKENIZER_FILES = [
    "config.json", "generation_config.json", "sentencepiece.bpe.model",
    "special_tokens_map.json", "tokenizer_config.json", "vocab.json",
]
# Files fetched by plain URL (not pinned by a Hugging Face commit) are checked
# against the copies that were reviewed and benchmarked.
FILE_SHA256 = {
    "kokoro-v1.0.onnx": "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
    "te_IN-padmavathi-medium.onnx": "414aa5960d91ceb6e45bbdf8c27fdc71af09f205130d7be4e99470f3c2cfa57d",
    "te_IN-padmavathi-medium.onnx.json": "6c86e4ee99d379815f78a75f23cdad62ccf50370062dd915c233d6e22de7109f",
}


# Only the PyTorch/ONNX/CT2 weights are used; skip TensorFlow, Flax and Rust copies.
IGNORE = ["*.h5", "*.msgpack", "*.ot", "*.tflite", "flax_model*", "tf_model*"]


def _hf_snapshot(repo: str, allow: list[str] | None = None) -> Path:
    from huggingface_hub import list_repo_files, snapshot_download

    print(f"  · {repo}", flush=True)
    ignore = list(IGNORE)
    # Some repos ship the same weights twice; transformers prefers safetensors.
    revision = PINNED_REVISIONS.get(repo)
    if allow is None and "model.safetensors" in list_repo_files(repo, revision=revision):
        ignore.append("pytorch_model.bin")
    return Path(snapshot_download(repo_id=repo, allow_patterns=allow, ignore_patterns=ignore,
                                  revision=revision))


def _fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  · {dest.name} (cached)", flush=True)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"  · {dest.name} ← {url}", flush=True)
    urllib.request.urlretrieve(url, tmp)
    expected = FILE_SHA256.get(dest.name)
    if expected:
        digest = hashlib.sha256()
        with tmp.open("rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            tmp.unlink()
            raise RuntimeError(f"{dest.name}: SHA-256 mismatch (the file changed upstream)")
    tmp.rename(dest)


def _quantize_int8(repo: str) -> None:
    """Dynamic int8 copy (MatMul + embedding Gather). For the punctuation model
    this gave identical output on the smoke set, 2.4x faster, 1.1 GB down to 0.28 GB."""
    from onnxruntime.quantization import QuantType, quantize_dynamic

    dst = int8_path(repo)
    if dst.exists():
        print(f"  · {dst.name} (cached)", flush=True)
        return
    src = _hf_snapshot(repo, [*PUNCT_FILES, "model.onnx"]) / "model.onnx"
    dst.parent.mkdir(parents=True, exist_ok=True)
    print(f"  · {dst.name} ← int8 of {repo}", flush=True)
    tmp = dst.with_suffix(".part.onnx")
    quantize_dynamic(str(src), str(tmp), weight_type=QuantType.QInt8,
                     op_types_to_quantize=["MatMul", "Gather"], extra_options={"MatMulConstBOnly": True})
    tmp.rename(dst)


def _convert_ct2(repo: str) -> None:
    """float32 CTranslate2 conversion of a Hugging Face seq2seq model (int8 changed meanings)."""
    import ctranslate2

    dst = ct2_path(repo)
    if (dst / "model.bin").exists():
        print(f"  · {dst.name} (cached)", flush=True)
        return
    print(f"  · {dst.name} ← CTranslate2 conversion of {repo}", flush=True)
    ctranslate2.converters.TransformersConverter(str(_hf_snapshot(repo))).convert(str(dst), force=True)


def model_repos(include_gated: bool) -> list[tuple[str, list[str] | None]]:
    r = routes()
    repos: dict[str, list[str] | None] = {SILERO[0]: SILERO[1]}
    for spec in r["asr"].values():
        if spec["engine"] == "parakeet":
            q = spec.get("quantization")
            pats = ["config.json", "vocab.txt", "nemo128.onnx"]
            pats += [f"*.{q}.onnx"] if q else ["encoder-model.onnx*", "decoder_joint-model.onnx"]
            repos[spec["model"]] = pats
        else:
            repos[spec["model"]] = None
        if spec.get("punctuation"):  # ONNX graph only; skip the 1.1 GB .nemo copy
            repos[spec["punctuation"]] = PUNCT_FILES
    for steps in [*r["mt"].values(), *r["mt_fallback"].values()]:
        for step in steps:
            repos[step["model"]] = M2M100_TOKENIZER_FILES if step["engine"] == "m2m100" else None
    return [(k, v) for k, v in repos.items() if include_gated or not k.startswith(GATED_PREFIX)]


def download(include_gated: bool = True) -> None:
    print(f"Models directory: {MODELS_DIR}  (profile: {PROFILE})")
    print("Hugging Face models:")
    failed: list[str] = []
    for repo, allow in model_repos(include_gated):
        try:
            _hf_snapshot(repo, allow)
        except Exception as e:
            failed.append(repo)
            print(f"    ! failed: {type(e).__name__}: {str(e).splitlines()[0][:160]}")

    print("Optimised copies:")
    for repo in sorted({s["punctuation"] for s in routes()["asr"].values() if s.get("punctuation")}):
        if repo not in failed:
            _quantize_int8(repo)
    steps = [s for route in [*routes()["mt"].values(), *routes()["mt_fallback"].values()] for s in route]
    for repo in sorted({s["model"] for s in steps if s["engine"] == "m2m100"} - set(failed)):
        _convert_ct2(repo)

    print("Piper voices (Telugu):")
    for spec in routes()["tts"].values():
        if spec["engine"] != "piper":
            continue
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{spec['hf_path']}"
        for suffix in (".onnx", ".onnx.json"):
            _fetch(f"{base}/{spec['voice']}{suffix}", MODELS_DIR / "piper" / f"{spec['voice']}{suffix}")
        _fetch(f"{base}/MODEL_CARD", MODELS_DIR / "piper" / f"{spec['voice']}.MODEL_CARD")

    print("Kokoro (English, Hindi, Mandarin):")
    for name in KOKORO_FILES:
        _fetch(f"{KOKORO_RELEASE}/{name}", MODELS_DIR / "kokoro" / name)

    if failed:
        print("\nSome downloads failed:")
        for repo in failed:
            print(f"  - {repo}")
        if any(r.startswith(GATED_PREFIX) for r in failed):
            print(
                "\nThe ai4bharat models are free (MIT) but gated. To unlock them:\n"
                "  1. Run: uv run hf auth login   (paste a 'read' token from https://huggingface.co/settings/tokens)\n"
                "  2. Open each page below and click 'Agree and access repository':\n"
                + "".join(f"     https://huggingface.co/{r}\n" for r in failed if r.startswith(GATED_PREFIX))
                + "  3. Run this download again."
            )
        raise SystemExit(1)
    print("\nAll models downloaded.")
