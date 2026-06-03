"""
Quantum-Assisted ML Framework for Drug Repurposing — Flask Application Factory.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Union

from flask import Flask
from flask_cors import CORS

_DEV_SECRET_SENTINEL = "dev-secret-change-in-production"


def _require_production_secrets(app: Flask) -> None:
    """Fail fast on Render/production if required env vars are missing or left at dev defaults."""
    sk = app.config.get("SECRET_KEY") or ""
    jwt_sk = app.config.get("JWT_SECRET_KEY") or ""
    mongo = app.config.get("MONGO_URI") or ""
    issues = []
    if not sk.strip() or sk == _DEV_SECRET_SENTINEL:
        issues.append("SECRET_KEY must be set to a strong random value")
    if not jwt_sk.strip():
        issues.append("JWT_SECRET_KEY must be set (or rely on SECRET_KEY by setting both explicitly)")
    if not mongo.strip():
        issues.append("MONGO_URI must be set (e.g. MongoDB Atlas connection string)")
    cors = app.config.get("CORS_ALLOWED_ORIGINS")
    if cors is None or cors == "*" or (isinstance(cors, list) and "*" in cors):
        issues.append(
            "CORS_ORIGINS must list allowed frontend origin(s) (comma-separated), e.g. "
            "https://your-app.vercel.app — wildcards are not allowed in production"
        )
    elif isinstance(cors, list) and len(cors) == 0:
        issues.append("CORS_ORIGINS must include at least one origin")
    if issues:
        raise RuntimeError("Production configuration: " + "; ".join(issues))


def create_app(config_name: Optional[str] = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    config_cls = config_from_name(config_name)
    app.config.from_object(config_cls)
    if config_cls.__name__ == "ProductionConfig":
        _require_production_secrets(app)

    if not app.config.get("DEBUG", False):
        logging.basicConfig(level=logging.INFO, force=True)

    cors_origins: Union[str, List[str]] = app.config.get("CORS_ALLOWED_ORIGINS", "*")
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    from app.extensions import init_extensions
    init_extensions(app)

    from app.api.v1 import register_blueprints
    register_blueprints(app)

    @app.route("/api/v1/health")
    def health():
        return {"status": "ok", "service": "quantum-drug-repurposing"}, 200

    return app


def config_from_name(name: str):
    from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
    return {"development": DevelopmentConfig, "production": ProductionConfig, "testing": TestingConfig}.get(
        name, DevelopmentConfig
    )
