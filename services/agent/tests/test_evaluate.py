from agent.evaluate import error_rate, numbers_in


def test_error_rate_ignores_punctuation_and_number_form():
    # The agent shows numbers as digits; the reference says them in words.
    assert error_rate("ఈ బియ్యం ధర కిలోకి యాభై రూపాయలు.", "ఈ బియ్యం ధర కిలోకి 50 రూపాయలు", "te") == (0, 6)
    assert error_rate("I will not come.", "I will come", "en") == (1, 4)


def test_chinese_uses_characters():
    assert error_rate("我明天不来。", "我明天不来", "zh") == (0, 5)
    assert error_rate("我明天不来。", "我明天来", "zh") == (1, 5)


def test_numbers_in_translation():
    assert numbers_in("मेरा फोन नंबर 98480 22338 है।", "hi") == {"9848022338"}
    assert "2500" in numbers_in("మొత్తం రూ. 2,500.", "te")
