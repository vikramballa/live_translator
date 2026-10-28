from itertools import pairwise

from hypothesis import given, settings
from hypothesis import strategies as st

from pipeline_core.endpointing import (
    EndpointConfig,
    Endpointer,
    EndReason,
    SpeechCancelled,
    SpeechEnd,
    SpeechStart,
    config_for,
)

CFG = EndpointConfig(frame_ms=32, initial_pause_ms=640, min_pause_ms=320, max_pause_ms=1280)


def run(probs, cfg=CFG):
    ep = Endpointer(cfg)
    events = []
    for p in probs:
        events.extend(ep.push(p))
    events.extend(ep.flush())
    return events


def frames(ms):
    return round(ms / 32)


def test_silence_produces_nothing():
    assert run([0.0] * 200) == []


def test_single_utterance():
    probs = [0.0] * 20 + [0.9] * frames(1500) + [0.0] * frames(1000)
    ev = run(probs)
    assert isinstance(ev[0], SpeechStart)
    ends = [e for e in ev if isinstance(e, SpeechEnd)]
    assert len(ends) == 1
    end = ends[0]
    assert end.reason == EndReason.PAUSE
    # pre-roll goes back before the first speech frame
    assert end.start_frame < 20
    # end includes a little trailing silence but not the whole pause
    speech_end = 20 + frames(1500)
    assert speech_end <= end.end_frame <= speech_end + frames(CFG.trailing_ms) + 1


def test_short_pause_does_not_split():
    probs = [0.9] * frames(800) + [0.0] * frames(300) + [0.9] * frames(800) + [0.0] * frames(1500)
    ends = [e for e in run(probs) if isinstance(e, SpeechEnd)]
    assert len(ends) == 1


def test_long_pause_splits():
    probs = [0.9] * frames(800) + [0.0] * frames(1500) + [0.9] * frames(800) + [0.0] * frames(1500)
    ends = [e for e in run(probs) if isinstance(e, SpeechEnd)]
    assert len(ends) == 2


def test_cough_is_cancelled():
    probs = [0.0] * 10 + [0.9] * frames(150) + [0.0] * frames(1500)
    ev = run(probs)
    assert any(isinstance(e, SpeechCancelled) for e in ev)
    assert not any(isinstance(e, SpeechEnd) for e in ev)


def test_hysteresis_keeps_utterance_open():
    # Probability dips to 0.4 (below start, above end threshold): still speech.
    probs = [0.9] * frames(500) + [0.4] * frames(1500) + [0.9] * frames(500) + [0.0] * frames(1500)
    ends = [e for e in run(probs) if isinstance(e, SpeechEnd)]
    assert len(ends) == 1


def test_max_length_cuts_and_continues():
    cfg = EndpointConfig(max_utterance_ms=3200, soft_split_after_ms=100_000)
    probs = [0.9] * frames(7000) + [0.0] * frames(1500)
    ends = [e for e in run(probs, cfg) if isinstance(e, SpeechEnd)]
    assert [e.reason for e in ends][:2] == [EndReason.MAX_LENGTH, EndReason.MAX_LENGTH]
    assert ends[-1].reason == EndReason.PAUSE
    # segments are contiguous: nothing is lost
    for a, b in pairwise(ends):
        assert b.start_frame == a.end_frame


def test_soft_split_on_long_monologue():
    cfg = EndpointConfig(soft_split_after_ms=3000, soft_split_pause_ms=320, max_utterance_ms=60_000)
    probs = ([0.9] * frames(1000) + [0.0] * frames(400)) * 6 + [0.0] * frames(1500)
    ends = [e for e in run(probs, cfg) if isinstance(e, SpeechEnd)]
    assert any(e.reason == EndReason.SOFT_SPLIT for e in ends)


def test_adaptive_pause_grows_for_slow_speaker():
    ep = Endpointer(EndpointConfig(min_pause_ms=320, max_pause_ms=1600, initial_pause_ms=700))
    # A speaker who regularly pauses ~600 ms inside sentences.
    for _ in range(8):
        for p in [0.9] * frames(700) + [0.0] * frames(600):
            ep.push(p)
    assert ep.end_pause_ms > 700


def test_language_defaults():
    assert config_for("te").initial_pause_ms > config_for("zh").initial_pause_ms


@settings(max_examples=60)
@given(st.lists(st.floats(min_value=0, max_value=1), min_size=1, max_size=1500))
def test_events_are_well_formed(probs):
    ev = run(probs)
    open_ = False
    last_end = 0
    for e in ev:
        if isinstance(e, SpeechStart):
            assert not open_
            open_ = True
        else:
            assert open_
            open_ = False
            if isinstance(e, SpeechEnd):
                assert e.start_frame < e.end_frame <= len(probs)
                assert e.start_frame >= 0
                assert e.end_frame >= last_end
                last_end = e.end_frame
    assert not open_  # flush always closes
