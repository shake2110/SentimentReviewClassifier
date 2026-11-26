"""Aspect-based sentiment analysis engine.

`get_analyzer()` returns a process-wide ReviewAnalyzer. Mode is chosen by the
NLP_MODE environment variable:

* "full" (default) - sentence-transformer matching + BERT star model
* "lite"           - keyword matching + lexicon sentiment, no model downloads
"""
from __future__ import annotations

import logging
import os
import threading

from .pipeline import ReviewAnalyzer
from .sentiment import LexiconScorer, label_for

log = logging.getLogger(__name__)
_lock = threading.Lock()
_analyzer: ReviewAnalyzer | None = None


def build_analyzer(mode: str | None = None) -> ReviewAnalyzer:
    mode = (mode or os.getenv("NLP_MODE", "full")).lower()
    if mode == "lite":
        log.info("NLP_MODE=lite: keyword matching + lexicon sentiment")
        return ReviewAnalyzer(None, LexiconScorer())
    from .embeddings import SentenceEmbedder
    from .sentiment import StarModelScorer

    log.info("Loading sentiment + embedding models (first run downloads ~800MB)...")
    analyzer = ReviewAnalyzer(SentenceEmbedder(), StarModelScorer())
    log.info("Models loaded.")
    return analyzer


def get_analyzer() -> ReviewAnalyzer:
    global _analyzer
    if _analyzer is None:
        with _lock:
            if _analyzer is None:
                _analyzer = build_analyzer()
    return _analyzer


def set_analyzer(analyzer: ReviewAnalyzer | None) -> None:
    """Override the shared analyzer (used by tests)."""
    global _analyzer
    _analyzer = analyzer


__all__ = ["ReviewAnalyzer", "build_analyzer", "get_analyzer", "set_analyzer", "label_for"]
