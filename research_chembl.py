import sqlite3
import os

db_path = r'c:\Users\vvign\OneDrive\Documents\Desktop\Projects\Project-QAML\quantum-drug-repurposing\backend\data\raw\chembl\chembl_36_sqlite\chembl_36\chembl_36_sqlite\chembl_36.db'
if not os.path.exists(db_path):
    # Try alternate path if first one fails
    db_path = r'backend\data\raw\chembl\chembl_36_sqlite\chembl_36\chembl_36_sqlite\chembl_36.db'
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_columns(table):
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

tables = ['target_dictionary', 'target_components', 'component_sequences', 'assays', 'component_synonyms']
for t in tables:
    try:
        print(f"--- Table: {t} ---")
        print(f"Columns: {get_columns(t)}")
        # Sample row
        res = cursor.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
        print(f"Sample row: {res}")
    except Exception as e:
        print(f"Error reading {t}: {e}")

# UniProt search
print("\n--- UniProt check ---")
try:
    cols = get_columns('component_sequences')
    if 'accession' in cols:
        print("Columns: ", cols)
        sample = cursor.execute("SELECT accession FROM component_sequences WHERE accession IS NOT NULL LIMIT 5").fetchall()
        print(f"Sample accessions (UniProt?): {sample}")
except:
    pass

# Confidence score check
print("\n--- Assays confidence score check ---")
try:
    cols = get_columns('assays')
    if 'confidence_score' in cols:
        print("Found confidence_score in assays.")
        sample = cursor.execute("SELECT confidence_score, count(*) FROM assays GROUP BY confidence_score LIMIT 10").fetchall()
        print(f"Confidence score distribution: {sample}")
except:
    pass

# Target families/classifications
print("\n--- Target families check ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%family%' OR name LIKE '%class%')")
family_tables = [r[0] for r in cursor.fetchall()]
print(f"Found family/class tables: {family_tables}")
for ft in family_tables:
    try:
        print(f"--- {ft} ---")
        print(get_columns(ft))
        res = cursor.execute(f"SELECT * FROM {ft} LIMIT 1").fetchone()
        print(f"Sample row: {res}")
    except Exception as e:
        print(f"Error: {e}")

conn.close()
