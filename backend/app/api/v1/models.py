"""
GET /api/v1/models — List trained model versions.
"""
from flask import Blueprint, jsonify
import os
from app.config import Config

bp = Blueprint("models", __name__)


@bp.route("/models", methods=["GET"])
def list_models():
    model_path = getattr(Config, "ML_MODEL_PATH", "")
    versions = []
    if model_path and os.path.isfile(model_path):
        versions.append({"path": model_path, "active": True})
    return jsonify({"models": versions}), 200
