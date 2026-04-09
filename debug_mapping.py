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
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline import disease_to_genes, genes_to_uniprots, uniprots_to_tids, get_drugs_by_tids

print("--- Testing Pipeline v3: Progeria ---")

db_path = r'c:\Users\vvign\OneDrive\Documents\Desktop\Projects\Project-QAML\quantum-drug-repurposing\backend\data\raw\chembl\chembl_36_sqlite\chembl_36\chembl_36_sqlite\chembl_36.db'
conn = sqlite3.connect(db_path)

try:
    # 1. Genes
    genes = disease_to_genes('Progeria')
    print(f"Genes: {genes}")
    
    # 2. UniProts
    uniprots = genes_to_uniprots(genes, conn)
    print(f"UniProts: {uniprots}")
    
    # 3. TIDs
    tids = uniprots_to_tids(uniprots, conn)
    print(f"TIDs: {tids}")
    
    # 4. Direct drugs
    drugs = get_drugs_by_tids(tids, conn)
    print(f"Direct drugs found: {len(drugs)}")
    
    # 5. Check families if directly 0
    if not drugs:
        print("Searching for Target Family fallback...")
        ph = ",".join("?" * len(tids))
        classes = conn.execute(f"SELECT DISTINCT cc.l1, cc.l2 FROM component_class cc JOIN target_components tc ON cc.component_id = tc.component_id WHERE tc.tid IN ({ph})", tuple(tids)).fetchall()
        print(f"Classes for LMNA TIDs: {classes}")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
finally:
    conn.close()
