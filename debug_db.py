from pymongo import MongoClient
import json
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["quantum_drug_repurposing"]

print("--- RECENT QUERIES ---")
for q in db["queries"].find().sort("created_at", -1).limit(5):
    # Remove ObjectId for printing
    q["_id"] = str(q["_id"])
    print(json.dumps(q, indent=2))

print("\n--- RECENT RESULTS ---")
for r in db["results"].find().sort("_id", -1).limit(5):
    r["_id"] = str(r["_id"])
    # Truncate ranked_drugs for brevity
    if "ranked_drugs" in r:
        r["ranked_drugs"] = f"{len(r['ranked_drugs'])} drugs"
    print(json.dumps(r, indent=2))
