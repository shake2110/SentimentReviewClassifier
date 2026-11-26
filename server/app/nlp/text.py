"""Tokenisation and review splitting.

A review is broken down in three levels:

    sentence  ->  segment  ->  fragment

* sentences are split on terminal punctuation / newlines,
* segments are split on contrast markers ("but", "however", ";" ...), which
  almost always separate two different opinions,
* fragments are split on soft joiners ("and", ",", "also" ...), which *may*
  separate opinions ("leather is great and the lace is weak") or may not
  ("the camera and screen are both bad"). The pipeline decides later whether
  fragments get merged back, based on which product parts they mention.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
CONTRAST_RE = re.compile(
    r"\s*(?:;|\s[-–—]\s|\bbut\b|\bhowever\b|\balthough\b|\bthough\b|"
    r"\bwhereas\b|\bwhile\b|\bexcept\b|\bon the other hand\b)\s*",
    re.IGNORECASE,
)
JOIN_RE = re.compile(r"\s*(?:,|&|\band\b|\balso\b|\bplus\b)\s*", re.IGNORECASE)

# Negations are deliberately absent: "not" carries opinion.
STOPWORDS = frozenset(
    """
    a an the this that these those it its it's they them their there here i me my
    we our you your he she his her him is are was were be been being am do does did
    has have had having to of in on at for with by from as into onto about over
    under after before so very really quite pretty just too also than then which who
    whom what when where why how all any both each few more most some such only own
    same can will would should could may might must shall s t d ll m re ve y
    if or because until up down out off again further once one get got gets
    overall bit lot lots much many even still
    otherwise honestly actually basically anyway frankly personally literally
    generally mostly totally though however besides additionally plus then now well
    """.split()
)

PRONOUNS = frozenset(
    "it its it's they them their theirs these those this that he she his her".split()
)

# Words that describe the product as a whole; they must never be matched to a
# specific part by semantic similarity.
GENERIC_WORDS = frozenset(
    """
    product item thing things stuff purchase buy bought order quality price value
    money cost brand seller delivery shipping package packaging box product's
    shoe shoes phone phones device pair pairs model one ones
    """.split()
)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def normalize(token: str) -> str:
    """Very small, predictable singulariser (laces -> lace, batteries -> battery)."""
    if token.endswith("'s"):
        token = token[:-2]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith(("ses", "xes", "zes", "ches", "shes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


@dataclass
class Fragment:
    text: str
    tokens: list[str]
    start: int = 0  # character span in the original review
    end: int = 0
    # Filled in by the matcher: aspect_id -> MatchInfo
    matches: dict = field(default_factory=dict)
    # indices of tokens that were consumed by an aspect match
    aspect_token_idx: set = field(default_factory=set)

    @property
    def has_opinion_content(self) -> bool:
        """True if the fragment says something beyond naming a part."""
        for i, tok in enumerate(self.tokens):
            if i in self.aspect_token_idx or tok in STOPWORDS:
                continue
            return True
        return False

    @property
    def starts_with_pronoun(self) -> bool:
        return bool(self.tokens) and self.tokens[0] in PRONOUNS


_TRIM = " \t\n,.;:!?-\u2013\u2014\"'()"


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start] in _TRIM:
        start += 1
    while end > start and text[end - 1] in _TRIM:
        end -= 1
    return start, end


def _split_spans(text: str, start: int, end: int, pattern: re.Pattern) -> list[tuple[int, int]]:
    """Split text[start:end] on `pattern`, returning spans in original coordinates."""
    spans, cursor = [], start
    for m in pattern.finditer(text, start, end):
        if m.start() == m.end():  # zero-width split (sentence lookbehind)
            continue
        spans.append((cursor, m.start()))
        cursor = m.end()
    spans.append((cursor, end))
    return spans


def snippet(text: str, start: int, end: int) -> str:
    s, e = _trim(text, start, end)
    return " ".join(text[s:e].split())


def split_review(text: str) -> list[list[list[Fragment]]]:
    """Return sentences -> segments -> fragments. Empty pieces are dropped."""
    sentences = []
    for s_start, s_end in _split_spans(text, 0, len(text), SENTENCE_RE):
        segments = []
        for g_start, g_end in _split_spans(text, s_start, s_end, CONTRAST_RE):
            fragments = []
            for f_start, f_end in _split_spans(text, g_start, g_end, JOIN_RE):
                f_start, f_end = _trim(text, f_start, f_end)
                tokens = tokenize(text[f_start:f_end])
                if tokens:
                    fragments.append(Fragment(snippet(text, f_start, f_end), tokens, f_start, f_end))
            if fragments:
                segments.append(fragments)
        if segments:
            sentences.append(segments)
    return sentences
