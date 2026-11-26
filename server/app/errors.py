from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400, fields: dict | None = None):
        super().__init__(message)
        self.message, self.status, self.fields = message, status, fields or {}


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _api_error(err):
        body = {"error": err.message}
        if err.fields:
            body["fields"] = err.fields
        return jsonify(body), err.status

    @app.errorhandler(404)
    def _not_found(_):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def _method(_):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def _too_large(_):
        return jsonify({"error": "Upload too large (max 8 MB)."}), 413

    @app.errorhandler(Exception)
    def _unhandled(err):
        if isinstance(err, HTTPException):
            return jsonify({"error": err.description or err.name}), err.code
        app.logger.exception("Unhandled error: %s", err)
        return jsonify({"error": "Something went wrong on the server."}), 500
