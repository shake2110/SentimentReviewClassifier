import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError

from .auth import auth_required, optional_user
from .db import get_db, oid
from .errors import ApiError
from .service import aspect_summaries, overall_stats_by_product, reanalyze_product_reviews

bp = Blueprint("products", __name__)

ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MAX_ASPECTS = 20


# ------------------------------------------------------------------ helpers
def _now():
    return datetime.now(timezone.utc)


def _save_image(file_storage) -> dict:
    if file_storage is None or not file_storage.filename:
        raise ApiError("A product image is required.", 422, {"image": "Upload a JPG, PNG or WEBP image."})
    try:
        with Image.open(file_storage.stream) as img:
            fmt = img.format
            img.verify()
        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as img:
            width, height = img.size
    except (UnidentifiedImageError, OSError):
        raise ApiError("That file is not a valid image.", 422, {"image": "Upload a JPG, PNG or WEBP image."})
    if fmt not in ALLOWED_FORMATS:
        raise ApiError("Unsupported image type.", 422, {"image": "Upload a JPG, PNG or WEBP image."})

    upload_dir = current_app.config["UPLOAD_DIR"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ALLOWED_FORMATS[fmt]}"
    file_storage.stream.seek(0)
    file_storage.save(upload_dir / filename)
    return {"image": filename, "image_width": width, "image_height": height}


def _delete_image(filename):
    if filename:
        (current_app.config["UPLOAD_DIR"] / filename).unlink(missing_ok=True)


def _product_fields(form, partial=False) -> dict:
    out, fields = {}, {}
    if "name" in form or not partial:
        name = str(form.get("name", "")).strip()
        if not 1 <= len(name) <= 120:
            fields["name"] = "Enter a product name (up to 120 characters)."
        out["name"] = name
    if "description" in form or not partial:
        desc = str(form.get("description", "")).strip()
        if len(desc) > 4000:
            fields["description"] = "Description is too long (max 4000 characters)."
        out["description"] = desc
    if "category" in form or not partial:
        out["category"] = str(form.get("category", "")).strip()[:60]
    if "price" in form or not partial:
        raw = str(form.get("price", "")).strip()
        if raw:
            try:
                price = round(float(raw), 2)
                if price < 0:
                    raise ValueError
                out["price"] = price
            except ValueError:
                fields["price"] = "Price must be a positive number."
        else:
            out["price"] = None
    if fields:
        raise ApiError("Please fix the highlighted fields.", 422, fields)
    return out


def _owned_product(product_id):
    product = _get_product(product_id)
    if product["provider_id"] != g.user["_id"]:
        raise ApiError("You can only manage your own products.", 403)
    return product


def _get_product(product_id):
    _id = oid(product_id)
    product = get_db().products.find_one({"_id": _id}) if _id else None
    if not product:
        raise ApiError("Product not found.", 404)
    return product


def serialize_product(product, stats=None, detail=False):
    data = {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product.get("description", ""),
        "category": product.get("category", ""),
        "price": product.get("price"),
        "image_url": f"/uploads/{product['image']}",
        "image_width": product.get("image_width"),
        "image_height": product.get("image_height"),
        "provider": {"id": str(product["provider_id"]), "name": product.get("provider_name", "")},
        "aspect_count": len(product.get("aspects", [])),
        "created_at": product["created_at"].isoformat(),
    }
    if detail:
        aspects, overall = aspect_summaries(product)
        data["aspects"] = aspects
        data["overall"] = overall
    else:
        data["overall"] = stats or {"count": 0, "avg_stars": None}
    return data


def _validate_aspects(raw) -> list[dict]:
    if not isinstance(raw, list):
        raise ApiError("`aspects` must be a list.", 422)
    if len(raw) > MAX_ASPECTS:
        raise ApiError(f"A product can have at most {MAX_ASPECTS} marked parts.", 422)
    cleaned, seen = [], set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ApiError(f"Part #{i + 1} is malformed.", 422)
        name = str(item.get("name", "")).strip()
        if not 1 <= len(name) <= 40:
            raise ApiError(f"Part #{i + 1} needs a name (up to 40 characters).", 422)
        if name.lower() in seen:
            raise ApiError(f'Two parts are both called "{name}". Part names must be unique.', 422)
        seen.add(name.lower())
        try:
            x, y = float(item.get("x")), float(item.get("y"))
        except (TypeError, ValueError):
            raise ApiError(f'Part "{name}" has no position on the image.', 422)
        if not (0 <= x <= 100 and 0 <= y <= 100):
            raise ApiError(f'Part "{name}" is positioned outside the image.', 422)
        keywords = item.get("keywords") or []
        if isinstance(keywords, str):
            keywords = keywords.split(",")
        keywords = list(dict.fromkeys(k.strip() for k in keywords if str(k).strip()))
        if len(keywords) > 15 or any(len(k) > 40 for k in keywords):
            raise ApiError(f'Part "{name}": at most 15 keywords of up to 40 characters.', 422)
        aspect_id = str(item.get("id") or "").strip() or uuid.uuid4().hex[:10]
        cleaned.append({"id": aspect_id[:32], "name": name, "keywords": keywords,
                        "x": round(x, 2), "y": round(y, 2)})
    return cleaned


