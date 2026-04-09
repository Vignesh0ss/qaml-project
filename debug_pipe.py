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

from app.services.pipeline import run_pipeline
import sys

print('Starting debug trace...')
try:
    res = run_pipeline("debug_id", {"disease_name": "ALS", "top_k": 5})
    print("Total Ranked:", len(res.get("ranked_drugs", [])))
    print("Total Rejected:", len(res.get("rejected_drugs", [])))
    print("First 15 rejected:", [r['name'] for r in res.get("rejected_drugs", [])][:15])
except Exception as e:
    print('Error:', e)
