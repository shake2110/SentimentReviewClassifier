from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from pymongo.errors import DuplicateKeyError

from .auth import auth_required
from .db import get_db, oid
from .errors import ApiError
from .products import _get_product
from .service import analyze

bp = Blueprint("reviews", __name__)
MIN_LEN, MAX_LEN = 10, 3000


def _clean_text(data) -> str:
    text = " ".join(str((data or {}).get("text", "")).split())
    if not MIN_LEN <= len(text) <= MAX_LEN:
        raise ApiError(f"Reviews must be between {MIN_LEN} and {MAX_LEN} characters.", 422,
                       {"text": f"Write at least {MIN_LEN} characters."})
    return text


def serialize_review(review: dict) -> dict:
    return {
        "id": str(review["_id"]),
        "product_id": str(review["product_id"]),
        "user": {"id": str(review["user_id"]), "name": review.get("user_name", "")},
        "text": review["text"],
        "overall": review.get("overall"),
        "mentions": review.get("mentions", []),
        "general": review.get("general", []),
        "created_at": review["created_at"].isoformat(),
        "updated_at": review.get("updated_at", review["created_at"]).isoformat(),
    }


def _own_review(review_id):
    _id = oid(review_id)
    review = get_db().reviews.find_one({"_id": _id}) if _id else None
    if not review:
        raise ApiError("Review not found.", 404)
    if review["user_id"] != g.user["_id"]:
        raise ApiError("You can only change your own review.", 403)
    return review


@bp.get("/api/products/<product_id>/reviews")
def list_reviews(product_id):
    product = _get_product(product_id)
    reviews = get_db().reviews.find({"product_id": product["_id"]}).sort("created_at", -1).limit(500)
    return jsonify({"reviews": [serialize_review(r) for r in reviews]})


@bp.post("/api/products/<product_id>/analyze")
@auth_required()
def preview(product_id):
    """Show how a draft review would be split, without saving it."""
    product = _get_product(product_id)
    return jsonify({"analysis": analyze(_clean_text(request.get_json(silent=True)),
                                        product.get("aspects", []))})


@bp.post("/api/products/<product_id>/reviews")
@auth_required("consumer")
def create_review(product_id):
    product = _get_product(product_id)
    text = _clean_text(request.get_json(silent=True))
    result = analyze(text, product.get("aspects", []))
    now = datetime.now(timezone.utc)
    review = {
        "product_id": product["_id"],
        "user_id": g.user["_id"],
        "user_name": g.user["name"],
        "text": text,
        **result,
        "created_at": now,
        "updated_at": now,
        "analyzed_at": now,
    }
    try:
        review["_id"] = get_db().reviews.insert_one(review).inserted_id
    except DuplicateKeyError:
        raise ApiError("You have already reviewed this product. Edit your existing review instead.", 409)
    return jsonify({"review": serialize_review(review)}), 201


@bp.put("/api/reviews/<review_id>")
@auth_required("consumer")
def update_review(review_id):
    review = _own_review(review_id)
    product = _get_product(review["product_id"])
    text = _clean_text(request.get_json(silent=True))
    now = datetime.now(timezone.utc)
    updates = {"text": text, **analyze(text, product.get("aspects", [])),
               "updated_at": now, "analyzed_at": now}
    get_db().reviews.update_one({"_id": review["_id"]}, {"$set": updates})
    review.update(updates)
    return jsonify({"review": serialize_review(review)})


@bp.delete("/api/reviews/<review_id>")
@auth_required("consumer")
def delete_review(review_id):
    review = _own_review(review_id)
    get_db().reviews.delete_one({"_id": review["_id"]})
    return jsonify({"deleted": True})
