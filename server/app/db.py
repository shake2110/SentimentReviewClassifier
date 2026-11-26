from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app
from pymongo import ASCENDING, DESCENDING, MongoClient


def init_db(app):
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=3000, tz_aware=True)
    db = client[app.config["MONGO_DB"]]
    app.extensions["mongo_client"] = client
    app.extensions["db"] = db
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.products.create_index([("provider_id", ASCENDING)])
        db.products.create_index([("created_at", DESCENDING)])
        db.reviews.create_index([("product_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
        db.reviews.create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
    except Exception as exc:  # pragma: no cover - surfaced by /api/health instead
        app.logger.error("MongoDB is not reachable at %s (%s). Start it with scripts/start-mongo.sh",
                         app.config["MONGO_URI"], exc)


def get_db():
    return current_app.extensions["db"]


def oid(value):
    """Parse an ObjectId from a URL/body value; None if it is not a valid id."""
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None
