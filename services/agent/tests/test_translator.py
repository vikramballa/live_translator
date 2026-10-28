"""Agent-level tests with fake models: the wiring of ITN → MT → checks → repair → TTS text."""

import pytest

from agent import engines, translator


class FakeMT:
    def __init__(self, table: dict[str, str]):
        self.table = table
        self.calls: list[list[str]] = []

    def translate(self, texts, _src, _tgt):
        self.calls.append(list(texts))
        return [self.table.get(t, t) for t in texts]


@pytest.fixture
def route(monkeypatch):
    def install(table, hops=1, fallback_table=None):
        mts = [FakeMT(table) for _ in range(hops)]
        chain = []
        for i, mt in enumerate(mts):
            chain.append((mt, "src" if i == 0 else "en", "tgt"))
        fb = FakeMT(fallback_table) if fallback_table is not None else None
        fb_chain = [(fb, "src", "tgt")] if fb else []
        monkeypatch.setattr(translator, "mt_route", lambda _s, _t, fallback=False: fb_chain if fallback else chain)
        return [*mts, fb] if fb else mts
    return install


def test_numbers_reach_mt_as_digits_and_facts_are_extracted(route):
    (mt,) = route({"500 రూపాయలు ఇవ్వండి": "Give 500 rupees"})
    r = translator.process_text("ఐదు వందల రూపాయలు ఇవ్వండి", "te", "en")
    assert mt.calls == [["500 రూపాయలు ఇవ్వండి"]]
    assert r.tgt_text == "Give 500 rupees"
    assert [f.display for f in r.facts] == ["₹500"]
    assert r.issues == []
    assert r.tts_sentences == ["Give five hundred rupees"]


def test_corrupted_number_is_repaired(route):
    route({"500 రూపాయలు ఇవ్వండి": "Give 50 rupees"})
    r = translator.process_text("ఐదు వందల రూపాయలు ఇవ్వండి", "te", "en")
    assert r.tgt_text == "Give 500 rupees"
    assert "number_repaired" in r.issues


def test_currency_is_restored(route):
    route({"一共2300块。": "That's $2,300."})
    r = translator.process_text("一共两千三百块。", "zh", "en")
    assert r.tgt_text == "That's 2,300 yuan."
    assert "currency_repaired" in r.issues


def test_sentences_are_translated_separately(route):
    (mt,) = route({"Hello.": "你好。", "500 rupees.": "500卢比。"})
    r = translator.process_text("Hello. 500 rupees.", "en", "zh")
    assert mt.calls == [["Hello.", "500 rupees."]]
    assert r.tgt_text == "你好。500卢比。"


def test_sentence_that_drops_a_number_is_retried_by_the_fallback_route(route):
    # Real IndicTrans2 hi→te behaviour (2026-10-14): "50 रुपये" → "రూ." with no number.
    ok, cut = "మొత్తం 3 కిలోలు.", "ఈ బియ్యం ధర రూ."
    fixed = "ఈ బియ్యం ధర కిలోకు 50 రూపాయలు."
    _primary, fb = route(
        {"कुल 3 किलो।": ok, "इस चावल का दाम 50 रुपये किलो है।": cut},
        fallback_table={"इस चावल का दाम 50 रुपये किलो है।": fixed},
    )
    r = translator.process_text("कुल 3 किलो। इस चावल का दाम 50 रुपये किलो है।", "hi", "te")
    assert fb.calls == [["इस चावल का दाम 50 रुपये किलो है।"]]  # only the bad sentence
    assert r.tgt_text == f"{ok} {fixed}"
    assert "number_missing" not in r.issues


def test_fallback_that_also_drops_the_number_is_not_used(route):
    src = "इस चावल का दाम 50 रुपये किलो है।"
    route({src: "ఈ బియ్యం ధర రూ."}, fallback_table={src: "బియ్యం ఖరీదు."})
    r = translator.process_text(src, "hi", "te")
    assert r.tgt_text == "ఈ బియ్యం ధర రూ."
    assert "number_missing" in r.issues  # the caption is flagged "check this number"


def test_dropped_full_stop_is_restored(route):
    route({"这个大米每公斤50块。": "కిలో బియ్యానికి 50 యువాన్", "我明天不来。": "నేను రేపు రావడం లేదు."})
    r = translator.process_text("这个大米每公斤五十块。我明天不来。", "zh", "te")
    assert r.tgt_text == "కిలో బియ్యానికి 50 యువాన్. నేను రేపు రావడం లేదు."
    route({"I will not come.": "我不来"})
    assert translator.process_text("I will not come.", "en", "zh").tgt_text == "我不来。"


def test_empty_input_returns_none(route):
    route({})
    assert translator.process_text("   ", "en", "te") is None


def test_pivot_route_chains_hops(route):
    first, second = route({}, hops=2)
    translator.process_text("hello there friend", "te", "zh")
    assert first.calls and second.calls


def test_route_table_covers_every_enabled_pair():
    from agent.settings import languages, routes

    for a, b in languages()["pairs"]:
        assert f"{a}>{b}" in routes()["mt"] and f"{b}>{a}" in routes()["mt"]
        assert a in routes()["asr"] and b in routes()["tts"]


def test_unknown_route_raises():
    engines.mt_route.cache_clear()
    with pytest.raises(ValueError):
        engines.mt_route("hi", "zh")
