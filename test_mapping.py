import sqlite3
import csv
import sys
import os

clinvar_path = "backend/data/processed/clinvar_gold_set.tsv"

def test(disease_name):
    genes = set()
    with open(clinvar_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if disease_name.lower() in str(row.get("PhenotypeList", "")).lower():
                genes.add(row.get("GeneSymbol", ""))

    print(f"Genes for '{disease_name}': {genes}")
    if not genes: return

    db_path = os.path.abspath("backend/data/raw/chembl/chembl_36_sqlite/chembl_36/chembl_36_sqlite/chembl_36.db")
    
    # Path manipulation for sqlite URI on Windows requires forward slashes
    db_uri_path = db_path.replace("\\", "/")
    # Add leading slash for URI if it's absolute on Windows e.g., /C:/path
    if not db_uri_path.startswith('/'):
        db_uri_path = '/' + db_uri_path
        
    uri = f"file:{db_uri_path}?mode=ro"
    
    print(f"Connecting to {uri}")
    conn = sqlite3.connect(uri, uri=True)
    placeholders = ", ".join("?" * len(genes))
    query = """
    SELECT DISTINCT t.pref_name AS target_name
    FROM target_dictionary t 
    JOIN target_components tc ON t.tid = tc.tid
    JOIN component_synonyms csyn ON tc.component_id = csyn.component_id
    WHERE csyn.component_synonym IN (""" + placeholders + """)
    """
    rows = conn.execute(query, tuple(genes)).fetchall()
    print(f"Targets from ChEMBL: {[r[0] for r in rows]}")

test("Usher syndrome")
