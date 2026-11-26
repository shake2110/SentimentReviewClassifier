import io
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("JWT_SECRET", "test-secret-" + "x" * 32)
os.environ["WARM_MODELS"] = "0"

from PIL import Image  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app import create_app  # noqa: E402
from app.nlp import build_analyzer, set_analyzer  # noqa: E402

TEST_DB = "aspectlens_test"


@pytest.fixture(scope="session", autouse=True)
def _mongo_available():
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    try:
        MongoClient(uri, serverSelectionTimeoutMS=1500).admin.command("ping")
    except Exception:
        pytest.skip("MongoDB is not running (scripts/start-mongo.sh)", allow_module_level=True)


@pytest.fixture()
def app(tmp_path):
    set_analyzer(build_analyzer("lite"))
    application = create_app({"MONGO_DB": TEST_DB, "UPLOAD_DIR": tmp_path / "uploads", "TESTING": True})
    yield application
    application.extensions["mongo_client"].drop_database(TEST_DB)
    set_analyzer(None)


@pytest.fixture()
def client(app):
    return app.test_client()


def png_bytes(w=400, h=300):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 120, 80)).save(buf, "PNG")
    buf.seek(0)
    return buf


@pytest.fixture()
def register(client):
    def _register(role="consumer", email=None, name=None):
        email = email or f"{role}{os.urandom(3).hex()}@example.com"
        res = client.post("/api/auth/register", json={
            "name": name or role.title(), "email": email, "password": "password123", "role": role})
        assert res.status_code == 201, res.get_json()
        body = res.get_json()
        return {"Authorization": f"Bearer {body['token']}"}, body["user"]
    return _register


@pytest.fixture()
def shoe(client, register):
    """A provider-owned shoe product with Leather / Lace / Sole parts."""
    headers, _ = register("provider")
    res = client.post("/api/products", headers=headers, content_type="multipart/form-data",
                      data={"name": "Trail Runner", "description": "A shoe", "category": "Footwear",
                            "price": "89.99", "image": (png_bytes(), "shoe.png")})
    assert res.status_code == 201, res.get_json()
    product = res.get_json()["product"]
    res = client.put(f"/api/products/{product['id']}/aspects", headers=headers, json={"aspects": [
        {"name": "Leather", "x": 40, "y": 40},
        {"name": "Lace", "x": 55, "y": 25, "keywords": ["strings"]},
        {"name": "Sole", "x": 50, "y": 90},
    ]})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["product"], headers
