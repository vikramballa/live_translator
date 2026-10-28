"""Spoken-number handling for te / hi / en / zh.

Two directions:

* ``itn(text, lang)`` (inverse text normalisation): turns spoken number words
  into digits, e.g. ``"ఐదు వందల రూపాయలు" → "500 రూపాయలు"``. It runs on ASR
  output *before* translation, so prices and phone numbers reach the
  translator as digits, which it copies reliably, and so we can verify them.
* ``to_words(n, lang)``: digits back into words, used to normalise text
  before speech synthesis.

Design rule: never invent a number. A run of number words is converted only
when it is *significant*: its value is at least 10, it is a digit string
(phone numbers), or a unit or currency word follows it. This keeps
article-like words such as ఒక / एक / "one" / 一 untouched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

Lang = str  # "te" | "hi" | "en" | "zh"

# --- Digit normalisation -------------------------------------------------------

_NATIVE_DIGITS = {
    **{chr(0x0C66 + i): str(i) for i in range(10)},  # Telugu ౦-౯
    **{chr(0x0966 + i): str(i) for i in range(10)},  # Devanagari ०-९
    **{chr(0xFF10 + i): str(i) for i in range(10)},  # Full-width ０-９
}
_NATIVE_RE = re.compile("[" + "".join(_NATIVE_DIGITS) + "]")
# 5,000 and Indian 5,00,000. A comma followed by a space is a list, not a separator.
_THOUSANDS_SEP_RE = re.compile(r"(?<=\d),(?=\d{2,3}(?:\D|$))")


def normalize_digits(text: str) -> str:
    """Native digits to ASCII and drop thousands separators."""
    text = _NATIVE_RE.sub(lambda m: _NATIVE_DIGITS[m.group()], text)
    return _THOUSANDS_SEP_RE.sub("", text)


def canonical(value: Decimal) -> str:
    """``Decimal('2500.0') → '2500'``, ``Decimal('1.50') → '1.5'``."""
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


# --- Lexicons ------------------------------------------------------------------

_TE_UNITS: dict[str, int] = {
    "సున్నా": 0,
    "ఒకటి": 1, "ఒక": 1, "ఒక్క": 1,
    "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "అయిదు": 5, "యిదు": 5, "ఇదు": 5,  # ASR writes ఐదు as యిదు
    "ఆరు": 6, "ఏడు": 7, "ఎనిమిది": 8, "తొమ్మిది": 9,
    "పది": 10, "పదకొండు": 11, "పన్నెండు": 12, "పదమూడు": 13, "పద్నాలుగు": 14,
    "పదిహేను": 15, "పదహారు": 16, "పదిహేడు": 17, "పద్దెనిమిది": 18, "పందొమ్మిది": 19,
    "ఇరవై": 20, "ముప్పై": 30, "ముప్పది": 30, "నలభై": 40, "నలబై": 40,
    "యాభై": 50, "యాబై": 50, "అరవై": 60, "డెబ్బై": 70, "డెబ్భై": 70,
    "ఎనభై": 80, "ఎనబై": 80, "తొంభై": 90, "తొంబై": 90,
}
# "X-and-a-half": రెండున్నర = 2.5
_TE_HALF_SUFFIX = "న్నర"
_TE_MULTS: dict[str, int] = {
    "వంద": 100, "వందలు": 100, "వందల": 100, "నూరు": 100, "నూట": 100,
    "వెయ్యి": 1000, "వేయి": 1000, "వేలు": 1000, "వేల": 1000,
    "లక్ష": 100_000, "లక్షలు": 100_000, "లక్షల": 100_000,
    "కోటి": 10_000_000, "కోట్లు": 10_000_000, "కోట్ల": 10_000_000,
}
# Telugu fused hundreds: ఇన్నూరు = 200 … ఏనూరు = 500
_TE_FUSED: dict[str, int] = {"ఇన్నూరు": 200, "మున్నూరు": 300, "నన్నూరు": 400, "ఏనూరు": 500}
# Case suffixes that may be glued to the last number word (ఐదు వందలకు).
_TE_SUFFIXES = ("లకు", "ల్లో", "కు", "కి", "లో", "తో", "ని", "కే", "కీ", "నే")

_HI_1_TO_99 = ["एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस", "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस", "तीस", "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस", "चालीस", "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास", "पचास", "इक्यावन", "बावन", "तिरपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ", "साठ", "इकसठ", "बासठ", "तिरसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर", "सत्तर", "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उन्यासी", "अस्सी", "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी", "नब्बे", "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे"]
assert len(_HI_1_TO_99) == 99
_HI_UNITS: dict[str, Decimal | int] = {w: i + 1 for i, w in enumerate(_HI_1_TO_99)}
_HI_UNITS.update({
    "शून्य": 0, "पांच": 5, "छः": 6, "छे": 6, "छै": 6, "पन्द्रह": 15, "अठ्ठाईस": 28,
    "उनासी": 79, "डेढ़": Decimal("1.5"), "डेढ": Decimal("1.5"),
    "ढाई": Decimal("2.5"),
})
_HI_MULTS: dict[str, int] = {
    "सौ": 100, "हज़ार": 1000, "हजार": 1000, "लाख": 100_000,
    "करोड़": 10_000_000, "करोड": 10_000_000,
}
# Modifiers on the following unit: साढ़े तीन = 3.5, सवा = +.25, पौने = -.25
_HI_MODIFIERS: dict[str, Decimal] = {
    "साढ़े": Decimal("0.5"), "साढे": Decimal("0.5"),
    "सवा": Decimal("0.25"), "पौने": Decimal("-0.25"),
}

_EN_UNITS: dict[str, int] = {
    w: i for i, w in enumerate(
        ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    )
}
_EN_UNITS.update({
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
})
_EN_MULTS: dict[str, int] = {
    "hundred": 100, "thousand": 1000, "lakh": 100_000, "lakhs": 100_000, "lac": 100_000,
    "million": 1_000_000, "crore": 10_000_000, "crores": 10_000_000, "billion": 1_000_000_000,
}
_EN_HALF = {"half": Decimal("0.5")}

# Words after a number that make it significant even when small (< 10).
UNIT_WORDS: dict[Lang, frozenset[str]] = {
    "te": frozenset(["రూపాయలు", "రూపాయల", "రూపాయి", "రూపాయ", "రూ", "కిలో", "కిలోలు", "కేజీ", "కేజీలు", "లీటర్", "లీటర్లు", "గంటలకు", "గంటలు", "శాతం", "డాలర్లు", "ఎకరాలు", "బస్తాలు", "టన్నులు"]),
    "hi": frozenset(["रुपये", "रुपए", "रुपया", "रु", "किलो", "लीटर", "बजे", "प्रतिशत", "डॉलर", "एकड़", "बोरी", "टन"]),
    "en": frozenset(["rupees", "rupee", "rs", "inr", "dollars", "dollar", "usd", "yuan", "rmb", "kg", "kilo", "kilos", "kilograms", "litre", "litres", "liter", "liters", "percent", "o'clock", "pm", "am", "acres", "bags", "tons", "tonnes"]),
    "zh": frozenset(["元", "块", "毛", "角", "卢比", "美元", "公斤", "斤", "升", "点", "时", "号", "日", "岁", "吨", "亩"]),
}

# --- Token classification for te / hi / en -------------------------------------


@dataclass(frozen=True)
class _Tok:
    kind: str  # "unit" | "mult" | "mod" | "digits" | "and"
    value: Decimal
    start: int
    end: int
    text: str
    suffix: str = ""  # Telugu case suffix glued to the word (kept on output)


@dataclass(frozen=True)
class NumberSpan:
    """A number found in normalised text. ``value`` is canonical (``"2500"``,
    ``"1.5"``) or a digit string for phone-like sequences (``"9876543210"``)."""

    start: int
    end: int
    value: str
    is_digit_string: bool = False


@dataclass(frozen=True)
class ItnResult:
    text: str
    numbers: tuple[NumberSpan, ...]


_WORD_RE = re.compile(r"[^\s,;:!?।॥\"“”'‘’()\[\]{}]+")
_DIGITS_RE = re.compile(r"^[₹$]?(\d+(?:\.\d+)?)$")
_EN_ORDINAL_DIGITS_RE = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)
# Digits with a case/ordinal suffix glued on: "15వ", "5కి", "15वीं".
_DIGITS_SUFFIX_RE = re.compile(r"^[₹$]?(\d+(?:\.\d+)?)([\u0C00-\u0C7F\u0900-\u097F]+)$")


def _te_lookup(word: str) -> tuple[str, Decimal, str] | None:
    """Return (kind, value, suffix) for a Telugu word, allowing a case suffix."""
    # Shortest suffix first: వందలకు = వందల + కు (not వంద + లకు).
    if word.endswith("ో") and len(word) > 2:  # ordinal: పదిహేనో = 15th, written 15వ
        for base in (word[:-1] + "ు", word[:-1] + "ి"):
            if base in _TE_UNITS:
                return "unit", Decimal(_TE_UNITS[base]), "వ"
    for stem, suffix in [(word, "")] + [
        (word[: -len(s)], s)
        for s in sorted(_TE_SUFFIXES, key=len)
        if word.endswith(s) and len(word) > len(s)
    ]:
        if stem in _TE_UNITS:
            return "unit", Decimal(_TE_UNITS[stem]), suffix
        if stem in _TE_MULTS:
            return "mult", Decimal(_TE_MULTS[stem]), suffix
        if stem in _TE_FUSED:
            return "unit", Decimal(_TE_FUSED[stem]), suffix
        if stem.endswith(_TE_HALF_SUFFIX):
            base = stem[: -len(_TE_HALF_SUFFIX)]
            if base in _TE_UNITS:
                return "unit", Decimal(_TE_UNITS[base]) + Decimal("0.5"), suffix
    return None


def _classify(word: str, lang: Lang) -> tuple[str, Decimal, str] | None:
    m = _DIGITS_RE.match(word.rstrip("."))  # "$2,300." at a sentence end
    if m:
        return "digits", Decimal(m.group(1)), ""
    if lang in ("te", "hi") and (m := _DIGITS_SUFFIX_RE.match(word.rstrip("."))):
        return "digits", Decimal(m.group(1)), m.group(2)
    if lang == "en" and (m := _EN_ORDINAL_DIGITS_RE.match(word.rstrip("."))):
        return "digits", Decimal(m.group(1)), m.group(2)
    word = word.rstrip(".")  # sentence-final full stop ("యాభై.")
    if lang == "te":
        return _te_lookup(word)
    if lang == "hi":
        if word in _HI_UNITS:
            return "unit", Decimal(_HI_UNITS[word]), ""
        if word in _HI_MULTS:
            return "mult", Decimal(_HI_MULTS[word]), ""
        if word in _HI_MODIFIERS:
            return "mod", _HI_MODIFIERS[word], ""
        return None
    if lang == "en":
        w = word.lower().rstrip(".")
        if w in _EN_UNITS:
            return "unit", Decimal(_EN_UNITS[w]), ""
        if w in _EN_MULTS:
            return "mult", Decimal(_EN_MULTS[w]), ""
        if w in ("and", "a"):
            return "and", Decimal(0), ""
        return None
    return None


def _tokens(text: str, lang: Lang) -> list[_Tok | None]:
    """Word tokens; ``None`` marks a non-number word (a run boundary)."""
    out: list[_Tok | None] = []
    for m in _WORD_RE.finditer(text):
        word = m.group()
        parts = [word]
        start = m.start()
        if lang == "en" and "-" in word:  # twenty-five
            parts = word.split("-")
        offset = start
        for part in parts:
            c = _classify(part, lang)
            if c is None:
                out.append(None)
            else:
                kind, value, suffix = c
                out.append(_Tok(kind, value, offset, offset + len(part), part, suffix))
            offset += len(part) + 1
    return out


def _parse_run(run: list[_Tok]) -> list[tuple[int, int, Decimal | str, str]]:
    """Split a run of number tokens into numbers.

    Returns ``(first_idx, last_idx, value, suffix)`` per number; ``value`` is a
    digit string for spoken digit sequences (phone numbers).
    """
    results: list[tuple[int, int, Decimal | str, str]] = []

    def digit_like(t: _Tok) -> bool:
        if t.kind == "unit":
            return t.value < 10 and t.value == t.value.to_integral_value()
        # A trailing full stop ends the sentence ("… 98480 22338."); any other dot is a decimal.
        return t.kind == "digits" and not t.suffix and "." not in t.text.rstrip(".")

    def digit_text(t: _Tok) -> str:
        return str(int(t.value)) if t.kind == "unit" else t.text.lstrip("₹$").rstrip(".")

    i = 0
    n = len(run)
    while i < n:
        # Phone numbers: digits read one by one ("తొమ్మిది ఎనిమిది ఏడు …") or
        # written in groups ("98765 43210") become one digit string.
        j = i
        while j < n and digit_like(run[j]) and not (j + 1 < n and run[j + 1].kind == "mult"):
            j += 1
        span = run[i:j]
        if span:
            spoken = sum(1 for t in span if t.kind == "unit")
            digits = "".join(digit_text(t) for t in span)
            if spoken >= 3 or len(digits) >= 10:
                results.append((i, j - 1, digits, span[-1].suffix))
                i = j
                continue
        i = _parse_arith(run, i, results)
    return results


def _parse_arith(run: list[_Tok], i: int, results: list) -> int:
    """Parse one arithmetic number starting at ``run[i]``; return next index."""
    n = len(run)
    total = Decimal(0)
    current = Decimal(0)
    last_small: Decimal | None = None  # last < 100 value added to current
    last_big: Decimal | None = None  # last multiplier >= 1000 applied
    modifier = Decimal(0)
    start = i
    end = i
    seen_value = False
    while i < n:
        t = run[i]
        if t.kind == "and":
            # "a hundred", "one hundred and five"
            if i + 1 < n and run[i + 1].kind in ("unit", "mult", "digits") and (seen_value or (
                t.text.lower() == "a" and run[i + 1].kind == "mult")):
                i += 1
                continue
            break
        if t.kind == "mod":
            if seen_value and current:
                break
            modifier = t.value
            i += 1
            continue
        if t.kind in ("unit", "digits"):
            v = t.value
            if seen_value and last_small is not None:
                # 20 + 5 → 25 (twenty five / ఇరవై ఐదు); anything else starts a new number.
                if last_small % 10 == 0 and 20 <= last_small <= 90 and 1 <= v <= 9 and t.kind == "unit":
                    current += v
                    last_small = None
                    end = i
                    i += 1
                    continue
                break
            if seen_value and last_small is None and current % 100 == 0 and current >= 100 and v < 100:
                current += v  # "రెండు వందల యాభై" = 200 + 50
            elif seen_value and current == 0 and total > 0 and v < 1000:
                current = v  # after a big multiplier: "five thousand three hundred"
            elif seen_value:
                break
            else:
                current = v
            if modifier:
                current += modifier
                modifier = Decimal(0)
            last_small = v if v < 100 else None
            seen_value = True
            end = i
            i += 1
            continue
        if t.kind == "mult":
            m = t.value
            if m >= 1000 and last_big is not None and m >= last_big:
                break  # "వెయ్యి వెయ్యి" → two numbers
            if m == 100 and current >= 100 and last_small is None:
                break  # "వంద వంద" → two numbers
            if current == 0:
                current = Decimal(1)  # "వంద" = 100, "వెయ్యి వంద" = 1100
            if m == 100:
                current *= 100
            else:
                total += current * m
                current = Decimal(0)
                last_big = m
            last_small = None
            seen_value = True
            end = i
            i += 1
            continue
        break
    if not seen_value:
        return i + 1
    results.append((start, end, total + current, run[end].suffix))
    return max(i, start + 1)


def _significant(value: Decimal | str, next_word: str | None, lang: Lang) -> bool:
    if isinstance(value, str):
        return True
    if value >= 10 or value != value.to_integral_value():
        return True
    return next_word is not None and is_unit_word(next_word, lang)


# Telugu attaches case endings to the unit (కిలోల, కిలోకు, రూపాయలకు), so match stems.
TE_UNIT_STEMS = ("రూపాయ", "కిలో", "కేజీ", "లీటర్", "లీటర", "గంట", "శాతం", "డాలర్", "ఎకర", "బస్తా", "టన్ను")


def is_unit_word(word: str, lang: Lang) -> bool:
    # "3 kilos." at a sentence end: the full stop is part of the word token.
    w = word.lower().rstrip(".")
    if w in UNIT_WORDS.get(lang, frozenset()):
        return True
    return lang == "te" and w.startswith(TE_UNIT_STEMS)


def _itn_words(text: str, lang: Lang) -> ItnResult:
    toks = _tokens(text, lang)
    words = [m.group() for m in _WORD_RE.finditer(text)]
    # Expand hyphenated english words so ``words`` aligns with ``toks``.
    if lang == "en":
        words = [p for w in words for p in (w.split("-") if "-" in w else [w])]
    replacements: list[tuple[int, int, str, NumberSpan | None]] = []
    numbers: list[tuple[int, int, str, bool]] = []

    idx = 0
    while idx < len(toks):
        if toks[idx] is None:
            idx += 1
            continue
        j = idx
        while j < len(toks) and toks[j] is not None:
            j += 1
        run = [t for t in toks[idx:j] if t is not None]
        for a, b, value, suffix in _parse_run(run):
            first, last = run[a], run[b]
            next_word = words[idx + b + 1] if idx + b + 1 < len(words) else None
            if not _significant(value, next_word, lang):
                continue
            is_digits = isinstance(value, str)
            rendered = value if is_digits else canonical(value)
            # Tokens that were already plain digits need no rewriting.
            if a == b and first.kind == "digits":
                lead = len(first.text) - len(first.text.lstrip("₹$"))  # "₹2500"
                start = first.start + lead
                numbers.append((start, start + len(rendered), rendered, is_digits))
                continue
            # Keep a sentence-final full stop that the last token carried ("… 22338.").
            end = last.end - (len(last.text) - len(last.text.rstrip(".")))
            replacements.append((first.start, end, rendered + suffix, None))
            numbers.append((first.start, end, rendered, is_digits))
        idx = j

    # Apply replacements right-to-left, then recompute spans in the new text.
    out = text
    for start, end, rep, _ in sorted(replacements, key=lambda r: r[0], reverse=True):
        out = out[:start] + rep + out[end:]
    # (original end, length change) of each replacement, to map old offsets to new ones.
    shifts = [(end, len(rep) - (end - start)) for start, end, rep, _ in replacements]

    def remap(pos: int) -> int:
        return pos + sum(delta for end, delta in shifts if end <= pos)

    spans = []
    for start, _end, value, is_digits in sorted(numbers):
        ns = remap(start)
        spans.append(NumberSpan(ns, ns + len(value), value, is_digits))
    return ItnResult(out, tuple(spans))


# --- Chinese -------------------------------------------------------------------

_ZH_DIGITS = {"零": 0, "〇": 0, "一": 1, "幺": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_ZH_SMALL = {"十": 10, "百": 100, "千": 1000}
_ZH_BIG = {"万": 10_000, "亿": 100_000_000}
_ZH_CHARS = set(_ZH_DIGITS) | set(_ZH_SMALL) | set(_ZH_BIG)
_ZH_RUN_RE = re.compile(r"(?:百分之)?[0-9零〇一幺二两三四五六七八九十百千万亿.点]+")
# Idioms that look like numbers but are not.
_ZH_IDIOMS = ("十分", "万一", "一一", "千万", "万万", "一点", "百万富")


def _zh_section(chars: str) -> Decimal:
    """Value of a run with 十百千万亿 and digits (ASCII digits allowed: 5千, 2.5万)."""
    total = Decimal(0)
    section = Decimal(0)
    number: Decimal | None = None
    prev_unit = 0
    i = 0
    while i < len(chars):
        ch = chars[i]
        if ch.isdigit() and ch.isascii():
            m = re.match(r"\d+(?:\.\d+)?", chars[i:])
            assert m
            number = Decimal(m.group())
            i += len(m.group())
            continue
        if ch in _ZH_DIGITS:
            number = Decimal(_ZH_DIGITS[ch])
            if ch in "零〇":
                prev_unit = 0
                number = None
        elif ch in _ZH_SMALL:
            unit = _ZH_SMALL[ch]
            section += (number if number is not None else Decimal(1)) * unit
            number = None
            prev_unit = unit
        elif ch in _ZH_BIG:
            unit = _ZH_BIG[ch]
            section += number or 0
            total = (total + section) * unit if unit == 100_000_000 else total + section * unit
            section = Decimal(0)
            number = None
            prev_unit = unit
        i += 1
    if number is not None:
        # Colloquial: 一百五 = 150, 三万五 = 35000, 两千三 = 2300
        if prev_unit >= 100:
            number *= Decimal(prev_unit) / 10
        section += number
    return total + section


def _zh_value(run: str) -> Decimal | str | None:
    body = run.replace("点", ".") if re.search(r"点[0-9零〇一二两三四五六七八九]+$", run) else run
    if "点" in body:
        return None  # time of day (三点十分) is not a decimal
    has_units = any(c in _ZH_SMALL or c in _ZH_BIG for c in body)
    if "." in body:
        whole, _, frac = body.partition(".")
        if not whole or not frac or any(c in _ZH_SMALL or c in _ZH_BIG for c in frac):
            return None
        frac_digits = "".join(str(_ZH_DIGITS[c]) if c in _ZH_DIGITS else c for c in frac)
        if not frac_digits.isdigit():
            return None
        whole_v = _zh_section(whole)
        return whole_v + Decimal("0." + frac_digits)
    if not has_units and len(body) >= 2:
        digits = "".join(str(_ZH_DIGITS[c]) if c in _ZH_DIGITS else c for c in body)
        return digits if digits.isdigit() else None
    return _zh_section(body)


def _itn_zh(text: str) -> ItnResult:
    out: list[str] = []
    spans: list[NumberSpan] = []
    pos = 0
    out_len = 0
    for m in _ZH_RUN_RE.finditer(text):
        run = m.group()
        percent = run.startswith("百分之")
        core_start = m.start() + (3 if percent else 0)
        core = text[core_start: m.end()].rstrip(".点")
        if not core or not any(c in _ZH_CHARS or c.isdigit() for c in core):
            continue
        core_end = core_start + len(core)
        before = text[m.start() - 1: m.start()] if m.start() else ""
        after = text[core_end: core_end + 2]
        if not percent and any((core + after).startswith(idiom) for idiom in _ZH_IDIOMS) and not (
            before and (before in _ZH_CHARS or before.isdigit())
        ):
            continue  # 十分好, 千万不要, 一点儿
        value: Decimal | str | None
        if core.isascii():
            if core.isdigit() and len(core) >= 10:
                value = core
            else:
                try:
                    value = Decimal(core)
                except ArithmeticError:
                    continue
        else:
            value = _zh_value(core)
        if value is None:
            continue
        unit_follows = after[:1] in UNIT_WORDS["zh"] or after[:2] in UNIT_WORDS["zh"]
        if (not percent and isinstance(value, Decimal) and value < 10
                and value == value.to_integral_value() and not unit_follows):
            continue  # 一个, 三天: small numbers stay as words
        rendered = value if isinstance(value, str) else canonical(value)
        piece = text[pos: m.start()]
        out.append(piece)
        out_len += len(piece)
        out.append(rendered + ("%" if percent else ""))
        spans.append(NumberSpan(out_len, out_len + len(rendered), rendered, isinstance(value, str)))
        out_len += len(out[-1])
        pos = core_end
    out.append(text[pos:])
    return ItnResult("".join(out), tuple(spans))


# --- Public API ----------------------------------------------------------------


def itn(text: str, lang: Lang) -> ItnResult:
    """Spoken numbers → digits. Returns the new text and the numbers found."""
    text = normalize_digits(text)
    if lang == "zh":
        return _itn_zh(text)
    return _itn_words(text, lang)


def significant_numbers(text: str, lang: Lang) -> list[str]:
    """Canonical values of all significant numbers in ``text`` (sorted)."""
    return sorted(n.value for n in itn(text, lang).numbers)


# --- Number → words (for TTS normalisation and round-trip tests) ---------------

_TE_UNIT_WORDS = {v: k for k, v in reversed(list(_TE_UNITS.items()))}
_TE_UNIT_WORDS[1] = "ఒకటి"
_TE_UNIT_WORDS[5] = "ఐదు"


def _te_below_100(n: int) -> str:
    if n in _TE_UNIT_WORDS:
        return _TE_UNIT_WORDS[n]
    tens, unit = divmod(n, 10)
    return f"{_TE_UNIT_WORDS[tens * 10]} {_TE_UNIT_WORDS[unit]}"


def _te_words(n: int) -> str:
    if n == 0:
        return "సున్నా"
    parts: list[str] = []
    crore, rest = divmod(n, 10_000_000)
    lakh, rest = divmod(rest, 100_000)
    thousand, rest = divmod(rest, 1000)
    hundred, below = divmod(rest, 100)

    def big(count: int, one: str, final: str, joined: str, more: bool) -> str:
        if count == 1:
            return one
        return f"{_te_words(count) if count >= 100 else _te_below_100(count)} {joined if more else final}"

    if crore:
        parts.append(big(crore, "కోటి", "కోట్లు", "కోట్ల", bool(lakh or thousand or hundred or below)))
    if lakh:
        parts.append(big(lakh, "లక్ష", "లక్షలు", "లక్షల", bool(thousand or hundred or below)))
    if thousand:
        parts.append(big(thousand, "వెయ్యి", "వేలు", "వేల", bool(hundred or below)))
    if hundred:
        if hundred == 1:
            parts.append("నూట" if below else "వంద")
        else:
            parts.append(f"{_TE_UNIT_WORDS[hundred]} {'వందల' if below else 'వందలు'}")
    if below:
        parts.append(_te_below_100(below))
    return " ".join(parts)


def _hi_words(n: int) -> str:
    if n == 0:
        return "शून्य"
    parts: list[str] = []
    crore, rest = divmod(n, 10_000_000)
    lakh, rest = divmod(rest, 100_000)
    thousand, rest = divmod(rest, 1000)
    hundred, below = divmod(rest, 100)
    if crore:
        parts.append(f"{_hi_words(crore)} करोड़")
    if lakh:
        parts.append(f"{_HI_1_TO_99[lakh - 1]} लाख")
    if thousand:
        parts.append(f"{_HI_1_TO_99[thousand - 1]} हज़ार")
    if hundred:
        parts.append(f"{_HI_1_TO_99[hundred - 1]} सौ")
    if below:
        parts.append(_HI_1_TO_99[below - 1])
    return " ".join(parts)


_EN_UNIT_WORDS = {v: k for k, v in _EN_UNITS.items()}


def _en_below_1000(n: int) -> str:
    parts = []
    hundred, below = divmod(n, 100)
    if hundred:
        parts.append(f"{_EN_UNIT_WORDS[hundred]} hundred")
    if below:
        if below in _EN_UNIT_WORDS:
            parts.append(_EN_UNIT_WORDS[below])
        else:
            tens, unit = divmod(below, 10)
            parts.append(f"{_EN_UNIT_WORDS[tens * 10]}-{_EN_UNIT_WORDS[unit]}")
    return " ".join(parts)


def _en_words(n: int) -> str:
    if n == 0:
        return "zero"
    parts = []
    for scale, name in ((1_000_000_000, "billion"), (1_000_000, "million"), (1000, "thousand")):
        count, n = divmod(n, scale)
        if count:
            parts.append(f"{_en_below_1000(count)} {name}")
    if n:
        parts.append(_en_below_1000(n))
    return " ".join(parts)


_ZH_DIGIT_CHARS = "零一二三四五六七八九"


def _zh_below_10000(n: int, leading: bool) -> str:
    """0 < n < 10000. ``leading``: the highest section (10-19 read as 十X, no leading 零)."""
    out = "" if leading or n >= 1000 else "零"
    started = False
    zero = False
    for d, unit in ((n // 1000, "千"), (n // 100 % 10, "百"), (n // 10 % 10, "十"), (n % 10, "")):
        if d == 0:
            zero = zero or started
            continue
        if zero:
            out += "零"
            zero = False
        if unit == "十" and d == 1 and leading and not started:
            out += "十"
        elif d == 2 and unit in ("千", "百") and not started:
            out += "两" + unit
        else:
            out += _ZH_DIGIT_CHARS[d] + unit
        started = True
    return out


def _zh_words(n: int) -> str:
    if n == 0:
        return "零"
    yi, rest = divmod(n, 100_000_000)
    wan, low = divmod(rest, 10_000)
    out = ""
    if yi:
        out += (_zh_words(yi) if yi != 2 else "两") + "亿"
    if wan:
        out += (_zh_below_10000(wan, leading=not out) if wan != 2 else "两") + "万"
    if low:
        if yi and not wan and low >= 1000:
            out += "零"
        out += _zh_below_10000(low, leading=not out)
    return out


def to_words(n: int, lang: Lang) -> str:
    if n < 0:
        raise ValueError("negative numbers are not supported")
    return {"te": _te_words, "hi": _hi_words, "en": _en_words, "zh": _zh_words}[lang](n)


def digits_to_words(digits: str, lang: Lang) -> str:
    """Read a digit string one digit at a time (phone numbers)."""
    sep = "" if lang == "zh" else " "
    return sep.join(to_words(int(d), lang) for d in digits if d.isdigit())
