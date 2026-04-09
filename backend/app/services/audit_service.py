"""
Secure Audit Logger: SHA-256 hash-chained entries in MongoDB. Tamper-evident.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

COLLECTION = "audit_log"


def _sha256(data: Dict[str, Any]) -> str:
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()

    return hashlib.sha256(json.dumps(data, sort_keys=True, cls=NumpyEncoder).encode()).hexdigest()


def log(
    db,
    task_id: str,
    event_type: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    user_id: Optional[str] = None,
    model_version: Optional[str] = None,
) -> str:
    if db is None:
        return ""
    coll = db[COLLECTION]
    prev = coll.find_one(sort=[("timestamp", -1)])
    prev_hash = prev["entry_hash"] if prev else "0" * 64
    entry = {
        "task_id": task_id,
        "event_type": event_type,
        "user_id": user_id,
        "model_version": model_version or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": _sha256(inputs),
        "output_hash": _sha256(outputs),
        "previous_hash": prev_hash,
    }
    entry["entry_hash"] = _sha256(entry)
    coll.insert_one(entry)
    return str(entry["entry_hash"])


def verify_chain(db, task_id: str) -> Tuple[bool, str]:
    """Verify hash chain integrity for entries belonging to task_id.

    The audit log is a GLOBAL chain across all tasks (each new entry's
    previous_hash points to the last entry ever inserted, not just the last
    entry for this task).  We therefore:
      1. Fetch all entries sorted by timestamp.
      2. Walk the global chain, verifying each entry's hash.
      3. Report a failure only if an entry that belongs to task_id is corrupt.
    """
    if db is None:
        return False, "database not available"
    coll = db[COLLECTION]

    # All entries for this task
    task_entries = list(coll.find({"task_id": task_id}).sort("timestamp", 1))
    if not task_entries:
        return False, "no entries found for task_id"

    task_ids_set = {str(e["_id"]) for e in task_entries}

    # Global chain (all entries, sorted)
    all_entries = list(coll.find().sort("timestamp", 1))

    prev_hash = "0" * 64
    for e in all_entries:
        # Validate previous_hash linkage
        if e.get("previous_hash") != prev_hash:
            if str(e["_id"]) in task_ids_set:
                return False, f"chain broken at timestamp {e.get('timestamp')}"
            # Entry from another task is broken – still update prev_hash to keep walking
            prev_hash = e.get("entry_hash", prev_hash)
            continue

        # Validate entry's own hash
        expected = _sha256({
            "task_id": e.get("task_id"),
            "event_type": e.get("event_type"),
            "user_id": e.get("user_id"),
            "model_version": e.get("model_version"),
            "timestamp": e.get("timestamp"),
            "input_hash": e.get("input_hash"),
            "output_hash": e.get("output_hash"),
            "previous_hash": e.get("previous_hash"),
        })
        if expected != e.get("entry_hash"):
            if str(e["_id"]) in task_ids_set:
                return False, f"entry_hash mismatch at {e.get('timestamp')}"
        prev_hash = e["entry_hash"]

    return True, "chain valid"


class AuditLogger:
    COLLECTION = COLLECTION

    @staticmethod
    def _sha256(data: dict) -> str:
        return _sha256(data)

    @classmethod
    def log(cls, db, task_id, event_type, inputs, outputs, user_id=None, model_version=None) -> str:
        if db is None:
            try:
                from flask import current_app
                db = current_app.extensions.get("pymongo") and current_app.extensions["pymongo"].mongo.db
            except Exception:
                db = None
        
        # Performance check: skip if db is offline to avoid cumulative 2s timeouts
        if db is not None:
            try:
                # Use a small timeout for the liveness check
                db.command("ping", maxTimeMS=200)
            except Exception:
                print(f"[Audit] Database offline, skipping event {event_type}")
                return ""
                
        return str(log(db, task_id, event_type, inputs, outputs, user_id, model_version))

    @classmethod
    def verify_chain(cls, db, task_id: str) -> Tuple[bool, str]:
        return verify_chain(db, task_id)
