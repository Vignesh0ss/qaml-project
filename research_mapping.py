import sqlite3
import os

db_path = r'c:\Users\vvign\OneDrive\Documents\Desktop\Projects\Project-QAML\quantum-drug-repurposing\backend\data\raw\chembl\chembl_36_sqlite\chembl_36\chembl_36_sqlite\chembl_36.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Map Gene Symbol to UniProt Accession
gene_symbol = 'LMNA' # Progeria associated gene
print(f"--- Mapping Gene: {gene_symbol} ---")
cursor.execute("""
    SELECT DISTINCT cs.accession, cs.description, cs.component_id
    FROM component_sequences cs
    JOIN component_synonyms syn ON cs.component_id = syn.component_id
    WHERE UPPER(syn.component_synonym) = ?
    AND syn.syn_type = 'GENE_SYMBOL'
""", (gene_symbol,))
res = cursor.fetchall()
print(f"UniProt Accessions for {gene_symbol}: {res}")

# 2. Map UniProt Accession to ChEMBL Target ID (TID)
if res:
    accession = res[0][0]
    print(f"\n--- Mapping UniProt: {accession} to TID ---")
    cursor.execute("""
        SELECT DISTINCT td.tid, td.pref_name, td.target_type
        FROM target_dictionary td
        JOIN target_components tc ON td.tid = tc.tid
        JOIN component_sequences cs ON tc.component_id = cs.component_id
        WHERE cs.accession = ?
    """, (accession,))
    res_tid = cursor.fetchall()
    print(f"ChEMBL TIDs for {accession}: {res_tid}")

# 3. Check Target Confidence Score distribution in assays for a specific TID
if res_tid:
    tid = res_tid[0][0]
    print(f"\n--- Assays for TID {tid} ---")
    cursor.execute("""
        SELECT confidence_score, count(*)
        FROM assays
        WHERE tid = ?
        GROUP BY confidence_score
    """, (tid,))
    print(f"Assay Confidence Distribution: {cursor.fetchall()}")

# 4. Target Hierarchy (Family)
print("\n--- Target Hierarchy for TID ---")
if res_tid:
    tid = res_tid[0][0]
    # Check if target_hierarchy exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='target_hierarchy'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM target_hierarchy WHERE tid = ?", (tid,))
        print(f"Hierarchy for TID {tid}: {cursor.fetchall()}")

conn.close()
