"""
Quantum-Assisted ML Framework for Drug Repurposing — Flask Application Factory.
"""
from flask import Flask
from flask_cors import CORS


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_from_name(config_name))
    CORS(
        app,
        resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization"]}},
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
