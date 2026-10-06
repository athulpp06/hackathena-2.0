"""
normalizer.py - Text normalization, multilingual detection, and character offset tracking.
Preserves exact index mapping back to original text for highlighted UI spans.
"""

import re
from typing import Any
import langdetect

ZERO_WIDTH_CHARS = {'\u200b', '\u200c', '\u200d', '\uFEFF'}

HOMOGLYPHS = {
    'а': 'a', 'о': 'o', 'е': 'e', 'с': 'c', 'р': 'p', 'х': 'x', 'у': 'y',
    'і': 'i', 'ј': 'j', 'ѕ': 's', 'ԁ': 'd', 'ԛ': 'q', 'ԝ': 'w',
}

LEET_MAP = {
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '@': 'a', '$': 's'
}


def detect_language(text: str) -> str:
    """
    Detects language with fast-path Unicode script recognition for Indian scripts.
    Returns: 'en', 'hi', 'ml', or other ISO language code.
    """
    if not text or len(text.strip()) < 3:
        return 'en'
    try:
        # Check Devanagari or Malayalam Unicode blocks directly
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
        malayalam_count = len(re.findall(r'[\u0D00-\u0D7F]', text))
        total_letters = len(re.findall(r'\w', text))
        if total_letters > 0:
            if devanagari_count / total_letters > 0.15:
                return 'hi'
            if malayalam_count / total_letters > 0.15:
                return 'ml'
        return str(langdetect.detect(text))
    except Exception:
        return 'en'


def normalize_with_mapping(original_text: str) -> tuple[str, list[int]]:
    """
    Normalizes text for robust regex matching while preserving 100% accurate
    character index mappings back to the original text.

    Operations:
    1. Collapses spaced-out letters (runs of 4+ single chars: 'W h a t s A p p' -> 'whatsapp').
    2. Maps Cyrillic homoglyphs to ASCII lookalikes.
    3. Maps leetspeak digits (0->o, 1->i, 3->e, 4->a, 5->s) ONLY when part of mixed-alpha words (leaves '50000' untouched).
    4. Strips zero-width invisible characters.
    5. Returns normalized string and offset map where offset_map[i] = original_index in original_text.
    """
    if not original_text:
        return "", []

    # 1. Pre-identify runs of single characters separated by spaces (e.g. 'W h a t s A p p')
    spaced_matches = list(re.finditer(r'(?i)\b[a-z](?:\s+[a-z]){3,}\b', original_text))
    skip_space_indices = set()
    for m in spaced_matches:
        for idx in range(m.start(), m.end()):
            if original_text[idx].isspace():
                skip_space_indices.add(idx)

    # 2. Pre-identify tokens containing mixed letters and leetspeak digits (e.g. 'g00gle', 'w0rk', 'r3gistr4ti0n')
    word_tokens = list(re.finditer(r'\S+', original_text))
    leet_replace_indices = set()
    for wt in word_tokens:
        tok = wt.group()
        has_alpha = any(c.isalpha() for c in tok)
        has_leet = any(c in LEET_MAP for c in tok)
        if has_alpha and has_leet:
            for idx in range(wt.start(), wt.end()):
                if original_text[idx] in LEET_MAP:
                    leet_replace_indices.add(idx)

    normalized_chars: list[str] = []
    offset_map: list[int] = []

    for i, char in enumerate(original_text):
        if char in ZERO_WIDTH_CHARS:
            continue
        if i in skip_space_indices:
            continue

        c_lower = char.lower()
        if c_lower in HOMOGLYPHS:
            c_norm = HOMOGLYPHS[c_lower]
        elif i in leet_replace_indices:
            c_norm = LEET_MAP.get(char, c_lower)
        else:
            c_norm = c_lower

        normalized_chars.append(c_norm)
        offset_map.append(i)

    return "".join(normalized_chars), offset_map


def normalize_text(text: str) -> str:
    """Convenience helper returning just the normalized text string."""
    norm_text, _ = normalize_with_mapping(text)
    return norm_text
