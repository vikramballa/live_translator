from pipeline_core.facts import extract_facts
from pipeline_core.numbers import significant_numbers
from pipeline_core.repair import repair_currency, repair_numbers


def test_repair_single_corrupted_number():
    assert repair_numbers("500 రూపాయలు", "te", "Give 50 rupees", "en") == "Give 500 rupees"


def test_no_repair_when_ambiguous():
    assert repair_numbers("500 and 700 rupees", "en", "50 and 70 rupees", "en") is None
    assert repair_numbers("500 rupees", "en", "rupees", "en") is None


def test_number_with_trailing_period_is_seen():
    assert significant_numbers("That's $2,300.", "en") == ["2300"]


def test_currency_dollar_to_yuan():
    facts = extract_facts("一共2300块", "zh")
    assert repair_currency(facts, "That's $2,300. Don't wait.", "en") == "That's 2,300 yuan. Don't wait."


def test_currency_untouched_when_correct():
    facts = extract_facts("500 రూపాయలు", "te")
    assert repair_currency(facts, "500 rupees", "en") is None


def test_currency_untouched_without_money_fact():
    assert repair_currency([], "That's $5.", "en") is None


def test_zh_usd_is_not_mistaken_for_yuan():
    facts = extract_facts("five hundred dollars", "en")
    assert repair_currency(facts, "500美元", "zh") is None
