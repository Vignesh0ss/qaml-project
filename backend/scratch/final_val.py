import os
from dotenv import load_dotenv
load_dotenv()

import time
import json
from app import create_app
from app.services.pipeline import run_pipeline
from app.extensions import mongo
import traceback

def test_final():
    app = create_app("development")
    with app.app_context():
        db = mongo.db
        task_id = "final_verification_test"
        disease = "Achondroplasia" # Should trigger AI fallback
        
        print(f"Starting pipeline for '{disease}'...")
        t0 = time.time()
        
        # We simulate the background task flow
        try:
            results = run_pipeline(task_id, {"disease_name": disease, "top_k": 5}, db=db)
            print(f"Pipeline finished in {time.time() - t0:.2f}s")
            
            ranked = results.get("ranked_drugs", [])
            print(f"Found {len(ranked)} candidates.")
            for d in ranked:
                print(f"- {d.get('drug_name')} (Source: {d.get('source')})")
            
            summary = results.get("ai_summary", "")
            print("\n--- AI FORMAL SUMMARY ---")
            print(summary)
            print("--------------------------")
            
            # Validation
            has_ai = any(d.get("source") == "nvidia_ai" for d in ranked)
            has_structure = "I. REPORT SUMMARY" in summary and "IV. CONCLUSION" in summary
            has_emojis = any(c in summary for c in "😊🚀🔬🏥")
            
            print(f"\nVALIDATION:")
            print(f"- AI Fallback Triggered: {has_ai}")
            print(f"- Formal Structure (I-IV): {has_structure}")
            print(f"- No Emojis: {not has_emojis}")
            
        except Exception as e:
            print(f"Pipeline failed: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_final()
