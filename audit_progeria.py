import sqlite3
import os
import sys
from pathlib import Path

DB_PATH = "backend/data/raw/chembl/chembl_36_sqlite/chembl_36/chembl_36_sqlite/chembl_36.db"

def audit_progeria():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
        
    conn = sqlite3.connect(DB_PATH)
    # Progeria mapping (LMNA -> P02545 -> TID 103668)
    tid = 103668 
    
    print(f"Auditing TID {tid} (LMNA)")
    
    # 1. Get drugs for this TID
    query = """
        SELECT md.pref_name, md.max_phase, md.molecule_type, td.pref_name
        FROM molecule_dictionary md
        JOIN activities a ON md.molregno = a.molregno
        JOIN assays ass ON a.assay_id = ass.assay_id
        JOIN target_dictionary td ON ass.tid = td.tid
        WHERE ass.tid = 103668
        AND md.molecule_type = 'Small molecule'
        AND md.max_phase >= 1
    """
    rows = conn.execute(query).fetchall()
    print(f"Direct Drugs (Small Molecule, Ph >= 1): {len(rows)}")
    for r in rows:
        print(f" - {r[0]} | Phase: {r[1]} | Target: {r[3]}")
    
    # 2. Check Target Family (Expansion)
    query_fam = """
        SELECT cc.protein_class_id
        FROM component_class cc
        JOIN target_components tc ON cc.component_id = tc.component_id
        WHERE tc.tid = 103668
    """
    pc_ids = [r[0] for r in conn.execute(query_fam).fetchall()]
    print(f"\nProtein Class IDs for LMNA: {pc_ids}")
    
    if pc_ids:
        ph = ",".join("?" * len(pc_ids))
        query_pool = f"""
            SELECT DISTINCT md.pref_name, md.max_phase, td.pref_name
            FROM molecule_dictionary md
            JOIN activities a ON md.molregno = a.molregno
            JOIN assays ass ON a.assay_id = ass.assay_id
            JOIN target_dictionary td ON ass.tid = td.tid
            JOIN target_components tc ON td.tid = tc.tid
            JOIN component_class cc ON tc.component_id = cc.component_id
            WHERE cc.protein_class_id IN ({ph})
            AND md.molecule_type = 'Small molecule'
            AND md.max_phase >= 1
            LIMIT 20
        """
        rows_pool = conn.execute(query_pool, pc_ids).fetchall()
        print(f"\nSample of Expanded Pool ({len(rows_pool)} shown):")
        for r in rows_pool:
            print(f" - {r[0]} | Phase: {r[1]} | Target: {r[2]}")

    conn.close()

if __name__ == "__main__":
    audit_progeria()
