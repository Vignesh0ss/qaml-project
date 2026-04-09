from pymongo import MongoClient
import json
import sys

def verify():
    client = MongoClient("mongodb://localhost:27017")
    db = client["quantum_drug_discovery"]
    task_id = "d3277021-5fed-49b3-95ce-e0d7dc713268"
    
    query_data = db["queries"].find_one({"task_id": task_id})
    if not query_data:
        print(f"Task {task_id} not found in database.")
        return

    print(f"Status: {query_data.get('status')}")
    results = query_data.get("results", {})
    ranked = results.get("ranked_drugs", [])
    
    print(f"Number of candidates: {len(ranked)}")
    for i, d in enumerate(ranked[:3]):
        print(f"{i+1}. {d.get('drug_name')} ({d.get('source')}) - {d.get('score')}")
        
    summary = results.get("ai_summary", "No summary found.")
    print("\n--- AI SUMMARY ---")
    print(summary[:1000])
    print("--- END ---")

if __name__ == "__main__":
    verify()
