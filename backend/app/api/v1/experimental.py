"""
Experimental researcher workflow:
- Unknown disease inference from structured input
- Weighted multi-disease drug recommendation
- Downloadable Word-compatible report
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict

from flask import Blueprint, jsonify, request, Response

from app.extensions import mongo
from app.services.pipeline import run_pipeline
from app.services.experimental_service import (
    attach_database_drug_recommendations,
    classify_unknown_disease,
    combine_weighted_drugs,
    format_experimental_summary_text,
    validate_experimental_payload,
)

bp = Blueprint("experimental", __name__)

_RUN_CACHE: Dict[str, Dict[str, Any]] = {}
_MAX_RUN_CACHE = 200
RUNS_COLLECTION = "experimental_runs"

def _classification_level_recommendations(predictions, top_k: int = 10):
    """
    Fallback recommendations derived directly from disease classification output.
    """
    recs = []
    seen = set()
    for p in predictions or []:
        disease = str(p.get("disease", "Unknown")).strip()
        prob = float(p.get("prob", 0.0) or 0.0)
        for name in p.get("recommended_drugs") or []:
            key = str(name).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            recs.append(
                {
                    "drug_name": str(name).strip(),
                    "final_score": round(max(0.2, prob), 4),
                    "source_diseases": [disease] if disease else [],
                    "target": "classification_fallback",
                    "confidence": "LOW",
                }
            )
    recs.sort(key=lambda x: x["final_score"], reverse=True)
    return recs[:top_k]


def _trim_cache() -> None:
    if len(_RUN_CACHE) <= _MAX_RUN_CACHE:
        return
    keys = list(_RUN_CACHE.keys())
    for k in keys[: len(_RUN_CACHE) - _MAX_RUN_CACHE]:
        _RUN_CACHE.pop(k, None)


def _persist_run(db, run_doc: Dict[str, Any]) -> None:
    if db is None:
        return
    try:
        db[RUNS_COLLECTION].replace_one({"run_id": run_doc["run_id"]}, run_doc, upsert=True)
    except Exception:
        # Keep API resilient even if DB is transiently offline.
        pass


def _load_run(db, run_id: str) -> Dict[str, Any] | None:
    if db is None:
        return None
    try:
        doc = db[RUNS_COLLECTION].find_one({"run_id": run_id})
        if not doc:
            return None
        doc.pop("_id", None)
        return doc
    except Exception:
        return None


def _run_pipeline_with_timeout(task_id: str, disease: str, db, timeout_sec: float = 12.0):
    box: Dict[str, Any] = {"result": None, "error": None}

    def _target():
        try:
            box["result"] = run_pipeline(task_id, {"disease_name": disease, "top_k": 3}, db=db)
        except Exception as exc:
            box["error"] = exc

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        return None, f"Pipeline stage timed out for {disease}."
    if box["error"] is not None:
        return None, f"Pipeline stage failed for {disease}: {box['error']}"
    return box["result"], None


@bp.route("/experimental/suggest", methods=["POST"])
def suggest_experimental():
    run_id = str(uuid4())
    db = mongo.db
    payload = request.get_json(silent=True) or {}
    symptoms = payload.get("symptoms") or []

    try:
        validation_warnings = validate_experimental_payload(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    result: Dict[str, Any] = {
        "run_id": run_id,
        "mode": "experimental",
        "status": "processing",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "input": {
            "age": payload.get("age"),
            "gender": payload.get("gender"),
            "blood_group": payload.get("blood_group"),
            "duration_days": payload.get("duration_days"),
            "symptoms": symptoms,
            "gene_patterns": payload.get("gene_patterns") or [],
            "lab_results": payload.get("lab_results") or {},
            "notes": payload.get("notes", ""),
        },
        "predicted_diseases": [],
        "recommended_drugs": [],
        "summary": "",
        "warnings": [
            "Experimental inference only. Not medical advice.",
            "Disease probabilities are approximate and should be validated clinically.",
            *validation_warnings,
        ],
        "errors": [],
    }
    _persist_run(db, result)

    try:
        predictions = classify_unknown_disease(payload)
        predictions = attach_database_drug_recommendations(predictions, per_disease_k=5)
        result["predicted_diseases"] = predictions

        per_disease_results: Dict[str, Dict[str, Any]] = {}
        # Keep this interactive and resilient: use top-1 disease and smaller candidate pool.
        for p in predictions[:1]:
            disease = str(p.get("disease", "")).strip()
            if not disease:
                continue
            task_id = f"exp-{uuid4()}"
            stage_result, stage_err = _run_pipeline_with_timeout(task_id, disease, db, timeout_sec=12.0)
            if stage_err:
                result["errors"].append(stage_err)
                continue
            if stage_result:
                per_disease_results[disease] = stage_result

        patient_genes = {str(g).strip().upper() for g in (payload.get("gene_patterns") or []) if str(g).strip()}
        result["recommended_drugs"] = combine_weighted_drugs(predictions, per_disease_results, patient_genes)
        if not result["recommended_drugs"]:
            result["recommended_drugs"] = _classification_level_recommendations(predictions, top_k=10)

        result["summary"] = format_experimental_summary_text(
            result["predicted_diseases"],
            result["recommended_drugs"],
        )

        result["status"] = "done"
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        _RUN_CACHE[run_id] = result
        _trim_cache()
        _persist_run(db, result)
        return jsonify(result), 200
    except Exception as e:
        result["status"] = "failed"
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        result["errors"].append(f"Unhandled experimental processing error: {e}")
        result["summary"] = (
            "Experimental workflow completed with partial failure. "
            "Please verify inputs and retry."
        )
        _RUN_CACHE[run_id] = result
        _trim_cache()
        _persist_run(db, result)
        return jsonify(result), 200


@bp.route("/experimental/report/<run_id>/word", methods=["GET"])
def experimental_report_word(run_id: str):
    db = mongo.db
    item = _RUN_CACHE.get(run_id) or _load_run(db, run_id)
    if not item:
        return jsonify({"error": "Run not found or expired.", "run_id": run_id}), 404

    lines = []
    lines.append("QAML EXPERIMENTAL RESEARCH REPORT")
    lines.append("=" * 60)
    lines.append(f"Run ID: {run_id}")
    lines.append(f"Generated At: {item.get('created_at', '')}")
    lines.append("Mode: EXPERIMENTAL")
    lines.append(f"Status: {item.get('status', 'unknown')}")
    lines.append("")
    lines.append("PATIENT INPUT")
    lines.append("-" * 60)
    ip = item.get("input", {})
    lines.append(f"Age: {ip.get('age', '')}")
    lines.append(f"Gender: {ip.get('gender', '')}")
    lines.append(f"Blood Group: {ip.get('blood_group', '')}")
    lines.append(f"Duration (days): {ip.get('duration_days', '')}")
    lines.append(f"Symptoms: {', '.join(ip.get('symptoms', []) or [])}")
    lines.append(f"Gene Patterns: {', '.join(ip.get('gene_patterns', []) or [])}")
    lines.append(f"Lab Results: {ip.get('lab_results', {})}")
    if ip.get("notes"):
        lines.append(f"Notes: {ip.get('notes')}")
    lines.append("")
    lines.append("PREDICTED DISEASES")
    lines.append("-" * 60)
    for p in item.get("predicted_diseases", []):
        lines.append(f"{p.get('disease')}: {round(float(p.get('prob', 0.0))*100, 2)}%")
    lines.append("")
    lines.append("RECOMMENDED DRUGS")
    lines.append("-" * 60)
    for i, d in enumerate(item.get("recommended_drugs", []), start=1):
        lines.append(
            f"{i}. {d.get('drug_name')} | score={d.get('final_score')} | confidence={d.get('confidence')} "
            f"| sources={', '.join(d.get('source_diseases', []) or [])}"
        )
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 60)
    lines.append(str(item.get("summary", "")))
    lines.append("")
    lines.append("WARNING")
    lines.append("-" * 60)
    for w in item.get("warnings", []):
        lines.append(f"- {w}")
    if item.get("errors"):
        lines.append("")
        lines.append("ERRORS")
        lines.append("-" * 60)
        for err in item.get("errors", []):
            lines.append(f"- {err}")

    content = "\r\n".join(lines)
    filename = f"qaml-experimental-report-{run_id}.doc"
    return Response(
        content,
        mimetype="application/msword",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

