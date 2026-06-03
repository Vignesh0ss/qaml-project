"""
Flask extensions: MongoDB, Redis, Celery, JWT. Initialized once, attached in create_app.
"""
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()
socketio = SocketIO()

# Redis and Celery are optional for minimal run without workers
_redis_client = None
_redis_checked = False  # cache the unavailable state to avoid repeated timeouts
_celery_app = None

def get_redis():
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client   # already know it's unavailable — don't retry
    _redis_checked = True
    try:
        import redis
        from flask import current_app
        url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()          # quick liveness check
        _redis_client = client
        print("[Redis] Connected successfully.")
    except Exception:
        _redis_client = None   # Redis not available — proceed without it
    return _redis_client


def get_celery():
    global _celery_app
    if _celery_app is None:
        try:
            from celery import Celery
            from flask import current_app
            _celery_app = Celery(
                "quantum_repurposing",
                broker=current_app.config.get("CELERY_BROKER_URL"),
                backend=current_app.config.get("CELERY_BROKER_URL"),
            )
            _celery_app.conf.update(
                task_serializer="json",
                accept_content=["json"],
                result_serializer="json",
            )
        except Exception:
            _celery_app = None
    return _celery_app


def ensure_indexes(app):
    """Ensure critical MongoDB indexes exist for performance."""
    with app.app_context():
        db = mongo.db
        if db is not None:
            try:
                print("[PyMongo] Ensuring indexes...")
                db.users.create_index("username", unique=True)
                db.users.create_index("email", unique=True)
                db.queries.create_index("task_id", unique=True)
                db.queries.create_index("created_at")
                db.results.create_index("task_id", unique=True)
                db.audit_log.create_index("timestamp")
                db.audit_log.create_index("task_id")
                print("[PyMongo] Indexes verified.")
            except Exception as e:
                print(f"[PyMongo] Index creation error: {e}")


def init_extensions(app):
    mongo.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors_origins = app.config.get("CORS_ALLOWED_ORIGINS", "*")
    socketio.init_app(app, cors_allowed_origins=cors_origins)
    ensure_indexes(app)
