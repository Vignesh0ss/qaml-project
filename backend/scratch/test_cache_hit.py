import time
import requests
import json

def test_cache():
    url = "http://localhost:5000/api/v1/query" 
    payload = {
        "disease_name": "Progeria",
        "top_k": 5
    }
    
    print("--- CACHE VERIFICATION TEST ---")
    
    # RUN 1: Potential Cold Start / Mapping
    print("\n[RUN 1] Requesting 'Progeria'...")
    t0 = time.time()
    try:
        r1 = requests.post(url, json=payload, timeout=60)
        time1 = time.time() - t0
        print(f"Status: {r1.status_code} | Time: {time1:.2f}s")
    except Exception as e:
        print(f"Run 1 Failed: {e}")
        return

    # RUN 2: Expected Cache Hit
    print("\n[RUN 2] Requesting 'Progeria' again (Expect < 0.1s)...")
    t1 = time.time()
    try:
        r2 = requests.post(url, json=payload, timeout=5)
        time2 = time.time() - t1
        print(f"Status: {r2.status_code} | Time: {time2:.2f}s")
        if time2 < 0.2:
            print("\nRESULT: ✅ CACHE IS WORKING (Sub-200ms Hit)")
        else:
            print(f"\nRESULT: ❌ CACHE FAIL (Time: {time2:.2f}s)")
    except Exception as e:
        print(f"Run 2 Failed: {e}")

if __name__ == "__main__":
    # First, let's find the correct endpoint name
    test_cache()
