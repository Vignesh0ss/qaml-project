"""
GET /api/v1/results/<task_id> — Retrieve ranked drug results.
"""
from flask import Blueprint, jsonify
from app.extensions import mongo

bp = Blueprint("results", __name__)


def _json_safe(obj):
    """
    Convert nested Mongo/Python values into JSON-safe primitives.
    Prevents intermittent 500s from non-serializable values.
    """
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, set):
        return [_json_safe(v) for v in sorted(list(obj), key=lambda x: str(x))]
    try:
        # numpy scalar support (if present)
        import numpy as np  # type: ignore
        if isinstance(obj, np.generic):
            return obj.item()
    except Exception:
        pass
    return obj


@bp.route("/results/<task_id>", methods=["GET"])
def get_results(task_id):
    db = mongo.db
    if db is None:
        return jsonify({"error": "database unavailable"}), 503
    try:
        # Prefer finished result; fall back to query status for polling
        doc = db["results"].find_one({"task_id": task_id})
        if not doc:
            q = db["queries"].find_one({"task_id": task_id})
            if q:
                q.pop("_id", None)
                return jsonify({"task_id": task_id, "status": q.get("status", "running"), "ranked_drugs": []}), 200
            return jsonify({"error": "results not found", "task_id": task_id}), 404
    except Exception:
        return jsonify({"error": "database offline", "task_id": task_id}), 503

    doc.pop("_id", None)
    doc = _json_safe(doc)
    ranked = doc.get("ranked_drugs") or []
    rejected = doc.get("rejected_drugs") or []
    doc["ranked_drugs"] = ranked[:10]
    doc["rejected_drugs"] = rejected[:10]
    for r in doc["ranked_drugs"]:
        if "priority" not in r:
            cl = str(r.get("confidence_label", "")).upper()
            r["priority"] = cl if cl in {"HIGH", "MEDIUM", "LOW"} else "MEDIUM"
    for rj in doc["rejected_drugs"]:
        if "priority" not in rj:
            rj["priority"] = "LOW"
    # Normalize summary fields for frontend compatibility.
    if "medical_summary" not in doc and "ai_summary" in doc:
        doc["medical_summary"] = doc["ai_summary"]
    if not str(doc.get("ai_summary", "")).strip():
        doc["ai_summary"] = "AI summary generation in progress..."
    if not str(doc.get("medical_summary", "")).strip():
        doc["medical_summary"] = doc["ai_summary"]
    return jsonify(doc), 200
