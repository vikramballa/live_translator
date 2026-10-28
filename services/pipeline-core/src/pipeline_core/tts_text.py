"""Prepare translated text for speech synthesis.

* Digits become words in the listener's language (TTS front-ends misread
  long numbers, and phone numbers must be read digit by digit).
* Currency signs and % become words.
* Text is split into sentences so the first sentence can be spoken while the
  rest is still being synthesised.
"""

from __future__ import annotations

import re

from .numbers import digits_to_words, normalize_digits, to_words

_CURRENCY_WORDS = {
    "₹": {"te": "రూపాయలు", "hi": "रुपये", "en": "rupees", "zh": "卢比"},
    "$": {"te": "డాలర్లు", "hi": "डॉलर", "en": "dollars", "zh": "美元"},
    "¥": {"te": "యువాన్", "hi": "युआन", "en": "yuan", "zh": "元"},
}
_PERCENT = {"te": "శాతం", "hi": "प्रतिशत", "en": "percent", "zh": "百分之"}
_POINT = {"te": "పాయింట్", "hi": "दशमलव", "en": "point", "zh": "点"}

_NUM_RE = re.compile(r"(?:([₹$¥])\s?)?(\d+(?:\.\d+)?)(\s?%)?")


def _say_number(raw: str, lang: str) -> str:
    whole, _, frac = raw.partition(".")
    if not frac and len(whole) >= 7 and (len(whole) >= 10 or whole.startswith("0")):
        return digits_to_words(whole, lang)  # phone / account numbers
    if len(whole) > 12:
        return digits_to_words(whole, lang)
    words = to_words(int(whole), lang)
    if frac:
        sep = "" if lang == "zh" else " "
        words += sep + _POINT[lang] + sep + digits_to_words(frac, lang)
    return words


def normalize_for_tts(text: str, lang: str) -> str:
    text = normalize_digits(text)

    def repl(m: re.Match[str]) -> str:
        sign, num, pct = m.group(1), m.group(2), m.group(3)
        spoken = _say_number(num, lang)
        if pct:
            return (_PERCENT["zh"] + spoken) if lang == "zh" else f"{spoken} {_PERCENT[lang]}"
        if sign:
            cur = _CURRENCY_WORDS[sign][lang]
            return f"{spoken}{cur}" if lang == "zh" else f"{spoken} {cur}"
        return spoken

    text = _NUM_RE.sub(repl, text)
    text = re.sub(r"[*_#~`|<>\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_SENT_END_RE = re.compile(r"(?<=[.!?।॥。！？])\s*")
# Chinese/Japanese text and punctuation join without spaces.
_CJK_END_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]$")


def _join(a: str, b: str) -> str:
    return f"{a}{'' if _CJK_END_RE.search(a) else ' '}{b}"


def split_sentences(text: str, min_chars: int = 12) -> list[str]:
    """Split on sentence punctuation; merge fragments shorter than ``min_chars``."""
    parts = [p.strip() for p in _SENT_END_RE.split(text) if p and p.strip()]
    merged: list[str] = []
    for p in parts:
        if merged and len(merged[-1]) < min_chars:
            merged[-1] = _join(merged[-1], p)
        else:
            merged.append(p)
    if len(merged) > 1 and len(merged[-1]) < min_chars:
        last = merged.pop()
        merged[-1] = _join(merged[-1], last)
    return merged


_CLAUSE_RE = re.compile(r"(?<=[,;，、；])\s*")


def split_for_speech(text: str, first_max_chars: int = 50, min_chars: int = 12) -> list[str]:
    """Sentences for TTS, with a long *first* sentence cut at a comma.

    Time to first audio is the time to synthesise the first chunk; later
    chunks are synthesised while earlier ones play. Only the first sentence
    is cut, and only at a comma, so prosody elsewhere is untouched.
    """
    sentences = split_sentences(text, min_chars)
    if not sentences or len(sentences[0]) <= first_max_chars:
        return sentences
    clauses = [c for c in _CLAUSE_RE.split(sentences[0]) if c]
    head = clauses[0]
    for c in clauses[1:]:
        if len(head) >= min_chars:
            break
        head = _join(head, c)
    tail = sentences[0][len(head):].strip()
    if len(head) < min_chars or len(tail) < min_chars:
        return sentences
    return [head, tail, *sentences[1:]]
