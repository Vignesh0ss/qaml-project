import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.services.pipeline import run_pipeline

def test_progeria():
    print("Testing Pipeline v3 with Progeria...")
    query = {"disease_name": "Progeria", "top_k": 5}
    task_id = "test_task_123"
    
    # Run without DB (db=None)
    result = run_pipeline(task_id, query, db=None)
    
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'done':
        ranked = result.get('ranked_drugs', [])
        print(f"Ranked Drugs: {len(ranked)}")
        for d in ranked:
            print(f" - {d.get('drug_name')} (Phase {d.get('max_phase')}) | Target: {d.get('target_name')} | Score: {d.get('score')} | Reasoning: {d.get('reasoning')}")
        
        rejected = result.get('rejected_drugs', [])
        print(f"\nRejected Drugs (Sample {len(rejected)}):")
        for r in rejected[:5]:
            print(f" - {r.get('name')} | Reason: {r.get('reason')}")
            
        print(f"\nQUBO Energy: {result.get('qubo_energy')}")
        
        summary = result.get('pipeline_summary', {})
        print(f"Summary Funnel: {summary}")
        
        # Validate keys for frontend
        expected_keys = ["stage_genes", "stage_targets", "stage_candidates_raw", "stage_hard_rejected", "stage_passed", "stage_ranked"]
        missing = [k for k in expected_keys if k not in summary]
        if missing:
            print(f"CRITICAL: Missing summary keys: {missing}")
        else:
            print("SUCCESS: All funnel keys present.")
    else:
        print(f"FAILED: {result.get('message')}")

if __name__ == "__main__":
    test_progeria()
