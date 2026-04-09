"""Test the drug validity gate — verify ions are rejected and real drugs pass."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.extensions import mongo
from app.services.pipeline import run_pipeline

app = create_app('development')
with app.app_context():
    db = mongo.db
    print('=== DRUG VALIDITY GATE TEST ===')
    try:
        result = run_pipeline('validity_test_001', {'disease_name': 'Progeria', 'top_k': 5}, db=db)
        print(f"\nStatus: {result.get('status')}")
        print(f"Valid candidates: {len(result.get('ranked_drugs', []))}")
        
        print("\n--- SELECTED CANDIDATES ---")
        for d in result.get('ranked_drugs', []):
            print(f"  [{d.get('rank')}] {d.get('drug_name')} | Phase: {d.get('max_phase')} | Score: {d.get('score', 0):.3f}")
            print(f"       Target: {d.get('target_name')} | SMILES: {(d.get('canonical_smiles',''))[:50]}...")
        
        print(f"\n--- REJECTED CANDIDATES ---")
        for rej in result.get('rejected_drugs', []):
            print(f"  X {rej.get('name')} -> {rej.get('reason')}")
            
    except Exception as e:
        import traceback
        print(f"PIPELINE ERROR: {e}")
        traceback.print_exc()
