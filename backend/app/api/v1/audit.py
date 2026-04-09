"""
GET /api/v1/audit/<task_id> — Audit chain for query.
GET /api/v1/audit/verify/<task_id> — Verify hash chain integrity.
"""
from flask import Blueprint, jsonify
from app.extensions import mongo
from app.services.audit_service import AuditLogger

bp = Blueprint("audit", __name__)


@bp.route("/audit/<task_id>", methods=["GET"])
def get_audit(task_id):
    db = mongo.db
    if db is None:
        return jsonify({"task_id": task_id, "entries": []}), 200
    try:
        coll = db[AuditLogger.COLLECTION]
        cursor = coll.find({"task_id": task_id}).sort("timestamp", 1)
        entries = []
        for e in cursor:
            e.pop("_id", None)
            # Frontend expects 'action'; DB stores 'event_type' — expose both
            if "action" not in e and "event_type" in e:
                e["action"] = e["event_type"]
            entries.append(e)
        return jsonify({"task_id": task_id, "entries": entries}), 200
    except Exception:
        return jsonify({"task_id": task_id, "entries": []}), 200


@bp.route("/audit/verify/<task_id>", methods=["GET"])
def verify_audit(task_id):
    db = mongo.db
    if db is None:
        return jsonify({"task_id": task_id, "valid": False, "message": "database unavailable"}), 200
    try:
        valid, message = AuditLogger.verify_chain(db, task_id)
        return jsonify({"task_id": task_id, "valid": valid, "message": message}), 200
    except Exception:
        return jsonify({"task_id": task_id, "valid": False, "message": "database offline"}), 200


@bp.route("/audit/history", methods=["GET"])
def get_audit_history():
    """
    Separate history view:
    includes task_id, disease, status, and failure reason (if any).
    """
    db = mongo.db
    if db is None:
        return jsonify({"items": []}), 200
    try:
        q_cursor = db["queries"].find(
            {},
            {"_id": 0, "task_id": 1, "disease_name": 1, "status": 1, "created_at": 1, "error": 1, "completed_at": 1},
        ).sort("created_at", -1).limit(200)
        items = []
        for q in q_cursor:
            items.append(
                {
                    "task_id": q.get("task_id", ""),
                    "disease_name": q.get("disease_name", "Unknown"),
                    "status": q.get("status", "unknown"),
                    "reason": q.get("error", ""),
                    "created_at": q.get("created_at"),
                    "completed_at": q.get("completed_at"),
                }
            )
        return jsonify({"items": items}), 200
    except Exception:
        return jsonify({"items": []}), 200
