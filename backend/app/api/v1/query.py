"""
POST /api/v1/query — Submit drug repurposing query. Returns 202 + task_id.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
import threading
from app.extensions import mongo
from app.schemas import QuerySchema
from marshmallow import ValidationError

bp = Blueprint("query", __name__)


@bp.route("/query", methods=["POST"])
def submit_query():
    raw_payload = request.get_json(silent=True) or {}
    if not raw_payload:
        return jsonify({"error": "Missing required field: disease_name"}), 400
    try:
        data = QuerySchema().load(raw_payload)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 422

    disease_name = data.get("disease_name")
    top_k = 10
    
    task_id = str(uuid.uuid4())
    try:
        user_id = get_jwt_identity()
    except Exception:
        user_id = None
    if isinstance(user_id, dict):
        user_id = user_id.get("user_id") or str(user_id)
    
    query_doc = {
        "task_id": task_id,
        "user_id": user_id or "anonymous",
        "disease_name": disease_name,
        "top_k": top_k,
        "constraints": data.get("constraints", {}),
        "status": "queued",
        "created_at": None,
        "completed_at": None,
    }
    
    # FR-QRY-03: Return quickly and run heavy pipeline work in background.
    def _run_pipeline_background():
        from app.tasks.pipeline_tasks import run_pipeline_sync
        from datetime import datetime, timezone
        from pymongo.errors import ServerSelectionTimeoutError
        import traceback

        try:
            db = mongo.db
            if db is not None:
                query_doc["created_at"] = datetime.now(timezone.utc).isoformat()
                try:
                    db["queries"].insert_one(query_doc)
                except ServerSelectionTimeoutError:
                    return

            run_pipeline_sync(
                task_id,
                {"disease_name": disease_name, "top_k": top_k, "user_id": user_id},
                db=db,
            )
        except Exception as e:
            print(f"[QueryAPI] Pipeline CRITICAL FAILURE: {str(e)}")
            traceback.print_exc()
            if mongo.db is not None:
                mongo.db["queries"].update_one(
                    {"task_id": task_id},
                    {"$set": {"status": "failed", "error": str(e)}},
                )

    threading.Thread(target=_run_pipeline_background, daemon=True).start()
    return jsonify({"task_id": task_id, "status": "queued"}), 202


@bp.route("/query/<task_id>/status", methods=["GET"])
def get_status(task_id):
    db = mongo.db
    if db is None:
        return jsonify({"task_id": task_id, "status": "unknown"}), 200
    try:
        q = db["queries"].find_one({"task_id": task_id})
    except Exception:
        return jsonify({"task_id": task_id, "status": "database_offline"}), 200
    if not q:
        return jsonify({"task_id": task_id, "status": "queued"}), 200
    return jsonify({"task_id": task_id, "status": q.get("status", "queued")}), 200
