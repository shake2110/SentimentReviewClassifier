"""Star-rating sentiment for review clauses.

The model (nlptown/bert-base-multilingual-uncased-sentiment) is a 5-class
classifier whose labels are "1 star" ... "5 stars". Instead of taking the
arg-max label we take the *expected* star value (sum of p(k) * k). That gives
a continuous 1.0-5.0 score that averages nicely across reviews, and the
positive / neutral / negative bucket is derived from it.
"""
from __future__ import annotations

import re
from typing import Protocol, Sequence

# The model's expected-star value is compressed toward 3 on short clauses
# ("The leather feels premium" -> 3.32, "The frame feels cheap" -> 2.57).
# On a 34-clause hand-labelled set, 3.3 / 2.7 scored 25/34 vs 22/34 for 3.5 / 2.5.
POSITIVE_FROM = 3.3  # expected stars >= this  -> positive
NEGATIVE_UPTO = 2.7  # expected stars <= this  -> negative


def label_for(stars: float) -> str:
    if stars >= POSITIVE_FROM:
        return "positive"
    if stars <= NEGATIVE_UPTO:
        return "negative"
    return "neutral"


class SentimentScorer(Protocol):
    def score(self, texts: Sequence[str]) -> list[float]:
        """Return an expected star rating (1.0-5.0) for each text."""
        ...


class StarModelScorer:
    MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

    def __init__(self, model_name: str | None = None):
        from transformers import pipeline

        self._pipe = pipeline(
            "text-classification",
            model=model_name or self.MODEL_NAME,
            top_k=None,  # return the probability of every star class
            truncation=True,
            max_length=512,
        )

    @staticmethod
    def _stars_from_label(label: str) -> int:
        match = re.match(r"\s*(\d)", label)
        if not match:
            raise ValueError(f"Unexpected sentiment label: {label!r}")
        return int(match.group(1))

    def score(self, texts: Sequence[str]) -> list[float]:
        if not texts:
            return []
        outputs = self._pipe(list(texts), batch_size=16)
        results = []
        for dist in outputs:
            expected = sum(self._stars_from_label(d["label"]) * d["score"] for d in dist)
            results.append(round(expected, 2))
        return results


class LexiconScorer:
    """Tiny rule-based fallback (no ML). Used by tests and NLP_MODE=lite."""

    POSITIVE = set(
        "good great excellent amazing awesome love loved perfect nice comfortable comfy sturdy "
        "durable solid premium beautiful gorgeous stylish fantastic superb crisp bright sharp "
        "fast smooth soft strong reliable impressive happy best brilliant lovely".split()
    )
    NEGATIVE = set(
        "bad poor terrible awful horrible hate hated worst cheap flimsy weak broke broken "
        "breaks tore torn frayed snapped fell slow dull dim blurry disappointing disappointed "
        "uncomfortable painful hurts loose ugly useless rubbish garbage cracked peeling dies "
        "died drains overheats laggy grainy faded".split()
    )
    NEGATORS = {"not", "no", "never", "isn't", "wasn't", "aren't", "don't", "doesn't", "didn't", "hardly"}

    def score(self, texts: Sequence[str]) -> list[float]:
        out = []
        for text in texts:
            tokens = re.findall(r"[a-z']+", text.lower())
            total = 0
            for i, tok in enumerate(tokens):
                polarity = 1 if tok in self.POSITIVE else -1 if tok in self.NEGATIVE else 0
                if polarity and any(t in self.NEGATORS for t in tokens[max(0, i - 3):i]):
                    polarity = -polarity
                total += polarity
            out.append(float(max(1, min(5, 3 + total * 1.5))))
        return out
