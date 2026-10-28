"""Key-Fact chips: prices, quantities, percentages and phone numbers.

Facts are extracted from the *speaker's* text (after number normalisation) and
shown to both people as language-neutral chips such as ``₹2,500`` or
``98765 43210``. Even if a translation garbles a number, the chip is
correct, and the listener can tap Repeat if the two disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .numbers import ItnResult, itn

FactKind = Literal["money", "percent", "phone", "quantity", "number"]

# word (lower-case) → (kind, unit code)
_UNIT_LEXICON: dict[str, dict[str, tuple[FactKind, str]]] = {
    "te": {
        **dict.fromkeys(["రూపాయలు", "రూపాయల", "రూపాయి", "రూపాయ", "రూ"], ("money", "INR")),
        **dict.fromkeys(["డాలర్లు", "డాలర్"], ("money", "USD")),
        **dict.fromkeys(["కిలో", "కిలోలు", "కేజీ", "కేజీలు"], ("quantity", "kg")),
        **dict.fromkeys(["లీటర్", "లీటర్లు"], ("quantity", "L")),
        **dict.fromkeys(["శాతం"], ("percent", "%")),
        **dict.fromkeys(["ఎకరాలు", "ఎకరం"], ("quantity", "acre")),
        **dict.fromkeys(["టన్నులు"], ("quantity", "t")),
    },
    "hi": {
        **dict.fromkeys(["रुपये", "रुपए", "रुपया", "रु"], ("money", "INR")),
        **dict.fromkeys(["डॉलर"], ("money", "USD")),
        **dict.fromkeys(["किलो"], ("quantity", "kg")),
        **dict.fromkeys(["लीटर"], ("quantity", "L")),
        **dict.fromkeys(["प्रतिशत"], ("percent", "%")),
        **dict.fromkeys(["एकड़"], ("quantity", "acre")),
        **dict.fromkeys(["टन"], ("quantity", "t")),
    },
    "en": {
        **dict.fromkeys(["rupees", "rupee", "rs", "inr"], ("money", "INR")),
        **dict.fromkeys(["dollars", "dollar", "usd"], ("money", "USD")),
        **dict.fromkeys(["yuan", "rmb", "renminbi"], ("money", "CNY")),
        **dict.fromkeys(["kg", "kilo", "kilos", "kilograms", "kilogram"], ("quantity", "kg")),
        **dict.fromkeys(["litre", "litres", "liter", "liters"], ("quantity", "L")),
        **dict.fromkeys(["percent", "per cent"], ("percent", "%")),
        **dict.fromkeys(["acres", "acre"], ("quantity", "acre")),
        **dict.fromkeys(["tons", "tonnes", "ton", "tonne"], ("quantity", "t")),
    },
    "zh": {
        **dict.fromkeys(["元", "块", "块钱", "人民币"], ("money", "CNY")),
        **dict.fromkeys(["卢比"], ("money", "INR")),
        **dict.fromkeys(["美元"], ("money", "USD")),
        **dict.fromkeys(["公斤"], ("quantity", "kg")),
        **dict.fromkeys(["斤"], ("quantity", "jin")),
        **dict.fromkeys(["升"], ("quantity", "L")),
        **dict.fromkeys(["吨"], ("quantity", "t")),
        **dict.fromkeys(["亩"], ("quantity", "mu")),
    },
}
_PREFIX_SYMBOLS = {"₹": "INR", "$": "USD", "¥": "CNY", "Rs": "INR", "Rs.": "INR"}
_CURRENCY_SIGN = {"INR": "₹", "USD": "$", "CNY": "¥"}


@dataclass(frozen=True)
class KeyFact:
    kind: FactKind
    value: str  # canonical digits, e.g. "2500" or "9876543210"
    unit: str | None
    display: str  # e.g. "₹2,500", "50%", "98765 43210", "2.5 kg"


def group_indian(digits: str) -> str:
    """2500000 → 25,00,000"""
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join([*parts, tail])


def group_western(digits: str) -> str:
    return f"{int(digits):,}"


def format_value(value: str, unit: str | None) -> str:
    whole, _, frac = value.partition(".")
    if not whole.isdigit():
        return value
    grouped = group_indian(whole) if unit == "INR" or unit is None else group_western(whole)
    return grouped + (f".{frac}" if frac else "")


def _format_phone(d: str) -> str:
    if len(d) == 10:
        return f"{d[:5]} {d[5:]}"
    if len(d) == 11 and d.startswith("1"):  # Chinese mobile
        return f"{d[:3]} {d[3:7]} {d[7:]}"
    return " ".join(d[i: i + 4] for i in range(0, len(d), 4))


def _next_word(text: str, end: int, lang: str) -> str:
    rest = text[end:].lstrip()
    if lang == "zh":
        for n in (3, 2, 1):
            if rest[:n] in _UNIT_LEXICON["zh"]:
                return rest[:n]
        return ""
    word = rest.split(maxsplit=1)[0] if rest else ""
    return word.strip(".,;:!?।").lower()


def _unit_entry(word: str, lang: str) -> tuple[FactKind, str] | None:
    lex = _UNIT_LEXICON.get(lang, {})
    if word in lex:
        return lex[word]
    if lang == "te":  # case endings: కిలోల, కిలోకు, రూపాయలకు → longest known form it starts with
        stems = sorted((k for k in lex if len(k) >= 3 and word.startswith(k)), key=len, reverse=True)
        if stems:
            return lex[stems[0]]
    return None


def facts_from(result: ItnResult, lang: str) -> list[KeyFact]:
    facts: list[KeyFact] = []
    for span in result.numbers:
        if span.is_digit_string and len(span.value) >= 7:
            facts.append(KeyFact("phone", span.value, None, _format_phone(span.value)))
            continue
        prefix = result.text[max(0, span.start - 3): span.start].strip()
        prefix_unit = next((code for sym, code in _PREFIX_SYMBOLS.items() if prefix.endswith(sym)), None)
        after = result.text[span.end: span.end + 1]
        word = _next_word(result.text, span.end, lang)
        if after == "%":
            facts.append(KeyFact("percent", span.value, "%", f"{span.value}%"))
        elif prefix_unit:
            sign = _CURRENCY_SIGN[prefix_unit]
            facts.append(KeyFact("money", span.value, prefix_unit, sign + format_value(span.value, prefix_unit)))
        elif (entry := _unit_entry(word, lang)) is not None:
            kind, unit = entry
            if kind == "money":
                display = _CURRENCY_SIGN[unit] + format_value(span.value, unit)
            elif kind == "percent":
                display = f"{span.value}%"
            else:
                display = f"{format_value(span.value, unit)} {unit}"
            facts.append(KeyFact(kind, span.value, unit, display))
        elif Decimal(span.value) >= 10 or span.is_digit_string:
            facts.append(KeyFact("number", span.value, None, format_value(span.value, None)))
    return _dedupe(facts)


def _dedupe(facts: list[KeyFact]) -> list[KeyFact]:
    seen: set[tuple[str, str | None]] = set()
    out = []
    for f in facts:
        key = (f.value, f.unit)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def extract_facts(text: str, lang: str) -> list[KeyFact]:
    return facts_from(itn(text, lang), lang)


# Abbreviated currency written before the number in Indic text ("రూ. 2500").
_INDIC_CURRENCY_PREFIX = ("రూ.", "రూ", "रु.", "रु", "Rs.", "Rs", "₹")


def number_kinds(text: str, lang: str) -> dict[str, set[str]]:
    """What each number in ``text`` counts: value → {"money", "quantity", "percent"}.

    Used to check that a translation kept the *kind* of a fact, not only its
    digits. The unit word right after a number wins over a currency before it:
    "రూ. 50 కిలోలు" counts kilos (IndicTrans2 hi→te turned "50 rupees a kilo"
    into exactly that). Numbers with no unit are left out.
    """
    result = itn(text, lang)
    kinds: dict[str, set[str]] = {}
    for span in result.numbers:
        if span.is_digit_string:
            continue
        entry = _unit_entry(_next_word(result.text, span.end, lang), lang)
        before = result.text[max(0, span.start - 6): span.start].rstrip()
        if result.text[span.end: span.end + 1] == "%":
            kind = "percent"
        elif entry is not None:
            kind = entry[0]
        elif before.endswith(_INDIC_CURRENCY_PREFIX) or before.endswith(tuple(_PREFIX_SYMBOLS)):
            kind = "money"
        else:
            continue
        kinds.setdefault(span.value, set()).add(kind)
    return kinds
