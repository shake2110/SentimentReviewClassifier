"""Map review fragments to the product parts a seller marked on the image.

Two signals, in order of trust:

1. Lexical - the part name or one of the seller's keywords appears in the
   fragment (with plural handling and compound suffixes, so "shoelaces"
   matches "lace").
2. Semantic - a sentence-transformer embedding of a word / two-word phrase
   in the fragment is close to the part name or a keyword ("traction" ->
   "sole", "selfies" -> "camera"). Only used when an embedder is available.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .sentiment import LexiconScorer
from .text import GENERIC_WORDS, STOPWORDS, Fragment, normalize, tokenize

# Opinion words describe a part, they never name one ("comfortable" must not
# be matched to an "Insole" part just because it is close to "cushioning").
OPINION_WORDS = frozenset(LexiconScorer.POSITIVE | LexiconScorer.NEGATIVE | {
    "okay", "ok", "fine", "decent", "average", "roomy", "tight", "thin", "thick",
    "heavy", "light", "lightweight", "stunning", "grainy", "dim", "slow", "quick",
    "sturdy", "supportive", "stiff", "loose", "fits", "fit", "feel", "feels", "felt",
    "look", "looks", "looked", "works", "worked", "lasts", "lasted", "week", "weeks",
    "day", "days", "month", "months", "year", "years", "time", "super", "absolutely",
})


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]):  # -> np.ndarray (n, d), L2-normalised
        ...


@dataclass
class MatchInfo:
    method: str  # "keyword" | "semantic"
    score: float  # 1.0 for keyword matches, cosine similarity otherwise
    term: str  # what in the review triggered it


@dataclass
class _Aspect:
    id: str
    name: str
    single_terms: set[str]  # normalised one-word terms
    phrases: list[list[str]]  # normalised multi-word terms
    embed_terms: list[str]  # raw terms used for semantic matching


class AspectMatcher:
    # Cosine similarity needed for a semantic match. Measured on all-MiniLM-L6-v2:
    # traction/sole 0.59, photos/camera 0.70, charging/battery 0.59,
    # screen/display 0.65 pass; comfortable/lace 0.37, good/sole 0.26 and
    # design/"build quality" 0.47 do not. Near-misses such as grip/sole (0.49)
    # are what seller keywords are for.
    DEFAULT_THRESHOLD = 0.5
    # A semantic match must beat the runner-up part by this margin, so one word
    # is not smeared over several similar parts.
    AMBIGUITY_MARGIN = 0.05
    # In a fragment that already names a *different* part by keyword, a word
    # must be much closer to claim a second part: "The microphone picks up
    # background noise" should not also rate "Sound" (noise/audio = 0.68).
    STRICT_THRESHOLD = 0.75

    def __init__(self, aspects: list[dict], embedder: Embedder | None = None,
                 threshold: float | None = None):
        self.embedder = embedder
        self.threshold = self.DEFAULT_THRESHOLD if threshold is None else threshold
        self.aspects = [self._prepare(a) for a in aspects]
        self._term_vectors = None  # lazily computed: (matrix, owner_index list)
        self._cache: dict[str, object] = {}

    @staticmethod
    def _prepare(aspect: dict) -> _Aspect:
        terms = [aspect["name"], *aspect.get("keywords", [])]
        single, phrases, embed_terms = set(), [], []
        for term in terms:
            toks = [normalize(t) for t in tokenize(term)]
            if not toks:
                continue
            embed_terms.append(" ".join(tokenize(term)))
            if len(toks) == 1:
                single.add(toks[0])
            else:
                phrases.append(toks)
        return _Aspect(aspect["id"], aspect["name"], single, phrases, embed_terms)

    # ------------------------------------------------------------------ lexical
    def _match_lexical(self, frag: Fragment) -> None:
        norm = [normalize(t) for t in frag.tokens]
        exact_owners: dict[int, set[str]] = {}

        # pass 1: exact single words and full phrases
        for asp in self.aspects:
            for i, tok in enumerate(norm):
                if tok in asp.single_terms:
                    exact_owners.setdefault(i, set()).add(asp.id)
                    self._record(frag, asp, {i}, MatchInfo("keyword", 1.0, frag.tokens[i]))
            for phrase in asp.phrases:
                n = len(phrase)
                for i in range(len(norm) - n + 1):
                    if norm[i:i + n] == phrase:
                        span = set(range(i, i + n))
                        self._record(frag, asp, span,
                                     MatchInfo("keyword", 1.0, " ".join(frag.tokens[i:i + n])))

        # pass 2: compound suffixes ("shoelaces" -> "lace"), but never steal a
        # token that is an exact match for another part ("insole" vs "sole").
        for asp in self.aspects:
            for i, tok in enumerate(norm):
                if i in exact_owners:
                    continue
                for term in asp.single_terms:
                    if len(term) >= 4 and len(tok) > len(term) and tok.endswith(term):
                        self._record(frag, asp, {i}, MatchInfo("keyword", 0.9, frag.tokens[i]))

    # ----------------------------------------------------------------- semantic
    def _vectors(self, texts: list[str]):
        missing = [t for t in texts if t not in self._cache]
        if missing:
            for t, v in zip(missing, self.embedder.encode(missing)):
                self._cache[t] = v
        import numpy as np
        return np.stack([self._cache[t] for t in texts])

    def _match_semantic(self, frags: list[Fragment]) -> None:
        if self.embedder is None or not self.aspects:
            return
        import numpy as np

        if self._term_vectors is None:
            owners, terms = [], []
            for idx, asp in enumerate(self.aspects):
                for t in asp.embed_terms:
                    owners.append(idx)
                    terms.append(t)
            self._term_vectors = (self._vectors(terms), owners)
        term_matrix, owners = self._term_vectors

        # candidate n-grams: content words not already claimed by a keyword match
        candidates: list[tuple[Fragment, set[int], str]] = []
        for frag in frags:
            toks = frag.tokens
            ok = [
                i not in frag.aspect_token_idx and t not in STOPWORDS
                and t not in GENERIC_WORDS and t not in OPINION_WORDS
                and len(t) > 2 and not t.isdigit()
                for i, t in enumerate(toks)
            ]
            for i, t in enumerate(toks):
                if ok[i]:
                    candidates.append((frag, {i}, t))
                if i + 1 < len(toks) and ok[i] and ok[i + 1]:
                    candidates.append((frag, {i, i + 1}, f"{t} {toks[i + 1]}"))
        if not candidates:
            return

        sims = self._vectors([c[2] for c in candidates]) @ term_matrix.T  # (n_cand, n_terms)
        n_aspects = len(self.aspects)
        for (frag, span, phrase), row in zip(candidates, sims):
            per_aspect = np.full(n_aspects, -1.0)
            for col, owner in enumerate(owners):
                per_aspect[owner] = max(per_aspect[owner], row[col])
            order = np.argsort(per_aspect)[::-1]
            best = order[0]
            best_score = float(per_aspect[best])
            runner_up = float(per_aspect[order[1]]) if n_aspects > 1 else -1.0
            if best_score < self.threshold or best_score - runner_up < self.AMBIGUITY_MARGIN:
                continue
            asp = self.aspects[best]
            keyword_parts = {aid for aid, m in frag.matches.items() if m.method == "keyword"}
            if keyword_parts - {asp.id} and best_score < self.STRICT_THRESHOLD:
                continue
            existing = frag.matches.get(asp.id)
            if existing is None or (existing.method == "semantic" and existing.score < best_score):
                self._record(frag, asp, span, MatchInfo("semantic", round(best_score, 3), phrase))

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _record(frag: Fragment, asp: _Aspect, span: set[int], info: MatchInfo) -> None:
        current = frag.matches.get(asp.id)
        if current is None or info.score > current.score:
            frag.matches[asp.id] = info
        frag.aspect_token_idx |= span

    def annotate(self, frags: list[Fragment]) -> None:
        """Fill `matches` / `aspect_token_idx` on every fragment in place."""
        for frag in frags:
            self._match_lexical(frag)
        self._match_semantic(frags)

    def name_of(self, aspect_id: str) -> str:
        for a in self.aspects:
            if a.id == aspect_id:
                return a.name
        return aspect_id
