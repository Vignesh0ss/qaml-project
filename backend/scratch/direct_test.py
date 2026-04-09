"""Direct pipeline test - bypasses Flask threading to see real errors."""
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
    print('=== DIRECT PIPELINE TEST ===')
    try:
        result = run_pipeline('direct_test_001', {'disease_name': 'Progeria', 'top_k': 5}, db=db)
        print(f"Status: {result.get('status')}")
        print(f"Candidates: {len(result.get('ranked_drugs', []))}")
        for d in result.get('ranked_drugs', [])[:3]:
            print(f"  - {d.get('drug_name')} (score: {d.get('score', 0):.3f})")
    except Exception as e:
        import traceback
        print(f"PIPELINE CRASHED: {e}")
        traceback.print_exc()
