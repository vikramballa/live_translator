import pytest

from pipeline_core.facts import extract_facts, group_indian
from pipeline_core.quality import check_translation, has_negation, repetition_loop, script_ratio
from pipeline_core.tts_text import normalize_for_tts, split_sentences

# --- Facts ---

def test_money_fact_te():
    facts = extract_facts("ఐదు వందల రూపాయలు ఇవ్వండి", "te")
    assert [(f.kind, f.value, f.display) for f in facts] == [("money", "500", "₹500")]


def test_money_fact_hi_lakh_grouping():
    facts = extract_facts("ढाई लाख रुपये", "hi")
    assert facts[0].display == "₹2,50,000"


def test_money_fact_zh():
    facts = extract_facts("一共两千三百块", "zh")
    assert (facts[0].kind, facts[0].display) == ("money", "¥2,300")


def test_phone_fact():
    facts = extract_facts("call 98765 43210", "en")
    assert (facts[0].kind, facts[0].display) == ("phone", "98765 43210")


@pytest.mark.parametrize(
    ("src", "sl", "tgt", "tl", "changed"),
    [
        # Real IndicTrans2 hi→te output on a run-on sentence (2026-10-14).
        ("इस चावल का दाम 50 रुपये किलो है", "hi", "ఈ బియ్యం ధర రూ. 50 కిలోలు", "te", True),
        ("इस चावल का दाम 50 रुपये किलो है", "hi", "ఈ బియ్యం ధర కిలోకు 50 రూపాయలు.", "te", False),
        ("कुल 2500 रुपये हुए।", "hi", "మొత్తం రూ. 2500.", "te", False),  # currency before the number
        ("I need 3 kilos.", "en", "నాకు 3 రూపాయలు కావాలి.", "te", True),
        ("这个大米每公斤50块。", "zh", "The rice is 50 yuan per kg.", "en", False),
        ("Call me at 5.", "en", "5 గంటలకు కాల్ చేయండి.", "te", False),  # no unit in the source
    ],
)
def test_unit_changed(src, sl, tgt, tl, changed):
    assert ("unit_changed" in check_translation(src, sl, tgt, tl).codes) is changed


def test_telugu_unit_with_case_ending():
    # కిలోల = "of kilos"; small numbers only become facts when a unit follows.
    assert [f.display for f in extract_facts("నాకు మూడు కిలోల టమోటాలు కావాలి", "te")] == ["3 kg"]
    assert [f.display for f in extract_facts("కిలోకు యాభై రూపాయలకు ఇస్తాను", "te")] == ["₹50"]
    r = check_translation("मुझे 3 किलो टमाटर चाहिए।", "hi", "నాకు 3 కిలోల టమోటాలు కావాలి.", "te")
    assert "number_missing" not in r.codes


def test_percent_and_quantity():
    assert extract_facts("百分之五十", "zh")[0].display == "50%"
    assert extract_facts("రెండున్నర కిలోలు", "te")[0].display == "2.5 kg"


def test_symbol_prefix():
    assert extract_facts("It costs ₹2500", "en")[0].display == "₹2,500"


def test_no_facts_in_plain_talk():
    assert extract_facts("how are you", "en") == []
    assert extract_facts("ఒక మనిషి వచ్చాడు", "te") == []


def test_group_indian():
    assert group_indian("2500000") == "25,00,000"
    assert group_indian("999") == "999"


# --- Quality ---

def test_good_translation_passes():
    r = check_translation("ఐదు వందల రూపాయలు ఇవ్వండి", "te", "Give 500 rupees", "en")
    assert r.ok, r.issues


def test_number_written_as_words_in_target_still_matches():
    r = check_translation("500 రూపాయలు", "te", "five hundred rupees", "en")
    assert r.ok, r.issues


def test_missing_number_is_critical():
    r = check_translation("ఐదు వందల రూపాయలు ఇవ్వండి", "te", "Give 50 rupees", "en")
    assert not r.ok
    assert "number_missing" in r.codes


def test_lakh_vs_western_formatting_matches():
    r = check_translation("రెండు లక్షల రూపాయలు", "te", "200,000 rupees", "en")
    assert r.ok, r.issues


