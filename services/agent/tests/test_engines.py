"""Model registry bookkeeping (no models are loaded)."""

from agent import engines


def test_needed_keys_cover_a_call_and_nothing_else():
    keys = engines.needed_keys({"hi", "te"})
    assert "asr:indic_conformer:ai4bharat/indic-conformer-600m-multilingual" in keys
    assert "punct:1-800-BAD-CODE/xlm-roberta_punctuation_fullstop_truecase" in keys
    assert "mt:indictrans2:ai4bharat/indictrans2-indic-indic-dist-320M" in keys
    assert "mt:indictrans2:ai4bharat/indictrans2-en-indic-dist-200M" in keys  # hi↔te fallback
    assert not any("whisper" in k or "parakeet" in k or "m2m100" in k for k in keys)


def test_release_unused_drops_models_and_their_warmups(monkeypatch):
    closed = []

    class Fake:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(engines, "_loaded", {"asr:x:y": Fake(), "mt:a:b": object()})
    monkeypatch.setattr(engines, "_warmed", {"asr:x:y|te", "mt:a:b|te>hi"})
    monkeypatch.setattr(engines, "needed_keys", lambda _langs: {"mt:a:b"})
    engines.release_unused(set())
    assert list(engines._loaded) == ["mt:a:b"]
    assert engines._warmed == {"mt:a:b|te>hi"}
    assert closed == [True]
