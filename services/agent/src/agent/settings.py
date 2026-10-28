"""Runtime settings, read once from environment variables.

Model files live inside the repo (``models/``) so the whole system can be
moved to the Contabo server with one directory copy, and nothing is written
to the user's global caches.
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "config" / "languages.json").exists():
            return parent
    raise RuntimeError("Could not find repo root (config/languages.json)")


REPO_ROOT = _find_repo_root()
MODELS_DIR = Path(os.environ.get("MODELS_DIR", REPO_ROOT / "models"))

# Must be set before huggingface_hub / transformers are imported anywhere.
os.environ.setdefault("HF_HOME", str(MODELS_DIR / "hf"))
# Use the token from a normal `hf auth login` (stored in the user's home), so the
# gated AI4Bharat models download into models/ without a second login.
os.environ.setdefault("HF_TOKEN_PATH", str(Path.home() / ".cache" / "huggingface" / "token"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


# Repos whose files run as code when loaded (IndicTrans2's trust_remote_code
# modelling files, IndicConformer's TorchScript preprocessor) are pinned to the
# commit that was reviewed: an upstream change is never downloaded or loaded
# until someone updates the hash here.
PINNED_REVISIONS = {
    "ai4bharat/indic-conformer-600m-multilingual": "2a77d305038dfc502fd9464e7d028b90381976cb",
    "ai4bharat/indictrans2-en-indic-dist-200M": "2cfd0a20057756d756bf3e53528f492afc52f91a",
    "ai4bharat/indictrans2-indic-en-dist-200M": "d66a2122ad6d28184f3dc3797b652bd80ae3f65f",
    "ai4bharat/indictrans2-indic-indic-dist-320M": "ffb7582b6d43791f1fb26b2153fc065f2e9ea575",
}


def int8_path(repo: str) -> Path:
    """Where `translator-cli download` puts the int8 copy of an ONNX model repo."""
    return MODELS_DIR / "int8" / f"{repo.replace('/', '--')}.onnx"


def ct2_path(repo: str) -> Path:
    """Where `translator-cli download` puts the CTranslate2 conversion of a seq2seq repo."""
    return MODELS_DIR / "ct2" / repo.replace("/", "--")


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    livekit_url: str = field(default_factory=lambda: os.environ.get("LIVEKIT_URL", "ws://127.0.0.1:7880"))
    livekit_api_key: str = field(default_factory=lambda: os.environ.get("LIVEKIT_API_KEY", "devkey"))
    livekit_api_secret: str = field(default_factory=lambda: os.environ.get("LIVEKIT_API_SECRET", "secret"))
    # The control endpoint the Bun API calls to ask the agent to join a room.
    control_host: str = field(default_factory=lambda: os.environ.get("AGENT_HOST", "127.0.0.1"))
    control_port: int = field(default_factory=lambda: _int("AGENT_PORT", 8765))
    control_secret: str = field(default_factory=lambda: os.environ.get("AGENT_SHARED_SECRET", ""))
    # CPU budget. On the 12-core Contabo VDS L: 5 threads per direction.
    threads_per_model: int = field(default_factory=lambda: _int("MODEL_THREADS", 4))
    inference_workers: int = field(default_factory=lambda: _int("INFERENCE_WORKERS", 2))
    # Load every model at start-up instead of on first use.
    preload: bool = field(default_factory=lambda: os.environ.get("PRELOAD_MODELS", "0") == "1")
    agent_identity: str = "translator"


@cache
def settings() -> Settings:
    return Settings()


@cache
def languages() -> dict:
    return json.loads((REPO_ROOT / "config" / "languages.json").read_text())


def default_profile() -> str:
    return "m4-local" if platform.system() == "Darwin" and platform.machine() == "arm64" else "contabo-cpu"


PROFILE = os.environ.get("PROFILE") or default_profile()


@cache
def routes() -> dict:
    """Route registry with the active profile's overrides applied."""
    generated = REPO_ROOT / "config" / "routes.generated.json"
    path = generated if generated.exists() else REPO_ROOT / "config" / "routes.bootstrap.json"
    data = json.loads(path.read_text())
    overrides = data.get("profiles", {}).get(PROFILE)
    if overrides is None:
        raise RuntimeError(f"unknown PROFILE {PROFILE!r}")
    for section, entries in overrides.items():
        data[section] = {**data[section], **entries}
    # Drop "$comment" keys so callers can iterate sections safely.
    data.setdefault("mt_fallback", {})
    for section in ("asr", "mt", "mt_fallback", "tts"):
        data[section] = {k: v for k, v in data[section].items() if not k.startswith("$")}
    return data


def enabled_pairs() -> set[frozenset[str]]:
    pairs = {frozenset(p) for p in languages()["pairs"]}
    # Testing only: e.g. EXTRA_PAIRS=en-zh lets the e2e harness use routes that
    # are not v1 call pairs. The API and web app never offer these.
    for item in filter(None, os.environ.get("EXTRA_PAIRS", "").split(",")):
        a, _, b = item.strip().partition("-")
        pairs.add(frozenset((a, b)))
    return pairs
