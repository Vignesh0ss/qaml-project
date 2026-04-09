import time
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append("backend")
from app import create_app
from app.services.pipeline import run_pipeline
from app.extensions import mongo

def verify_logic():
    app = create_app("development")
    with app.app_context():
        db = mongo.db
        query = {"disease_name": "Progeria", "top_k": 5}
        
        print("--- LOGIC CACHE VERIFICATION ---")
        
        # RUN 1: Warm up cache
        print("\n[RUN 1] Running full pipeline for 'Progeria'...")
        t0 = time.time()
        res1 = run_pipeline("verify_v1", query, db=db)
        print(f"Run 1 Time: {time.time() - t0:.2f}s")
        
        # RUN 2: Instant Hit
        print("\n[RUN 2] Running again for 'Progeria' (Expect sub-100ms)...")
        t1 = time.time()
        res2 = run_pipeline("verify_v2", query, db=db)
        time2 = time.time() - t1
        print(f"Run 2 Time: {time2:.4f}s")
        
        if time2 < 0.1:
            print("\nRESULT: SUCCESS - LOGIC CACHE IS WORKING (Instant Hit)")
        else:
            print(f"\nRESULT: FAIL ({time2:.4f}s)")

if __name__ == "__main__":
    verify_logic()
