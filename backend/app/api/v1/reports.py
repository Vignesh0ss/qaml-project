"""
GET /api/v1/reports/<task_id>/word — Download Word-compatible report (.doc).
"""
from flask import Blueprint, jsonify, Response
from app.extensions import mongo

bp = Blueprint("reports", __name__)


@bp.route("/reports/<task_id>/word", methods=["GET"])
def get_report_word(task_id):
    db = mongo.db
    if db is None:
        return jsonify({"error": "database unavailable", "task_id": task_id}), 503
    try:
        q = db["queries"].find_one({"task_id": task_id}) or {}
        r = db["results"].find_one({"task_id": task_id}) or {}
        a = list(db["audit_log"].find({"task_id": task_id}).sort("timestamp", 1))
    except Exception:
        return jsonify({"error": "database offline", "task_id": task_id}), 503

    for x in a:
        x.pop("_id", None)
    q.pop("_id", None)
    r.pop("_id", None)

    lines = []
    lines.append("QAML RESEARCH REPORT")
    lines.append("=" * 60)
    lines.append(f"Task ID: {task_id}")
    lines.append(f"Disease: {r.get('disease') or q.get('disease_name', 'Unknown')}")
    lines.append(f"Status: {q.get('status', r.get('status', 'unknown'))}")
    if q.get("error"):
        lines.append(f"Failure Reason: {q.get('error')}")
    lines.append("")
    lines.append("AI SUMMARY")
    lines.append("-" * 60)
    lines.append(str(r.get("ai_summary") or r.get("medical_summary") or "Summary unavailable."))
    lines.append("")
    lines.append("DRUG CANDIDATES")
    lines.append("-" * 60)
    candidates = r.get("candidates") or []
    if not candidates:
        candidates = r.get("ranked_drugs") or []
    for i, c in enumerate(candidates, start=1):
        name = c.get("drug_name") or c.get("target_name") or "Unknown"
        score = c.get("ml_score", c.get("score", ""))
        target = c.get("target", c.get("target_name", ""))
        lines.append(f"{i}. {name} | score={score} | target={target}")
    lines.append("")
    lines.append("AUDIT LOG")
    lines.append("-" * 60)
    if not a:
        lines.append("No audit entries.")
    for e in a:
        event = e.get("event_type", "EVENT")
        ts = e.get("timestamp", "")
        details = e.get("input_snapshot", {}) or {}
        lines.append(f"{ts} | {event} | {details}")

    content = "\r\n".join(lines)
    filename = f"qaml-report-{task_id}.doc"
    return Response(
        content,
        mimetype="application/msword",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
