"""Audio helpers: streaming Silero VAD and resampling."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import soxr

SAMPLE_RATE = 16_000
VAD_FRAME = 512  # samples per VAD frame at 16 kHz = 32 ms
_VAD_CONTEXT = 64  # Silero v5+/v6 expects the previous 64 samples prepended


def resample(audio: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out or audio.size == 0:
        return audio
    return soxr.resample(audio, sr_in, sr_out, quality="HQ").astype(audio.dtype, copy=False)


def int16_to_float(pcm: np.ndarray) -> np.ndarray:
    return (pcm.astype(np.float32) / 32768.0).clip(-1.0, 1.0)


def float_to_int16(audio: np.ndarray) -> np.ndarray:
    return (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)


class SileroVAD:
    """Streaming Silero VAD (MIT). One instance per audio stream (it is stateful).

    The ONNX session is shared between instances; only the recurrent state and
    the 64-sample context are per stream.
    """

    _sessions: ClassVar[dict[str, object]] = {}

    def __init__(self, model_path: str, threads: int = 1) -> None:
        import onnxruntime as ort

        if model_path not in self._sessions:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = threads
            opts.inter_op_num_threads = 1
            self._sessions[model_path] = ort.InferenceSession(
                model_path, sess_options=opts, providers=["CPUExecutionProvider"]
            )
        self.session = self._sessions[model_path]
        self.reset()

    def reset(self) -> None:
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, _VAD_CONTEXT), dtype=np.float32)

    def __call__(self, frame: np.ndarray) -> float:
        """``frame``: 512 float32 samples at 16 kHz. Returns speech probability."""
        if frame.shape[-1] != VAD_FRAME:
            raise ValueError(f"VAD frame must be {VAD_FRAME} samples")
        x = np.concatenate([self._context, frame.reshape(1, -1).astype(np.float32)], axis=1)
        out, self._state = self.session.run(  # type: ignore[attr-defined]
            None, {"input": x, "state": self._state, "sr": np.array(SAMPLE_RATE, dtype=np.int64)}
        )
        self._context = x[:, -_VAD_CONTEXT:]
        return float(out[0][0])


def silero_model_path() -> str:
    from huggingface_hub import hf_hub_download

    # local_files_only: no network round-trip each time a call starts.
    return hf_hub_download("onnx-community/silero-vad", "onnx/model.onnx", local_files_only=True)
