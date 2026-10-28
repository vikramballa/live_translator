import pytest
from hypothesis import given
from hypothesis import strategies as st

from pipeline_core.numbers import itn, normalize_digits, significant_numbers, to_words


def values(text: str, lang: str) -> list[str]:
    return [n.value for n in itn(text, lang).numbers]


@pytest.mark.parametrize(
    ("lang", "text", "expected_text", "expected"),
    [
        ("te", "ఐదు వందల రూపాయలు ఇవ్వండి", "500 రూపాయలు ఇవ్వండి", ["500"]),
        ("te", "రెండు లక్షల యాభై వేలు", "250000", ["250000"]),
        ("te", "ఐదు వందలకు ఇస్తాను", "500కు ఇస్తాను", ["500"]),
        ("te", "రెండున్నర కిలోలు", "2.5 కిలోలు", ["2.5"]),
        ("te", "నూట ఐదు", "105", ["105"]),
        ("te", "ఇరవై ఐదు వేలు", "25000", ["25000"]),
        ("hi", "ढाई हज़ार रुपये", "2500 रुपये", ["2500"]),
        ("hi", "साढ़े तीन सौ", "350", ["350"]),
        ("hi", "पौने दो सौ", "175", ["175"]),
        ("hi", "दो हज़ार पाँच सौ पचास", "2550", ["2550"]),
        ("en", "I paid twenty-five thousand rupees", "I paid 25000 rupees", ["25000"]),
        ("en", "a hundred and five", "105", ["105"]),
        ("en", "five lakh", "500000", ["500000"]),
        ("zh", "一共两千三百块", "一共2300块", ["2300"]),
        ("zh", "三万五", "35000", ["35000"]),
        ("zh", "百分之五十", "50%", ["50"]),
        ("zh", "5千元", "5000元", ["5000"]),
        ("zh", "三点五公斤", "3.5公斤", ["3.5"]),
    ],
)
def test_itn_examples(lang, text, expected_text, expected):
    r = itn(text, lang)
    assert r.text == expected_text
    assert [n.value for n in r.numbers] == expected


@pytest.mark.parametrize(
    ("lang", "text"),
    [
        ("te", "ఒక మనిషి వచ్చాడు"),  # "a man came": article, not a number
        ("hi", "एक आदमी आया"),
        ("en", "one man came"),
        ("zh", "一个人来了"),
        ("zh", "十分好"),  # "very good"
        ("zh", "千万不要"),  # "must not"
        ("zh", "差一点"),  # "almost"
        ("zh", "万一下雨"),  # "in case it rains"
    ],
)
def test_itn_leaves_non_numbers_alone(lang, text):
    r = itn(text, lang)
    assert r.text == text
    assert r.numbers == ()


def test_small_number_with_unit_is_kept():
    assert values("ఐదు రూపాయలు", "te") == ["5"]
    assert values("पाँच रुपये", "hi") == ["5"]
    assert values("five dollars", "en") == ["5"]
    assert values("五块", "zh") == ["5"]
    assert values("మొత్తం 3 కిలోలు.", "te") == ["3"]  # unit word with a full stop
    assert values("total 3 kilos.", "en") == ["3"]


@pytest.mark.parametrize(
    ("lang", "text", "expected"),
    [
        ("te", "నంబర్ 98480 22338. దయచేసి", "నంబర్ 9848022338. దయచేసి"),
        ("te", "ధర యాభై. సరేనా", "ధర 50. సరేనా"),
        ("en", "price is fifty. ok", "price is 50. ok"),
        ("en", "it is 2.5. ok", "it is 2.5. ok"),
    ],
)
def test_sentence_final_full_stop_survives(lang, text, expected):
    # Losing it merges two sentences before translation.
    assert itn(text, lang).text == expected


@pytest.mark.parametrize(
    ("lang", "text", "expected"),
    [
        ("te", "నా నంబర్ తొమ్మిది ఎనిమిది ఏడు ఆరు ఐదు", "98765"),
        ("en", "call 98765 43210", "9876543210"),
        ("en", "my number is 98765 43210.", "9876543210"),  # full stop at the sentence end
        ("te", "నా ఫోన్ నంబర్ 98480 22338.", "9848022338"),
        ("zh", "电话一三八一二三四五六七八", "13812345678"),
    ],
)
def test_phone_numbers_become_digit_strings(lang, text, expected):
    nums = itn(text, lang).numbers
    assert len(nums) == 1
    assert nums[0].value == expected
    assert nums[0].is_digit_string


def test_native_digits_and_separators():
    assert normalize_digits("౫౦౦") == "500"
    assert normalize_digits("५,००,०००") == "500000"
    assert normalize_digits("5,000 and 6, 7") == "5000 and 6, 7"
    assert normalize_digits("１２３") == "123"


def test_spans_point_into_new_text():
    r = itn("నాకు ఐదు వందల రూపాయలు మరియు రెండు వేలు కావాలి", "te")
    for n in r.numbers:
        assert r.text[n.start:n.end] == n.value


def test_two_separate_numbers():
    assert values("వెయ్యి వెయ్యి", "te") == ["1000", "1000"]
    assert significant_numbers("twenty rupees and thirty rupees", "en") == ["20", "30"]


# --- Property tests: words → digits round trip ---

LANGS = ["te", "hi", "en", "zh"]


@given(n=st.integers(min_value=10, max_value=999_999_999), lang=st.sampled_from(LANGS))
def test_round_trip(n, lang):
    words = to_words(n, lang)
    assert values(words, lang) == [str(n)], words


@given(n=st.integers(min_value=10, max_value=10_000_000), lang=st.sampled_from(LANGS))
def test_round_trip_in_sentence(n, lang):
    sep = "" if lang == "zh" else " "
    prefix = {"te": "ధర", "hi": "कीमत", "en": "price", "zh": "价格"}[lang]
    suffix = {"te": "రూపాయలు", "hi": "रुपये", "en": "rupees", "zh": "块"}[lang]
    text = f"{prefix}{sep}{to_words(n, lang)}{sep}{suffix}"
    assert values(text, lang) == [str(n)], text


@given(n=st.integers(min_value=0, max_value=10**12))
def test_digits_survive_itn_unchanged(n):
    for lang in LANGS:
        sep = "" if lang == "zh" else " "
        text = f"x{sep}{n}{sep}y" if lang != "zh" else f"共{n}个"
        r = itn(text, lang)
        assert r.text == text


@pytest.mark.parametrize(
    ("lang", "text", "expected"),
    [
        ("te", "మొత్తం రెండు వేల యిదు వందల రూపాయలు", ["2500"]),  # ASR spelling of ఐదు
        ("te", "ఈ నెల పదిహేనో తేదీలోపు", ["15"]),  # spoken ordinal → "15వ"
        ("te", "ఈ నెల 15వ తేదీ నాటికి", ["15"]),  # digits with a suffix (MT output)
        ("hi", "इस महीने की 15वीं तारीख", ["15"]),
        ("en", "Pay by the 15th of this month.", ["15"]),
        ("zh", "货物于星期一下午5时抵达。", ["5"]),  # 时 = o'clock
    ],
)
def test_numbers_found_in_asr_and_mt_forms(lang, text, expected):
    assert values(text, lang) == expected


def test_telugu_ordinal_is_written_with_va():
    assert itn("ఈ నెల పదిహేనో తేదీలోపు", "te").text == "ఈ నెల 15వ తేదీలోపు"
