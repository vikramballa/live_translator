"""Cheap, rule-based translation checks.

These run on every translation in well under a millisecond. A *critical*
issue triggers one retry through the fallback route (and, failing that, a
number repair); a *warning* is only counted as a metric.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from .facts import number_kinds
from .numbers import significant_numbers

Severity = Literal["critical", "warning"]

SCRIPT_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "te": ((0x0C00, 0x0C7F),),
    "hi": ((0x0900, 0x097F),),
    "en": ((0x0041, 0x005A), (0x0061, 0x007A)),
    "zh": ((0x4E00, 0x9FFF), (0x3400, 0x4DBF)),
}

# Typical characters per unit of meaning, relative to English (rough, for bounds only).
_DENSITY = {"te": 1.0, "hi": 1.0, "en": 1.0, "zh": 0.3}

_TE_NEG_VERBS = (
    # Telugu negates inside the verb (రాను = "I won't come"). The suffixes alone
    # (-ను, -దు, …) also end ordinary words (నేను), so list frequent verbs whole.
    "రాను|రావు|రాడు|రాదు|రారు|పోను|పోదు|వెళ్ళను|వెళ్లను|చేయను|చేయదు|చేయడు|చేయరు|"
    "ఇవ్వను|ఇవ్వదు|ఇవ్వడు|ఇవ్వరు|తినను|తినదు|చెప్పను|చెప్పదు|ఉండను|ఉండదు|ఉండరు|"
    "కొనను|కొనరు|అమ్మను|అమ్మరు|తెలియదు|కుదరదు|సరిపోదు|అవ్వదు|అవదు|పట్టదు|దొరకదు|"
    "నచ్చదు|ఒప్పుకోను|తీసుకోను|చూడను|మాట్లాడను|చెల్లించను|విక్రయించను|పంపను|ఇవ్వలేను"
)
# Negative imperative: పంపకండి / తీసుకోకండి = "don't send / don't take" (positive: పంపండి).
_TE_NEG_IMPERATIVE = "[\u0C00-\u0C7F]+కండి"
NEGATION: dict[str, re.Pattern[str]] = {
    # The verb list cannot see every negative form, so a *missing* Telugu marker
    # is only ever a warning.
    "te": re.compile(r"(లేదు|కాదు|వద్దు|లేను|లేవు|లేరు|కాను|కూడదు|లేక|లేని|కాని)|"
                     rf"(?<![ఀ-౿])({_TE_NEG_VERBS}|{_TE_NEG_IMPERATIVE})(?![ఀ-౿])"),
    # न / ना are left out: they are also question tags ("आओगे न?").
    "hi": re.compile(r"(?<![ऀ-ॣ])(नहीं|नहि|मत)(?![ऀ-ॣ])"),
    "en": re.compile(r"\b(not|no|never|nothing|none|nobody|cannot|can't|won't|don't|doesn't|"
                     r"didn't|isn't|aren't|wasn't|weren't|shouldn't|wouldn't|haven't|hasn't|n't)\b",
                     re.IGNORECASE),
    "zh": re.compile(r"(不|没|別|别|无|未|非|勿|甭)"),
}
# Chinese words that contain a negation character but are not negations.
_ZH_NOT_NEGATION = re.compile(r"不错|不过|不管|不同|不论|非常|未来|无论|并非|莫非|没错")


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Severity


@dataclass(frozen=True)
class QualityReport:
    issues: tuple[Issue, ...]

    @property
    def ok(self) -> bool:
        return not any(i.severity == "critical" for i in self.issues)

    @property
    def codes(self) -> list[str]:
        return [i.code for i in self.issues]


def script_ratio(text: str, lang: str) -> float:
    """Share of letters in ``text`` that belong to ``lang``'s script (1.0 if there are no
    letters, e.g. a translation that is only a phone number)."""
    ranges = SCRIPT_RANGES[lang]
    letters = [c for c in text if unicodedata.category(c)[0] in ("L", "M")]
    if not letters:
        return 1.0
    hits = sum(1 for c in letters if any(lo <= ord(c) <= hi for lo, hi in ranges))
    return hits / len(letters)


def has_negation(text: str, lang: str) -> bool:
    if lang == "zh":
        text = _ZH_NOT_NEGATION.sub("", text)
    return bool(NEGATION[lang].search(text))


def repetition_loop(text: str) -> bool:
    """Detect decoder loops such as "the the the the" or "好好好好好好好好好"."""
    if re.search(r"(.)\1{7,}", text):
        return True
    tokens = text.split() if " " in text.strip() else list(text)
    if len(tokens) < 8:
        return False
    for n in (1, 2, 3, 4):
        grams = Counter(tuple(tokens[i: i + n]) for i in range(len(tokens) - n + 1))
        if grams and grams.most_common(1)[0][1] >= max(4, len(tokens) // (2 * n)) and n * \
                grams.most_common(1)[0][1] > len(tokens) * 0.5:
            return True
    return False


def check_translation(src: str, src_lang: str, tgt: str, tgt_lang: str) -> QualityReport:
    issues: list[Issue] = []
    src_s, tgt_s = src.strip(), tgt.strip()
    if not tgt_s:
        return QualityReport((Issue("empty_output", "critical"),))

    # 1. Facts are sacred: every significant number must survive.
    src_nums = Counter(significant_numbers(src_s, src_lang))
    tgt_nums = Counter(significant_numbers(tgt_s, tgt_lang))
    missing = src_nums - tgt_nums
    extra = tgt_nums - src_nums
    if missing:
        issues.append(Issue("number_missing", "critical"))
    if extra:
        issues.append(Issue("number_added", "warning"))
    # 1b. ... and what it counts: "50 rupees a kilo" must not become "50 kilos".
    src_kinds, tgt_kinds = number_kinds(src_s, src_lang), number_kinds(tgt_s, tgt_lang)
    if any(v in src_kinds and k.isdisjoint(src_kinds[v]) for v, k in tgt_kinds.items()):
        issues.append(Issue("unit_changed", "critical"))

    # 2. Output must be in the target script (catches copy-through and wrong language).
    if script_ratio(tgt_s, tgt_lang) < 0.5:
        issues.append(Issue("wrong_script", "critical"))

    # 3. Negation should survive. Marker lists cannot see every negation (Telugu
    #    negates with verb suffixes; idioms like 不错 = "good"), so this is a
    #    warning that feeds the metrics, not a retry trigger.
    if has_negation(src_s, src_lang) and not has_negation(tgt_s, tgt_lang):
        issues.append(Issue("negation_lost", "warning"))

    # 4. Length sanity, adjusted for script density.
    s_len = max(1.0, len(src_s) / _DENSITY[src_lang])
    t_len = max(1.0, len(tgt_s) / _DENSITY[tgt_lang])
    ratio = t_len / s_len
    if len(src_s) >= 12 and not (0.3 <= ratio <= 3.5):
        issues.append(Issue("length_ratio", "warning"))

    # 5. Decoder loops.
    if repetition_loop(tgt_s):
        issues.append(Issue("repetition", "critical"))

    return QualityReport(tuple(issues))
