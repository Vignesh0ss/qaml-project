"""
Environment-based configuration. Secrets via .env; never commit real secrets.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Force load dotenv so SECRET_KEY matches docker/run consistently
env_path = BASE_DIR.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "jwt-secret"))
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    BCRYPT_LOG_ROUNDS = 12

    MONGODB_DB = os.environ.get("MONGODB_DB", "quantum_drug_repurposing")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/quantum_drug_repurposing?serverSelectionTimeoutMS=2000")

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
    NVIDIA_NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-405b-instruct")
    EXPERIMENTAL_NVIDIA_NIM_API_KEY = os.environ.get("EXPERIMENTAL_NVIDIA_NIM_API_KEY", "")
    EXPERIMENTAL_NVIDIA_NIM_MODEL = os.environ.get("EXPERIMENTAL_NVIDIA_NIM_MODEL", NVIDIA_NIM_MODEL)
    ENABLE_ESM2 = os.environ.get("ENABLE_ESM2", "true").lower() == "true"
    NVIDIA_ESM2_ENDPOINT = os.environ.get("NVIDIA_ESM2_ENDPOINT", "https://integrate.api.nvidia.com/v1/esm2-650m")
    NVIDIA_ESM2_TIMEOUT = int(os.environ.get("NVIDIA_ESM2_TIMEOUT", "10"))


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    EXTERNAL_AI_ENABLED = False
    MONGO_URI = "mongodb://localhost:27017/quantum_drug_repurposing_test?serverSelectionTimeoutMS=2000"
