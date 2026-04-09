import os
import sys
# Add backend to path so modules resolve automatically
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if 'backend/tests' in WORKSPACE_DIR.replace('\\', '/'):
    BACKEND_DIR = os.path.dirname(WORKSPACE_DIR)
else:
    BACKEND_DIR = os.path.join(WORKSPACE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import sys
sys.path.insert(0, './backend')
import traceback
from app.services.audit_service import log

try:
    log(None, "t_id", "TEST", {"in": 1}, {"out": {"a": [1,2,3]}})
    print("Log call to None DB passed (no exception)")
    
    from pymongo import MongoClient
    db = MongoClient("mongodb://localhost:27017/")["quantum_drug_repurposing"]
    import numpy as np
    
    inputs = {"test": np.float64(1.5), "arr": np.array([1, 2, 3])}
    out = log(db, "t_id", "TEST_NP", inputs, inputs)
    print(f"Log call with Numpy output: {out}")
except:
    traceback.print_exc()
