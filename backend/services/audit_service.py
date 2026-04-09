import os
import json
import hashlib
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AUDIT_LOG_FILE = os.path.join(BASE_DIR, "backend", "data", "raw", "audit_registry.json")


def initialize_audit_log():
    """Initializes the audit log if it doesn't exist."""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    if not os.path.exists(AUDIT_LOG_FILE):
        initial_entry = {
            "entries": [
                {
                    "event_name": "genesis_block",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data_hash": hashlib.sha256(b"genesis").hexdigest(),
                    "previous_hash": "0" * 64,
                    "entry_hash": hashlib.sha256(b"genesis").hexdigest()
                }
            ]
        }
        with open(AUDIT_LOG_FILE, 'w') as f:
            json.dump(initial_entry, f, indent=4)


def log_event(event_name, data_payload):
    """
    Logs an event securely using a SHA-256 hash chain.
    """
    initialize_audit_log()

    with open(AUDIT_LOG_FILE, 'r') as f:
        log_data = json.load(f)

    last_entry = log_data["entries"][-1]
    previous_hash = last_entry["entry_hash"]

    # Serialize data payload to JSON string
    serialized_data = json.dumps(data_payload, sort_keys=True)
    data_hash = hashlib.sha256(serialized_data.encode('utf-8')).hexdigest()

    timestamp = datetime.now(timezone.utc).isoformat()

    # Create tamper-evident entry_hash (previous_hash + data_hash)
    entry_string = f"{previous_hash}{data_hash}{timestamp}"
    entry_hash = hashlib.sha256(entry_string.encode('utf-8')).hexdigest()

    new_entry = {
        "event_name": event_name,
        "timestamp": timestamp,
        "data_payload": data_payload,
        "data_hash": data_hash,
        "previous_hash": previous_hash,
        "entry_hash": entry_hash
    }

    log_data["entries"].append(new_entry)

    with open(AUDIT_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=4)

    return entry_hash


def main():
    # Test the service with the final 5 discovery list
    processed_dir = os.path.join(BASE_DIR, "backend", "data", "processed")
    final_5_csv = os.path.join(processed_dir, "final_5_discovery_list.csv")

    print(f"Reading {final_5_csv} for audit logging...")
    if os.path.exists(final_5_csv):
        import pandas as pd
        df = pd.read_csv(final_5_csv)
        payload = df.to_dict(orient='records')

        entry_hash = log_event("QUBO_Final_Discovery_Selected", payload)
        print("✅ Secure Audit Entry Created!")
        print(f"Entry Hash: {entry_hash}")
    else:
        print("Final discovery list not found. Run Phase 6 first.")


if __name__ == "__main__":
    main()
