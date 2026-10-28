"""Repair impossible letter sequences in Telugu/Hindi ASR output.

IndicConformer's CTC decoder emits one symbol per frame, and now and then a
stray combining mark lands next to another one, giving spellings no writer
would produce (measured on the 2026-10-15 smoke set):

* a vowel sign right before a virama:      అయి్యింది → అయ్యింది
* an anusvara right after a virama:        पन्ंद्रह → पन्द्रह
* anusvara and chandrabindu together:      पांँच → पाँच
* two vowel signs in a row (keep the last): పదిహేనుో → పదిహేనో

These strings are not real words, so translation and number reading
(पन्द्रह = 15) fail on them. Only these unambiguous patterns are touched.
"""

from __future__ import annotations

import re

# Per script: (vowel signs, virama, anusvara, chandrabindu)
_SCRIPTS = {
    "te": ("ా-ౌ", "్", "ం", "ఁ"),
    "hi": ("ा-ौ", "्", "ं", "ँ"),
}

_RULES: dict[str, list[tuple[re.Pattern[str], str]]] = {
    lang: [
        (re.compile(f"[{vowels}](?={virama})"), ""),  # vowel sign + virama → virama
        (re.compile(f"[{vowels}](?=[{vowels}])"), ""),  # two vowel signs → the last one
        (re.compile(f"(?<={virama}){anusvara}"), ""),  # virama + anusvara → virama
        (re.compile(f"{anusvara}{chandra}|{chandra}{anusvara}"), chandra),
    ]
    for lang, (vowels, virama, anusvara, chandra) in _SCRIPTS.items()
}


def clean_asr_text(text: str, lang: str) -> str:
    """Remove impossible combining-mark sequences. Other languages pass through."""
    for pattern, repl in _RULES.get(lang, []):
        text = pattern.sub(repl, text)
    return text
