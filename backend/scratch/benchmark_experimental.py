import requests
import time
import json

BASE_URL = "http://localhost:5000/api/v1"

payload = {
    "age": 19,
    "gender": "male",
    "blood_group": "B+",
    "duration_days": 90,
    "symptoms": ["fever", "bleeding", "migrane"],
    "gene_patterns": ["HBB"],
    "lab_results": {
        "blood_test": {
            "hemoglobin": 6,
            "red_blood_cells": "4.45",
            "wbc": 15,
            "platelets": 8
        }
    },
    "notes": "Testing performance optimization"
}

def benchmark():
    print(f"Sending request to {BASE_URL}/experimental/suggest...")
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/experimental/suggest", json=payload, timeout=120)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Response received in {duration:.4f} seconds.")
        
        if response.status_code == 200:
            data = response.json()
            print("Status:", data.get("status"))
            print("Predicted Diseases:", [p["disease"] for p in data.get("predicted_diseases", [])])
            print("Number of Recommended Drugs:", len(data.get("recommended_drugs", [])))
            if duration < 5:
                print("SUCCESS: Performance requirement (< 5s) met.")
            else:
                print("FAILURE: Performance requirement NOT met.")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    benchmark()
