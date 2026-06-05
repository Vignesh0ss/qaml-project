"""
Environment-based configuration. Secrets via .env; never commit real secrets.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Force load dotenv so SECRET_KEY matches docker/run consistently
env_path = BASE_DIR.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def mongo_uri_with_timeouts(uri: str) -> str:
    """Append Atlas-friendly timeouts when missing (cold starts, free tier)."""
    if not uri or not uri.strip().startswith("mongodb"):
        return uri
    extra: List[str] = []
    if "connectTimeoutMS" not in uri:
        extra.append("connectTimeoutMS=30000")
    if "socketTimeoutMS" not in uri:
        extra.append("socketTimeoutMS=30000")
    if not extra:
        return uri
    sep = "&" if "?" in uri else "?"
    return uri + sep + "&".join(extra)


def parse_cors_origins(*, production: bool) -> Union[str, List[str], None]:
    """
    CORS_ORIGINS: comma-separated list, e.g. https://app.vercel.app,http://localhost:3000
    Production requires at least one origin (no wildcard).
    """
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return None if production else "*"
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return None if production else "*"
    return origins


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "jwt-secret"))
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    BCRYPT_LOG_ROUNDS = 12

    MONGODB_DB = os.environ.get("MONGODB_DB", "quantum_drug_repurposing")
    MONGO_URI = mongo_uri_with_timeouts(
        os.environ.get(
            "MONGO_URI",
            "mongodb://localhost:27017/quantum_drug_repurposing?serverSelectionTimeoutMS=2000",
        )
    )

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

    USE_CLOUD_QUANTUM = os.environ.get("USE_CLOUD_QUANTUM", "false").lower() == "true"
    DWAVE_API_TOKEN = os.environ.get("DWAVE_API_TOKEN", "")
    DWAVE_SOLVER = os.environ.get("DWAVE_SOLVER", "Advantage_system6.4")

    ML_MODEL_PATH = os.environ.get("ML_MODEL_PATH", str(BASE_DIR / "ml" / "artifacts" / "model.joblib"))
    MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "")
    EXTERNAL_AI_ENABLED = os.environ.get("EXTERNAL_AI_ENABLED", "true").lower() == "true"

    # Nvidia NIM – primary AI engine
    NVIDIA_NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
    NVIDIA_NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")
    EXPERIMENTAL_NVIDIA_NIM_API_KEY = os.environ.get("EXPERIMENTAL_NVIDIA_NIM_API_KEY", "")
    EXPERIMENTAL_NVIDIA_NIM_MODEL = os.environ.get("EXPERIMENTAL_NVIDIA_NIM_MODEL", NVIDIA_NIM_MODEL)
    ENABLE_ESM2 = False



class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    CORS_ALLOWED_ORIGINS = parse_cors_origins(production=False)


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CORS_ALLOWED_ORIGINS = parse_cors_origins(production=True)


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    EXTERNAL_AI_ENABLED = False
    CORS_ALLOWED_ORIGINS = "*"
    MONGO_URI = mongo_uri_with_timeouts(
        "mongodb://localhost:27017/quantum_drug_repurposing_test?serverSelectionTimeoutMS=2000"
    )
