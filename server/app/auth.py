import re
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import Blueprint, current_app, g, jsonify, request
from pymongo.errors import DuplicateKeyError

from .db import get_db, oid
from .errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLES = ("consumer", "provider")


def public_user(user: dict) -> dict:
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user["role"]}


def issue_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["_id"]),
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def _user_from_request():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(header[7:], current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError("Your session has expired. Please log in again.", 401)
    except jwt.InvalidTokenError:
        raise ApiError("Invalid authentication token.", 401)
    user_id = oid(payload.get("sub"))
    user = get_db().users.find_one({"_id": user_id}) if user_id else None
    if not user:
        raise ApiError("Account no longer exists.", 401)
    return user


def optional_user():
    """Current user or None, without failing on a missing token."""
    if not hasattr(g, "user"):
        try:
            g.user = _user_from_request()
        except ApiError:
            g.user = None
    return g.user


def auth_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _user_from_request()
            if user is None:
                raise ApiError("Please log in to continue.", 401)
            if roles and user["role"] not in roles:
                raise ApiError(f"This action is only available to {' / '.join(roles)} accounts.", 403)
            g.user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "consumer"))

    fields = {}
    if not 1 <= len(name) <= 80:
        fields["name"] = "Enter your name (up to 80 characters)."
    if not EMAIL_RE.match(email):
        fields["email"] = "Enter a valid email address."
    if len(password) < 8:
        fields["password"] = "Password must be at least 8 characters."
    if len(password.encode()) > 72:
        fields["password"] = "Password must be at most 72 bytes."
    if role not in ROLES:
        fields["role"] = "Choose consumer or provider."
    if fields:
        raise ApiError("Please fix the highlighted fields.", 422, fields)

    user = {
        "name": name,
        "email": email,
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "role": role,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        user["_id"] = get_db().users.insert_one(user).inserted_id
    except DuplicateKeyError:
        raise ApiError("An account with this email already exists.", 409, {"email": "Already registered."})
    return jsonify({"token": issue_token(user), "user": public_user(user)}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = get_db().users.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode()[:72], user["password_hash"].encode()):
        raise ApiError("Incorrect email or password.", 401)
    return jsonify({"token": issue_token(user), "user": public_user(user)})


@bp.get("/me")
@auth_required()
def me():
    return jsonify({"user": public_user(g.user)})
