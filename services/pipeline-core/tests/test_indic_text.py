import pytest

from pipeline_core.indic_text import clean_asr_text
from pipeline_core.numbers import itn


@pytest.mark.parametrize(
    ("lang", "heard", "clean"),
    [
        # Real IndicConformer CTC outputs, 2026-10-15 smoke set.
        ("te", "మొత్తం 2500 రూపాయలు అయి్యింది", "మొత్తం 2500 రూపాయలు అయ్యింది"),
        ("hi", "इस महीने की पन्ंद्रह तारीख", "इस महीने की पन्द्रह तारीख"),
        ("hi", "माल सोमवार शाम पांँच बजे", "माल सोमवार शाम पाँच बजे"),
        ("te", "ఈ నెల పదిహేనుో తేదీ", "ఈ నెల పదిహేనో తేదీ"),
    ],
)
def test_impossible_sequences_are_repaired(lang, heard, clean):
    assert clean_asr_text(heard, lang) == clean


@pytest.mark.parametrize(
    ("lang", "text"),
    [
        ("te", "నేను రేపు రాను. మీకు ఎన్ని బస్తాలు కావాలి?"),
        ("te", "అయ్యింది, ఇంకా, సంచులు"),
        ("hi", "मुझे वह रंग पसंद नहीं आया, पाँच, पन्द्रह, हिन्दी"),
        ("en", "plain English stays"),
        ("zh", "我明天不来。"),
    ],
)
def test_valid_text_is_unchanged(lang, text):
    assert clean_asr_text(text, lang) == text


def test_cleaning_lets_numbers_be_read():
    assert itn(clean_asr_text("पन्ंद्रह तारीख", "hi"), "hi").text == "15 तारीख"