def test_wrong_script_is_critical():
    r = check_translation("How are you?", "en", "How are you?", "te")
    assert "wrong_script" in r.codes and not r.ok


def test_negation_lost_is_a_warning():
    r = check_translation("I do not want it", "en", "我要它", "zh")
    assert "negation_lost" in r.codes
    assert r.ok  # warning only


def test_chinese_idioms_are_not_negation():
    assert not has_negation("这个不错", "zh")
    assert has_negation("我不要", "zh")


def test_hindi_negation_next_to_punctuation():
    assert has_negation("मुझे नहीं चाहिए।", "hi")
    assert has_negation("नहीं।", "hi")


def test_telugu_negative_verb_forms():
    assert has_negation("నేను రేపు రాను.", "te")  # "I won't come tomorrow"
    assert has_negation("నాకు తెలియదు", "te")
    assert not has_negation("నేను రేపు వస్తాను.", "te")  # "I will come" (ends in -ను)
    assert not has_negation("రానున్న వారం", "te")  # "the coming week": రాను inside a word
    r = check_translation("I will not come tomorrow.", "en", "నేను రేపు రాను.", "te")
    assert "negation_lost" not in r.codes


def test_repetition_loop():
    assert repetition_loop("the the the the the the the the the the")
    assert repetition_loop("好好好好好好好好好好")
    assert not repetition_loop("I will come tomorrow at five in the evening")


def test_empty_output():
    assert not check_translation("hello", "en", "  ", "te").ok


def test_script_ratio():
    assert script_ratio("నమస్తే", "te") == 1.0
    assert script_ratio("hello", "te") == 0.0
    assert script_ratio("你好", "zh") == 1.0


# --- TTS text ---

@pytest.mark.parametrize(
    ("text", "lang", "expected"),
    [
        ("Give 500 rupees", "en", "Give five hundred rupees"),
        ("₹2500", "en", "two thousand five hundred rupees"),
        ("50%", "zh", "百分之五十"),
        ("2300块", "zh", "两千三百块"),
        ("500 రూపాయలు", "te", "ఐదు వందలు రూపాయలు"),
        ("Call 9876543210", "en", "Call nine eight seven six five four three two one zero"),
        ("2.5 kg", "en", "two point five kg"),
    ],
)
def test_normalize_for_tts(text, lang, expected):
    assert normalize_for_tts(text, lang) == expected


def test_split_sentences():
    assert split_sentences("Hello there. How are you today? I am fine.", min_chars=5) == [
        "Hello there.", "How are you today?", "I am fine."]
    # fragments shorter than min_chars are merged into their neighbour
    assert split_sentences("How are you today? Fine.") == ["How are you today? Fine."]
    assert split_sentences("你好。今天天气很好，我们去公园吧。") == ["你好。今天天气很好，我们去公园吧。"]
    assert split_sentences("Hi. Ok.") == ["Hi. Ok."]


def test_long_first_sentence_is_cut_at_a_comma_for_speech():
    from pipeline_core.tts_text import split_for_speech

    text = "My name is Ramu and I am calling from Guntur, I want to buy fifty bags of rice. Thank you very much."
    assert split_for_speech(text) == [
        "My name is Ramu and I am calling from Guntur,",
        "I want to buy fifty bags of rice.",
        "Thank you very much.",
    ]
    assert split_for_speech("Short one, fine. Next.") == split_sentences("Short one, fine. Next.")
    long_no_comma = "This sentence is rather long but it has no comma anywhere inside it."
    assert split_for_speech(long_no_comma) == [long_no_comma]


def test_more_telugu_negative_forms():
    assert has_negation("నేను 300 రూపాయలకు మించి చెల్లించను.", "te")
    assert has_negation("ఈ ధరకు నేను విక్రయించను.", "te")
    assert has_negation("దయచేసి వస్తువులను పంపకండి.", "te")  # don't send
    assert not has_negation("దయచేసి వస్తువులను పంపండి.", "te")  # send


def test_translation_that_is_only_a_number_is_not_wrong_script():
    assert script_ratio("9848022338.", "te") == 1.0
    assert check_translation("9848022338", "en", "9848022338.", "te").ok
