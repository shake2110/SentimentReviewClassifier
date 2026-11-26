"""Review -> per-part sentiment.

    analyzer = ReviewAnalyzer(embedder, scorer)
    result = analyzer.analyze("The leather is great but the laces frayed", aspects)

Clause assembly rules (applied after the matcher has tagged fragments):

* A fragment that only *names* parts ("The camera" in "The camera and screen
  are both bad") is merged forward into the next fragment, so both parts get
  the shared opinion.
* A fragment that names no part ("durable" in "the sole is sturdy, durable and
  grippy") is merged back into the previous fragment of the same segment.
  Leading part-less fragments stay general ("Great shoes, ...").
* A segment/sentence that names no part but starts with a pronoun ("It snapped
  after a week") is attributed to the most recently mentioned parts.
* Anything else is general commentary: it still counts toward the overall
  rating, but is not pinned to a part.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .matcher import AspectMatcher, Embedder, MatchInfo
from .sentiment import SentimentScorer, label_for
from .text import Fragment, snippet, split_review


@dataclass
class Clause:
    text: str
    aspect_ids: list[str]
    matches: dict[str, MatchInfo] = field(default_factory=dict)
    inherited: bool = False  # attributed via a pronoun


def _join(a: str, b: str) -> str:
    return f"{a} {b}".strip() if a else b


def _merge(a: Fragment, b: Fragment) -> Fragment:
    """Merge two adjacent fragments (a precedes b in the review)."""
    merged = Fragment(_join(a.text, b.text), a.tokens + b.tokens, a.start, b.end)
    merged.matches = {**b.matches, **a.matches}
    offset = len(a.tokens)
    merged.aspect_token_idx = set(a.aspect_token_idx) | {i + offset for i in b.aspect_token_idx}
    return merged


def assemble_clauses(sentences: list[list[list[Fragment]]], source: str = "") -> list[Clause]:
    clauses: list[Clause] = []

    def text_of(frag: Fragment) -> str:
        # Re-read merged spans from the original review so joiners ("and", ",")
        # survive: "The leather and the laces both feel cheap".
        return snippet(source, frag.start, frag.end) if source else frag.text
    last_aspects: list[str] = []

    for segments in sentences:
        for fragments in segments:
            # 1. merge "name-only" fragments forward
            forward: list[Fragment] = []
            pending: Fragment | None = None
            for frag in fragments:
                if pending is not None:
                    frag = _merge(pending, frag)
                    pending = None
                if frag.matches and not frag.has_opinion_content:
                    pending = frag
                    continue
                forward.append(frag)
            if pending is not None:
                if forward:
                    forward[-1] = _merge(forward[-1], pending)
                else:
                    forward.append(pending)

            # 2. merge part-less fragments back into the previous one
            grouped: list[Fragment] = []
            for frag in forward:
                if not frag.matches and grouped and grouped[-1].matches:
                    grouped[-1] = _merge(grouped[-1], frag)
                else:
                    grouped.append(frag)

            # 3. turn into clauses, resolving pronoun-led general fragments
            for idx, frag in enumerate(grouped):
                if frag.matches:
                    ids = list(frag.matches)
                    clauses.append(Clause(text_of(frag), ids, dict(frag.matches)))
                    last_aspects = ids
                elif idx == 0 and frag.starts_with_pronoun and last_aspects:
                    clauses.append(Clause(text_of(frag), list(last_aspects), inherited=True))
                else:
                    clauses.append(Clause(text_of(frag), []))
    return clauses


class ReviewAnalyzer:
    def __init__(self, embedder: Embedder | None, scorer: SentimentScorer,
                 threshold: float | None = None):
        self.embedder = embedder
        self.scorer = scorer
        self.threshold = threshold

    def matcher_for(self, aspects: list[dict]) -> AspectMatcher:
        return AspectMatcher(aspects, self.embedder, self.threshold)

    def analyze(self, text: str, aspects: list[dict]) -> dict:
        text = (text or "").strip()
        matcher = self.matcher_for(aspects)
        sentences = split_review(text)
        matcher.annotate([f for sent in sentences for seg in sent for f in seg])
        clauses = assemble_clauses(sentences, text)

        scores = self.scorer.score([text] + [c.text for c in clauses]) if text else [3.0]
        overall_stars, clause_scores = scores[0], scores[1:]

        per_aspect: dict[str, dict] = {}
        general = []
        for clause, stars in zip(clauses, clause_scores):
            if not clause.aspect_ids:
                general.append({"snippet": clause.text, "stars": stars, "label": label_for(stars)})
                continue
            for aid in clause.aspect_ids:
                entry = per_aspect.setdefault(aid, {"snippets": [], "stars": [], "evidence": []})
                entry["snippets"].append(clause.text)
                entry["stars"].append(stars)
                info = clause.matches.get(aid)
                if info is not None:
                    entry["evidence"].append({"method": info.method, "term": info.term,
                                              "score": info.score})
                elif clause.inherited:
                    entry["evidence"].append({"method": "pronoun", "term": clause.text.split()[0],
                                              "score": None})

        mentions = []
        for aspect in aspects:  # keep the seller's ordering
            entry = per_aspect.get(aspect["id"])
            if not entry:
                continue
            stars = round(sum(entry["stars"]) / len(entry["stars"]), 2)
            mentions.append({
                "aspect_id": aspect["id"],
                "aspect_name": aspect["name"],
                "snippet": " … ".join(dict.fromkeys(entry["snippets"])),
                "stars": stars,
                "label": label_for(stars),
                "evidence": entry["evidence"],
            })

        return {
            "overall": {"stars": overall_stars, "label": label_for(overall_stars)},
            "mentions": mentions,
            "general": general,
        }
