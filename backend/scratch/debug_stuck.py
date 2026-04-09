from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def check_stuck_tasks():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["quantum_drug_repurposing"]
    
    print("--- QUERY STATUS AUDIT ---")
    queries = list(db["queries"].find().sort("created_at", -1).limit(3))
    for q in queries:
        print(f"Task: {q.get('task_id')} | Status: {q.get('status')} | Error: {q.get('error')}")
    
    print("\n--- RESULTS AUDIT ---")
    results = list(db["results"].find().sort("created_at", -1).limit(3))
    for r in results:
        print(f"Result for: {r.get('disease_name')} | TaskID: {r.get('task_id')}")

if __name__ == "__main__":
    check_stuck_tasks()
