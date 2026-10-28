"""Async client for the separate TTS worker process (services/tts-worker).

The worker is a different program with its own virtualenv (it uses GPL
espeak-ng via Piper/Kokoro phonemisers). We talk to it over a pipe with a
tiny line-delimited protocol, see tts_worker/main.py.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import os
import sys

import numpy as np

from .settings import REPO_ROOT

log = logging.getLogger(__name__)

WORKER_DIR = REPO_ROOT / "services" / "tts-worker"
# A sentence takes well under a second; this only catches a hung worker.
REQUEST_TIMEOUT_S = 30.0


class TTSError(RuntimeError):
    pass


class TTSClient:
    def __init__(self, preload: list[str] | None = None) -> None:
        self._proc: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()
        self._ids = itertools.count()
        self._preload = preload or []

    async def start(self) -> None:
        async with self._lock:
            await self._spawn()

    async def _spawn(self) -> None:
        """Start (or restart) the worker. Call with the lock held."""
        self._kill()
        python = WORKER_DIR / ".venv" / "bin" / "python"
        if not python.exists():
            raise TTSError(f"TTS worker venv missing; run `uv sync` in {WORKER_DIR}")
        env = {**os.environ, "TTS_PRELOAD": ",".join(self._preload)}
        # Run the script by path in isolated mode (-I): no reliance on .pth files,
        # and nothing from the current directory can shadow an import.
        self._proc = await asyncio.create_subprocess_exec(
            str(python), "-I", str(WORKER_DIR / "src" / "tts_worker" / "main.py"),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=sys.stderr,
            env=env, cwd=str(WORKER_DIR), limit=2**20,
        )
        assert self._proc.stdout
        ready = json.loads(await asyncio.wait_for(self._proc.stdout.readline(), timeout=180))
        if not ready.get("ready"):
            raise TTSError(f"TTS worker failed to start: {ready}")
        log.info("TTS worker ready (%s)", ",".join(ready.get("langs", [])))

    def _kill(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.kill()
        self._proc = None

    async def synth(self, text: str, lang: str, speed: float = 1.0) -> tuple[np.ndarray, int]:
        """Return (int16 mono PCM, sample_rate). Requests are serialised.

        The exchange is shielded: when a caller is cancelled mid-request (its
        room closed), the reply is still read off the pipe, so it can never be
        handed to the next caller, possibly in another room.
        """
        task = asyncio.ensure_future(self._request(text, lang, speed))
        task.add_done_callback(lambda t: t.cancelled() or t.exception())  # no "never retrieved"
        return await asyncio.shield(task)

    async def _request(self, text: str, lang: str, speed: float) -> tuple[np.ndarray, int]:
        async with self._lock:
            if self._proc is None or self._proc.returncode is not None:
                log.warning("TTS worker not running; restarting")
                await self._spawn()
            assert self._proc and self._proc.stdin and self._proc.stdout
            req_id = str(next(self._ids))
            line = json.dumps({"id": req_id, "lang": lang, "text": text, "speed": speed}) + "\n"
            try:
                async with asyncio.timeout(REQUEST_TIMEOUT_S):
                    self._proc.stdin.write(line.encode())
                    await self._proc.stdin.drain()
                    header = json.loads(await self._proc.stdout.readline())
                    if header.get("id") != req_id:
                        raise ValueError(f"reply for request {header.get('id')!r}, expected {req_id!r}")
                    size = int(header["bytes"])
                    data = await self._proc.stdout.readexactly(size) if size else b""
            except (OSError, ValueError, KeyError, TypeError, asyncio.IncompleteReadError,
                    TimeoutError) as e:
                # Out of step or hung: restart rather than risk mixing up replies.
                self._kill()
                raise TTSError(f"TTS worker failed: {type(e).__name__}") from e
        if header.get("error"):
            raise TTSError(header["error"])
        return np.frombuffer(data, dtype="<i2"), int(header["sample_rate"])

    async def close(self) -> None:
        if self._proc and self._proc.returncode is None:
            assert self._proc.stdin
            self._proc.stdin.close()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except TimeoutError:
                self._proc.kill()