# ------------------------------------------------------------------- routes
@bp.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename, max_age=86400)


@bp.get("/api/products")
def list_products():
    query = {}
    q = request.args.get("q", "").strip()
    if q:
        import re
        query["$or"] = [{"name": {"$regex": re.escape(q), "$options": "i"}},
                        {"category": {"$regex": re.escape(q), "$options": "i"}}]
    category = request.args.get("category", "").strip()
    if category:
        import re
        query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}
    if request.args.get("mine") == "1":
        user = optional_user()
        if not user:
            raise ApiError("Please log in to continue.", 401)
        query["provider_id"] = user["_id"]
    products = list(get_db().products.find(query).sort("created_at", -1).limit(200))
    stats = overall_stats_by_product([p["_id"] for p in products])
    return jsonify({"products": [serialize_product(p, stats.get(p["_id"])) for p in products]})


@bp.get("/api/categories")
def list_categories():
    rows = get_db().products.aggregate([
        {"$match": {"category": {"$nin": ["", None]}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ])
    return jsonify({"categories": [{"name": r["_id"], "count": r["count"]} for r in rows]})


@bp.get("/api/products/<product_id>")
def get_product(product_id):
    product = _get_product(product_id)
    data = serialize_product(product, detail=True)
    user = optional_user()
    data["viewer"] = {
        "is_owner": bool(user and user["_id"] == product["provider_id"]),
        "can_review": bool(user and user["role"] == "consumer"),
        "my_review_id": None,
    }
    if user:
        mine = get_db().reviews.find_one({"product_id": product["_id"], "user_id": user["_id"]}, {"_id": 1})
        data["viewer"]["my_review_id"] = str(mine["_id"]) if mine else None
    return jsonify({"product": data})


@bp.post("/api/products")
@auth_required("provider")
def create_product():
    fields = _product_fields(request.form)
    image = _save_image(request.files.get("image"))
    now = _now()
    product = {**fields, **image, "aspects": [], "provider_id": g.user["_id"],
               "provider_name": g.user["name"], "created_at": now, "updated_at": now}
    product["_id"] = get_db().products.insert_one(product).inserted_id
    return jsonify({"product": serialize_product(product, detail=True)}), 201


@bp.patch("/api/products/<product_id>")
@auth_required("provider")
def update_product(product_id):
    product = _owned_product(product_id)
    updates = _product_fields(request.form, partial=True)
    old_image = None
    if request.files.get("image"):
        updates.update(_save_image(request.files["image"]))
        old_image = product["image"]
    updates["updated_at"] = _now()
    get_db().products.update_one({"_id": product["_id"]}, {"$set": updates})
    _delete_image(old_image)
    product.update(updates)
    return jsonify({"product": serialize_product(product, detail=True)})


@bp.delete("/api/products/<product_id>")
@auth_required("provider")
def delete_product(product_id):
    product = _owned_product(product_id)
    db = get_db()
    db.reviews.delete_many({"product_id": product["_id"]})
    db.products.delete_one({"_id": product["_id"]})
    _delete_image(product.get("image"))
    return jsonify({"deleted": True})


@bp.put("/api/products/<product_id>/aspects")
@auth_required("provider")
def set_aspects(product_id):
    product = _owned_product(product_id)
    aspects = _validate_aspects((request.get_json(silent=True) or {}).get("aspects"))
    get_db().products.update_one({"_id": product["_id"]},
                                 {"$set": {"aspects": aspects, "updated_at": _now()}})
    product["aspects"] = aspects
    reanalyzed = reanalyze_product_reviews(product)
    return jsonify({"product": serialize_product(product, detail=True), "reanalyzed_reviews": reanalyzed})
