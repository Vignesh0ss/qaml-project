import os
import time
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append("backend")

from app import create_app
from app.services.pipeline import run_pipeline
from app.extensions import mongo

def ensure_all():
    app = create_app("development")
    with app.app_context():
        db = mongo.db
        
        # Test 1: High-Speed Cached/Local Query (Progeria)
        print("\n[TEST 1] VERIFYING PROGERIA (Local/Fast Path)...")
        t0 = time.time()
        res1 = run_pipeline("bench_progeria", {"disease_name": "Progeria", "top_k": 5}, db=db)
        print(f"RES: {res1.get('status')} | Time: {time.time() - t0:.2f}s | Candidates: {len(res1.get('ranked_drugs', []))}")
        
        # Test 2: AI Search & Fetch Fallback (Achondroplasia)
        print("\n[TEST 2] VERIFYING ACHONDROPLASIA (AI Search Fallback)...")
        # Ensure we use a unique task ID to avoid cache hits for this test if we want a fresh run
        t1 = time.time()
        res2 = run_pipeline("bench_achondro", {"disease_name": "Achondroplasia", "top_k": 5}, db=db)
        print(f"RES: {res2.get('status')} | Time: {time.time() - t1:.2f}s | Candidates: {len(res2.get('ranked_drugs', []))}")
        
        # Test 3: Fresh High-Speed Discovery (Parkinson's)
        print("\n[TEST 3] VERIFYING PARKINSON'S (Fresh Discovery - AI Summary)...")
        t2 = time.time()
        # Use a unique disease name or clear cache to ensure AI generates fresh summary
        res3 = run_pipeline("bench_parkinsons", {"disease_name": "Parkinsons Disease", "top_k": 5}, db=db)
        print(f"RES: {res3.get('status')} | Time: {time.time() - t2:.2f}s | Candidates: {len(res3.get('ranked_drugs', []))}")
        
        summary3 = res3.get('ai_summary', '')
        has_structure = "I." in summary3 and "IV." in summary3
        print(f"Parkinson's Summary Structure (I-IV): {has_structure}")
        
        print("\n[SUMMARY]")
        print(f"Progeria Summary Structure: {'I.' in res1.get('ai_summary', '')}")
        print(f"Achondroplasia AI Triggered: {any(d.get('source') == 'nvidia_ai' for d in res2.get('ranked_drugs', []))}")
        print(f"Final Report Health: {has_structure}")

if __name__ == "__main__":
    ensure_all()
