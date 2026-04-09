import pymongo
import json
from bson import json_util

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["quantum_drug_repurposing"]

latest_query = db["queries"].find().sort("_id", -1).limit(1)
for q in latest_query:
    print("----- LATEST QUERY -----")
    print(json.dumps(q, default=json_util.default, indent=2))
    
    task_id = q.get("task_id")
    print(f"\n----- RESULTS for {task_id} -----")
    res = db["results"].find_one({"task_id": task_id})
    if res:
        print(json.dumps(res, default=json_util.default, indent=2)[:1000] + "...")
    else:
        print("No results found.")
        
    print(f"\n----- AUDIT TRAIL for {task_id} -----")
    audits = db["audit_trail"].find({"task_id": task_id})
    for a in audits:
        print(json.dumps(a, default=json_util.default, indent=2))
