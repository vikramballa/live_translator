"""Small, safe repairs for facts the translation got wrong.

Translation models occasionally corrupt exactly the things a trader cares
about. We fix only unambiguous cases and never guess:

* ``repair_numbers``: one source number missing and one unexpected number
  in the translation ("500" → "50") → substitute.
* ``repair_currency``: the speaker named one currency and the translation
  switched to another (Opus-MT renders 块/yuan as "$") → restore it.
"""

from __future__ import annotations

import re
from collections import Counter

from .facts import KeyFact
from .numbers import itn


def repair_numbers(src_text: str, src_lang: str, tgt_text: str, tgt_lang: str) -> str | None:
    """Return a repaired translation, or ``None`` if no safe repair exists."""
    src_vals = Counter(n.value for n in itn(src_text, src_lang).numbers)
    tgt = itn(tgt_text, tgt_lang)
    tgt_vals = Counter(n.value for n in tgt.numbers)
    missing = list((src_vals - tgt_vals).elements())
    extra = list((tgt_vals - src_vals).elements())
    if len(missing) != 1 or len(extra) != 1:
        return None
    span = next(n for n in tgt.numbers if n.value == extra[0])
    return tgt.text[: span.start] + missing[0] + tgt.text[span.end:]


# How each currency is written in each language: (prefix symbol, word after the number).
_CURRENCY_FORMS: dict[str, dict[str, str]] = {
    "INR": {"en": "rupees", "te": "రూపాయలు", "hi": "रुपये", "zh": "卢比"},
    "USD": {"en": "dollars", "te": "డాలర్లు", "hi": "डॉलर", "zh": "美元"},
    "CNY": {"en": "yuan", "te": "యువాన్", "hi": "युआन", "zh": "元"},
}
_CURRENCY_PATTERNS: dict[str, dict[str, re.Pattern[str]]] = {
    "en": {
        "INR": re.compile(r"(₹|\bRs\.?|\brupees?\b|\bINR\b)", re.IGNORECASE),
        "USD": re.compile(r"(\$|\bdollars?\b|\bUSD\b|\bbucks?\b)", re.IGNORECASE),
        "CNY": re.compile(r"(¥|\byuan\b|\bRMB\b|\brenminbi\b|\bCNY\b)", re.IGNORECASE),
    },
    "zh": {
        "INR": re.compile(r"(₹|卢比)"),
        "USD": re.compile(r"(\$|美元|美金)"),
        "CNY": re.compile(r"(¥|(?<!美)元|块钱|块|人民币)"),  # not the 元 in 美元
    },
    "te": {
        "INR": re.compile(r"(₹|రూపాయ[^\s.,!?।]*|రూ\.?)"),
        "USD": re.compile(r"(\$|డాలర్[^\s.,!?।]*)"),
        "CNY": re.compile(r"(¥|యువాన్[^\s.,!?।]*)"),
    },
    "hi": {
        "INR": re.compile(r"(₹|रुप[^\s.,!?।]*|रु\.?)"),
        "USD": re.compile(r"(\$|डॉलर[^\s.,!?।]*)"),
        "CNY": re.compile(r"(¥|युआन[^\s.,!?।]*)"),
    },
}
_SYMBOL_BEFORE_NUMBER = re.compile(r"([$₹¥])\s?(\d[\d,]*(?:\.\d+)?)")


def repair_currency(src_facts: list[KeyFact], tgt_text: str, tgt_lang: str) -> str | None:
    """Restore the speaker's currency if the translation switched it."""
    src_units = {f.unit for f in src_facts if f.kind == "money"}
    if len(src_units) != 1:
        return None  # none, or several currencies: too ambiguous to touch
    want = next(iter(src_units))
    assert want is not None
    pats = _CURRENCY_PATTERNS[tgt_lang]
    wrong = [code for code, pat in pats.items() if code != want and pat.search(tgt_text)]
    if not wrong:
        return None
    word = _CURRENCY_FORMS[want][tgt_lang]
    sep = "" if tgt_lang == "zh" else " "
    fixed = tgt_text
    for code in wrong:
        # "$2,300" → "2,300 yuan" (symbol before number becomes a word after it)
        sym = {"USD": "$", "INR": "₹", "CNY": "¥"}[code]
        fixed = _SYMBOL_BEFORE_NUMBER.sub(
            lambda m, s=sym: f"{m.group(2)}{sep}{word}" if m.group(1) == s else m.group(0), fixed)
        fixed = pats[code].sub(word, fixed)
    return fixed if fixed != tgt_text else None
