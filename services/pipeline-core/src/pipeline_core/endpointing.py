"""Adaptive endpointing: decide when a speaker has finished an utterance.

Input is one voice-activity probability per fixed-size frame (32 ms with
Silero at 16 kHz). Output is events with frame indices; the caller keeps the
audio and cuts it with these indices.

Why adaptive: a fixed silence timeout is either too short for
slow, thoughtful speakers (we cut them mid-sentence, and in Telugu/Hindi the
verb and negation come *last*) or too long for quick speakers (dead air).
We learn each speaker's normal within-sentence pause length and set the
end-of-turn silence a margin above it, clamped to a safe range per language.
Long monologues are split at a shorter pause so translation can start
before the speaker stops.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum


class EndReason(StrEnum):
    PAUSE = "pause"  # normal end of turn
    SOFT_SPLIT = "soft_split"  # long utterance split at a short pause
    MAX_LENGTH = "max_length"  # hard cap reached while still speaking
    FLUSH = "flush"  # stream ended / participant left


@dataclass(frozen=True)
class SpeechStart:
    frame: int  # first frame to include (pre-roll already applied)


@dataclass(frozen=True)
class SpeechEnd:
    start_frame: int  # inclusive, pre-roll applied
    end_frame: int  # exclusive; includes a little trailing silence
    reason: EndReason
    speech_frames: int  # frames above threshold inside the utterance


@dataclass(frozen=True)
class SpeechCancelled:
    """An opened utterance had too little real speech (cough, click, breath)."""

    start_frame: int


Event = SpeechStart | SpeechEnd | SpeechCancelled


@dataclass(frozen=True)
class EndpointConfig:
    frame_ms: int = 32
    start_threshold: float = 0.5
    end_threshold: float = 0.35  # hysteresis: speech continues while prob >= this
    min_start_ms: int = 96  # consecutive speech needed to open an utterance
    min_speech_ms: int = 250  # utterances with less real speech are dropped (coughs, clicks)
    pre_roll_ms: int = 320
    trailing_ms: int = 160  # silence kept after speech so words are not clipped
    # End-of-turn silence: adaptive between these bounds.
    min_pause_ms: int = 450
    max_pause_ms: int = 1200
    initial_pause_ms: int = 700
    pause_margin: float = 1.5  # end pause = p90(within-utterance pauses) × margin
    # Long utterances: after soft_split_after_ms, a shorter pause also ends the segment.
    soft_split_after_ms: int = 7000
    soft_split_pause_ms: int = 300
    max_utterance_ms: int = 15000


# Telugu and Hindi are verb-final: the decisive word (and negation) arrives
# last, so they get a longer starting pause and a higher floor.
LANGUAGE_DEFAULTS: dict[str, dict[str, int]] = {
    "te": {"initial_pause_ms": 750, "min_pause_ms": 550},
    "hi": {"initial_pause_ms": 700, "min_pause_ms": 500},
    "en": {"initial_pause_ms": 600, "min_pause_ms": 450},
    "zh": {"initial_pause_ms": 550, "min_pause_ms": 400},
}


def config_for(lang: str, **overrides: int | float) -> EndpointConfig:
    return EndpointConfig(**{**LANGUAGE_DEFAULTS.get(lang, {}), **overrides})


def _percentile(values: list[int], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


@dataclass
class Endpointer:
    config: EndpointConfig = field(default_factory=EndpointConfig)
    _frame: int = 0
    _in_speech: bool = False
    _start_run: int = 0  # consecutive frames above start threshold while idle
    _utt_start: int = 0
    _last_speech: int = -1
    _speech_frames: int = 0
    _silence_run: int = 0
    _pauses: deque[int] = field(default_factory=lambda: deque(maxlen=60))

    # --- Adaptive pause ---
    @property
    def end_pause_ms(self) -> float:
        c = self.config
        if len(self._pauses) < 5:
            return float(c.initial_pause_ms)
        p90 = _percentile(list(self._pauses), 0.9) * c.frame_ms
        return min(max(p90 * c.pause_margin, c.min_pause_ms), c.max_pause_ms)

    def _frames(self, ms: float) -> int:
        return max(1, round(ms / self.config.frame_ms))

    # --- Main loop ---
    def push(self, prob: float) -> list[Event]:
        """Feed one frame's speech probability; return any events."""
        c = self.config
        events: list[Event] = []
        f = self._frame
        self._frame += 1

        if not self._in_speech:
            self._start_run = self._start_run + 1 if prob >= c.start_threshold else 0
            if self._start_run >= self._frames(c.min_start_ms):
                first_speech = f - self._start_run + 1
                self._in_speech = True
                self._utt_start = max(0, first_speech - self._frames(c.pre_roll_ms))
                self._last_speech = f
                self._speech_frames = self._start_run
                self._silence_run = 0
                self._start_run = 0
                events.append(SpeechStart(self._utt_start))
            return events

        # In speech.
        if prob >= c.end_threshold:
            if self._silence_run:
                # A pause that did not end the utterance: learn from it.
                self._pauses.append(self._silence_run)
            self._silence_run = 0
            self._last_speech = f
            self._speech_frames += 1
        else:
            self._silence_run += 1

        length_ms = (f - self._utt_start + 1) * c.frame_ms
        reason: EndReason | None = None
        if self._silence_run >= self._frames(self.end_pause_ms):
            reason = EndReason.PAUSE
        elif length_ms >= c.soft_split_after_ms and self._silence_run >= self._frames(
            c.soft_split_pause_ms
        ):
            reason = EndReason.SOFT_SPLIT
        elif length_ms >= c.max_utterance_ms:
            reason = EndReason.MAX_LENGTH

        if reason is not None:
            events.extend(self._close(reason, continuing=reason == EndReason.MAX_LENGTH))
        return events

    def flush(self) -> list[Event]:
        """Close any open utterance (call when the audio stream ends)."""
        if not self._in_speech:
            return []
        return self._close(EndReason.FLUSH, continuing=False)

    def _close(self, reason: EndReason, continuing: bool) -> list[Event]:
        c = self.config
        if continuing:
            end = self._frame  # cut right here; speech goes on in a new utterance
        else:
            end = min(self._frame, self._last_speech + 1 + self._frames(c.trailing_ms))
        speech = self._speech_frames
        start = self._utt_start
        self._in_speech = False
        self._silence_run = 0
        self._start_run = 0
        events: list[Event] = []
        if speech >= self._frames(c.min_speech_ms):
            events.append(SpeechEnd(start, end, reason, speech))
        else:
            events.append(SpeechCancelled(start))
        if continuing:
            # Re-open immediately: the speaker has not stopped.
            self._in_speech = True
            self._utt_start = self._frame
            self._speech_frames = 0
            self._last_speech = self._frame - 1
            events.append(SpeechStart(self._utt_start))
        return events

    @property
    def in_speech(self) -> bool:
        return self._in_speech

    @property
    def frame_index(self) -> int:
        return self._frame
