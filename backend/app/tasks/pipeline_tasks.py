"""
Celery task: pipeline_task.delay(task_id, query).
Sync fallback: run_pipeline_sync(task_id, query) when Celery not available.
"""
import os
import sys
from typing import Dict, Any

# Ensure backend is on path when running as script or from Celery
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _get_db():
    """Get MongoDB db from Flask app context or create app."""
    try:
        # _get_current_object() raises RuntimeError when outside context
        from app.extensions import mongo
        return mongo.db
    except Exception:
        pass
    try:
        from app import create_app
        from app.extensions import mongo
        app = create_app("development")
        with app.app_context():
            return mongo.db
    except Exception:
        return None


def run_pipeline_sync(task_id: str, query: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Run pipeline synchronously (no Celery). Used when broker not available."""
    from app.services.pipeline import run_pipeline
    
    if db is not None:
        return run_pipeline(task_id, query, db=db)

    try:
        from flask import current_app
        # _get_current_object() raises RuntimeError when outside context
        current_app._get_current_object()
        from app.extensions import mongo
        return run_pipeline(task_id, query, db=mongo.db)
    except (RuntimeError, Exception):
        pass

    from app import create_app
    from app.extensions import mongo
    app = create_app("development")
    with app.app_context():
        try:
            return run_pipeline(task_id, query, db=mongo.db)
        except Exception as e:
            if mongo.db:
                mongo.db.queries.update_one({"task_id": task_id}, {"$set": {"status": "failed", "error": str(e)}})
            raise e


# Celery task: only register if broker URL is set
_celery_app = None
try:
    from celery import Celery
    broker = os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL", ""))
    if broker:
        _celery_app = Celery("quantum_repurposing", broker=broker, backend=broker)
        _celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")
except Exception:
    pass

if _celery_app is not None:
    @_celery_app.task(bind=True, max_retries=3)
    def pipeline_task(self, task_id: str, query: dict):
        try:
            from app.services.pipeline import run_pipeline
            db = _get_db()
            return run_pipeline(task_id, query, db=db)
        except Exception as exc:
            self.retry(exc=exc, countdown=30)
else:
    def pipeline_task(*args, **kwargs):
        raise RuntimeError("Celery not configured; use run_pipeline_sync instead")
