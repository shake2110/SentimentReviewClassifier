"""Review analysis + aggregation shared by the products and reviews APIs."""
from __future__ import annotations

from datetime import datetime, timezone

from .db import get_db
from .nlp import get_analyzer, label_for


def analyze(text: str, aspects: list[dict]) -> dict:
    return get_analyzer().analyze(text, aspects)


def reanalyze_product_reviews(product: dict) -> int:
    """Re-run analysis for every review after a seller changes the part list."""
    db = get_db()
    count = 0
    for review in db.reviews.find({"product_id": product["_id"]}, {"text": 1}):
        result = analyze(review["text"], product.get("aspects", []))
        db.reviews.update_one({"_id": review["_id"]}, {"$set": {
            "overall": result["overall"],
            "mentions": result["mentions"],
            "general": result["general"],
            "analyzed_at": datetime.now(timezone.utc),
        }})
        count += 1
    return count


def _summary(stars: list[float], labels: list[str]) -> dict:
    n = len(stars)
    avg = round(sum(stars) / n, 2) if n else None
    return {
        "count": n,
        "avg_stars": avg,
        "label": label_for(avg) if avg is not None else None,
        "positive": labels.count("positive"),
        "neutral": labels.count("neutral"),
        "negative": labels.count("negative"),
    }


def aspect_summaries(product: dict, snippet_limit: int = 100) -> tuple[list[dict], dict]:
    """Per-part star summaries + snippets, and the overall summary."""
    reviews = list(get_db().reviews.find(
        {"product_id": product["_id"]},
        {"user_name": 1, "overall": 1, "mentions": 1, "created_at": 1},
    ).sort("created_at", -1))

    buckets = {a["id"]: {"stars": [], "labels": [], "snippets": []} for a in product.get("aspects", [])}
    for review in reviews:
        for mention in review.get("mentions", []):
            bucket = buckets.get(mention["aspect_id"])
            if bucket is None:
                continue
            bucket["stars"].append(mention["stars"])
            bucket["labels"].append(mention["label"])
            if len(bucket["snippets"]) < snippet_limit:
                bucket["snippets"].append({
                    "review_id": str(review["_id"]),
                    "user_name": review.get("user_name", "Anonymous"),
                    "text": mention["snippet"],
                    "stars": mention["stars"],
                    "label": mention["label"],
                    "created_at": review["created_at"].isoformat(),
                })

    aspects = []
    for aspect in product.get("aspects", []):
        b = buckets[aspect["id"]]
        aspects.append({**aspect, "summary": _summary(b["stars"], b["labels"]), "snippets": b["snippets"]})

    overall = _summary([r["overall"]["stars"] for r in reviews if r.get("overall")],
                       [r["overall"]["label"] for r in reviews if r.get("overall")])
    return aspects, overall


def overall_stats_by_product(product_ids: list) -> dict:
    pipeline = [
        {"$match": {"product_id": {"$in": product_ids}}},
        {"$group": {"_id": "$product_id", "count": {"$sum": 1}, "avg": {"$avg": "$overall.stars"}}},
    ]
    return {row["_id"]: {"count": row["count"], "avg_stars": round(row["avg"], 2) if row["avg"] else None}
            for row in get_db().reviews.aggregate(pipeline)}
