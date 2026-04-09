import os
import sys
# Add backend to path so modules resolve automatically
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if 'backend/tests' in WORKSPACE_DIR.replace('\\', '/'):
    BACKEND_DIR = os.path.dirname(WORKSPACE_DIR)
else:
    BACKEND_DIR = os.path.join(WORKSPACE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import sys
import json
sys.path.insert(0, './backend')
from app.services.pipeline import run_pipeline

q = {"disease_name": "corona", "top_k": 5}
res = run_pipeline("test-corona-12345", q)
print("\nPipeline Result:")
for drug in res["ranked_drugs"]:
    print(f"Rank {drug['rank']}: Target - {drug.get('target_name', '')} | Score: {drug.get('score', 0)}")

# Check audit log
from pymongo import MongoClient
c = MongoClient("mongodb://localhost:27017/")
db = c["quantum_drug_repurposing"]
audit = db["audit_log"].find_one({"task_id": "test-corona-12345"})
if audit:
    print(f"Audit log found! Hash: {audit.get('entry_hash')}")
else:
    print("Audit log MISSING!")
