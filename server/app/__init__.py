import logging
import threading

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config


def create_app(overrides: dict | None = None) -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    Config.validate()
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)
    app.json.sort_keys = False

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from . import auth, products, reviews
    from .db import init_db
    from .errors import register_error_handlers
    from .nlp import get_analyzer

    init_db(app)
    register_error_handlers(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(reviews.bp)

    nlp_state = {"status": "not loaded"}

    def warm():
        nlp_state["status"] = "loading"
        try:
            get_analyzer()
            nlp_state["status"] = "ready"
        except Exception as exc:  # pragma: no cover
            nlp_state["status"] = f"error: {exc}"
            app.logger.exception("Could not load NLP models")

    if app.config["WARM_MODELS"]:
        threading.Thread(target=warm, daemon=True).start()

    @app.get("/api/health")
    def health():
        try:
            app.extensions["mongo_client"].admin.command("ping")
            db_status = "ok"
        except Exception:
            db_status = "unreachable - run scripts/start-mongo.sh"
        return jsonify({"status": "ok", "database": db_status, "nlp": nlp_state["status"]})

    return app
