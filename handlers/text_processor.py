"""Text segmentation utilities.

The goal is to turn long, sprawling Uzbek posts into short, punchy fragments
that read cleanly as subtitles on a vertical mobile viewport. We split on
sentence boundaries first, then on natural phrase boundaries so every segment
stays within a small word budget (see :func:`split_text`).
"""

from __future__ import annotations

import re
from typing import List

from config import MAX_SEGMENTS


# Sentence boundary regex. Handles ``.``, ``!``, ``?`` and the Uzbek-specific
# punctuation that frequently appears in school/competition copy.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# A run of whitespace.
_WHITESPACE = re.compile(r"\s+")

# Punctuation we want to strip from the very edges of a segment so subtitles
# never start or end with a stray quote / dash.
_EDGE_PUNCT = "\"'“”‘’`-—–—–"


def _clean_segment(segment: str) -> str:
    """Normalise whitespace and strip edge punctuation from a fragment."""
    cleaned = _WHITESPACE.sub(" ", segment).strip()
    while cleaned and cleaned[0] in _EDGE_PUNCT:
        cleaned = cleaned[1:].lstrip()
    while cleaned and cleaned[-1] in _EDGE_PUNCT:
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def _split_by_words(text: str, max_words: int) -> List[str]:
    """Split a single sentence into ``max_words``-sized word chunks."""
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start : start + max_words])
        cleaned = _clean_segment(chunk)
        if cleaned:
            chunks.append(cleaned)
    return chunks


def split_text(text: str, max_words: int = 4) -> List[str]:
    """Split ``text`` into subtitle-friendly segments.

    Strategy:
        1. Split on sentence boundaries (``.``, ``!``, ``?``).
        2. For each sentence, split again on commas / semicolons so phrases
           stay punchy.
        3. If any resulting fragment is still longer than ``max_words`` words,
           hard-split it into word chunks of at most ``max_words`` words.

    Args:
        text: Raw announcement text in Uzbek (Latin script).
        max_words: Maximum number of words per segment (4-5 recommended).

    Returns:
        A list of cleaned, non-empty text segments, capped at
        :data:`config.MAX_SEGMENTS`.
    """
    if max_words < 1:
        raise ValueError("max_words must be at least 1")
    if not text:
        return []

    # Normalise whitespace first so sentence splitting behaves predictably.
    normalised = _WHITESPACE.sub(" ", text).strip()

    segments: List[str] = []
    for sentence in _SENTENCE_SPLIT.split(normalised):
        sentence = _clean_segment(sentence)
        if not sentence:
            continue

        # Try to break the sentence on commas / semicolons / em-dashes for
        # shorter, more scannable phrases.
        sub_phrases = re.split(r"[,;—–]\s*", sentence)
        for phrase in sub_phrases:
            phrase = _clean_segment(phrase)
            if not phrase:
                continue

            word_count = len(phrase.split())
            if word_count > max_words:
                # Hard-split oversized phrases into word-sized chunks.
                segments.extend(_split_by_words(phrase, max_words))
            else:
                segments.append(phrase)

    # Cap the total so generated videos never exceed a sane duration.
    if len(segments) > MAX_SEGMENTS:
        segments = segments[:MAX_SEGMENTS]
    return segments


def estimate_duration(segments: List[str], base_seconds_per_word: float = 0.35) -> float:
    """Estimate the total speech duration for a list of segments.

    A rough rule of thumb: ~0.35 s per word plus a small pause between
    segments. Used as a fallback when the actual gTTS audio is unavailable.
    """
    total_words = sum(len(seg.split()) for seg in segments)
    pauses = max(0, len(segments) - 1) * 0.4
    return total_words * base_seconds_per_word + pauses