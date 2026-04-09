"""
Stats endpoint: returns real live query/drug/user counts from MongoDB.
"""
from flask import Blueprint, jsonify
from datetime import datetime, timezone
from app.extensions import mongo
import traceback

bp = Blueprint("stats", __name__)


@bp.route("/stats", methods=["GET"])
def get_stats():
    try:
        db = mongo.db
        if db is None:
            return jsonify({
                "total_queries": 0,
                "completed": 0,
                "drugs_analyzed": 0,
                "audit_entries": 0,
                "recent": [],
                "warning": "Database is offline. Stats unavailable."
            }), 200

        queries_coll = db["queries"]
        results_coll = db["results"]
        audit_coll = db["audit_log"]

        total_queries = queries_coll.count_documents({})
        completed = queries_coll.count_documents({"status": "done"})
        total_audit = audit_coll.count_documents({})

        # Count distinct drug candidates across all results
        # Use $ifNull for cases where ranked_drugs is missing
        pipeline = [
            {"$project": {"count": {"$size": {"$ifNull": ["$ranked_drugs", []]}}}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}}
        ]
        drugs_res = list(results_coll.aggregate(pipeline))
        drugs_analyzed = drugs_res[0]["total"] if drugs_res else 0

        # Recent queries (last 10)
        recent_raw = list(
            queries_coll.find({}, {"task_id": 1, "disease_name": 1,
                                   "status": 1, "created_at": 1, "top_k": 1})
            .sort("created_at", -1)
            .limit(10)
        )
        
        # Batch fetch results for these 10 tasks to avoid N+1 queries
        task_ids = [q.get("task_id") for q in recent_raw if q.get("task_id")]
        results_docs = {r["task_id"]: r for r in results_coll.find({"task_id": {"$in": task_ids}}, {"task_id": 1, "ranked_drugs": 1})}

        recent = []
        history = []
        now = datetime.now(timezone.utc)
        for q in recent_raw:
            created = q.get("created_at")
            if isinstance(created, str):
                try:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                except Exception:
                    created_dt = None
            else:
                created_dt = created

            if created_dt:
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                diff = now - created_dt
                mins = int(diff.total_seconds() / 60)
                if mins < 1:
                    time_str = "just now"
                elif mins < 60:
                    time_str = f"{mins}m ago"
                elif mins < 1440:
                    time_str = f"{int(mins/60)}h ago"
                else:
                    time_str = f"{int(mins/1440)}d ago"
            else:
                time_str = "recently"

            # Check if we have results for this task in our pre-fetched map
            res_doc = results_docs.get(q.get("task_id"))
            if res_doc and "ranked_drugs" in res_doc:
                drugs_count = len(res_doc["ranked_drugs"])
            else:
                drugs_count = q.get("top_k", 0)

            recent.append({
                "task_id": str(q.get("task_id", "")),
                "query":   str(q.get("disease_name", "Unknown")),
                "status":  str(q.get("status", "unknown")),
                "drugs":   int(drugs_count),
                "time":    time_str,
            })

        # Full history for dashboard audit section (last 50)
        hist_raw = list(
            queries_coll.find(
                {},
                {"task_id": 1, "disease_name": 1, "status": 1, "created_at": 1, "error": 1},
            )
            .sort("created_at", -1)
            .limit(50)
        )
        for h in hist_raw:
            history.append(
                {
                    "task_id": str(h.get("task_id", "")),
                    "disease_name": str(h.get("disease_name", "Unknown")),
                    "status": str(h.get("status", "unknown")),
                    "reason": str(h.get("error", "")),
                    "created_at": h.get("created_at"),
                }
            )

        return jsonify({
            "total_queries":  int(total_queries),
            "completed":      int(completed),
            "drugs_analyzed": int(drugs_analyzed),
            "audit_entries":  int(total_audit),
            "recent":         recent,
            "history":        history,
        })
    except Exception as exc:
        if "Timeout" in str(exc) or "Socket" in str(exc) or "ServerSelectionTimeoutError" in type(exc).__name__:
            return jsonify({
                "total_queries": 0,
                "completed": 0,
                "drugs_analyzed": 0,
                "audit_entries": 0,
                "recent": [],
                "warning": "Database is currently offline. Showing mock data."
            }), 200
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500
