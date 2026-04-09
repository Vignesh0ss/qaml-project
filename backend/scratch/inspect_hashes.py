from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def inspect_hashes():
    client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    db = client[os.environ.get("MONGODB_DB", "quantum_drug_repurposing")]
    users = db["users"]
    
    print(f"Total users: {users.count_documents({})}")
    for user in users.find():
        ph = user.get("password_hash", "")
        prefix = ph[:10] if ph else "NONE"
        print(f"User: {user.get('username')} | Hash Prefix: {prefix} | Length: {len(ph)}")

if __name__ == "__main__":
    inspect_hashes()
