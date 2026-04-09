import sqlite3
import os

DB_PATH = "backend/data/raw/chembl/chembl_36_sqlite/chembl_36/chembl_36_sqlite/chembl_36.db"

def search_indications():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
        
    conn = sqlite3.connect(DB_PATH)
    q = "%Progeria%"
    q2 = "%Hutchinson-Gilford%"
    
    query = """
        SELECT DISTINCT md.pref_name, di.mesh_heading, di.max_phase_for_ind
        FROM drug_indication di
        JOIN molecule_dictionary md ON di.molregno = md.molregno
        WHERE di.mesh_heading LIKE ? OR di.mesh_heading LIKE ?
    """
    rows = conn.execute(query, (q, q2)).fetchall()
    print(f"Indicated Drugs for Progeria: {len(rows)}")
    for r in rows:
        print(f" - {r[0]} | Heading: {r[1]} | Phase: {r[2]}")
        
    conn.close()

if __name__ == "__main__":
    search_indications()
