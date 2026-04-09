import sqlite3, csv, sys

db = 'backend/data/raw/chembl/chembl_36_sqlite/chembl_36/chembl_36_sqlite/chembl_36.db'
conn = sqlite3.connect(db)

# molecule_dictionary columns
cols = [c[1] for c in conn.execute('PRAGMA table_info(molecule_dictionary)').fetchall()]
sys.stdout.write("mol_dict cols: " + str(cols) + "\n")

# phase stats
p4 = conn.execute("SELECT COUNT(*) FROM molecule_dictionary WHERE molecule_type='Small molecule' AND max_phase=4").fetchone()[0]
p2 = conn.execute("SELECT COUNT(*) FROM molecule_dictionary WHERE molecule_type='Small molecule' AND max_phase>=2").fetchone()[0]
sys.stdout.write(f"Phase-4 approved: {p4}, Phase-2+: {p2}\n")

# progeria-linked targets via LMNA gene
tgts = conn.execute("""
    SELECT DISTINCT t.pref_name, t.tid FROM target_dictionary t
    JOIN target_components tc ON t.tid = tc.tid
    JOIN component_synonyms cs ON tc.component_id = cs.component_id
    WHERE LOWER(cs.component_synonym) IN ('lmna','hgps','lamin a')
    LIMIT 10
""").fetchall()
sys.stdout.write("Progeria targets: " + str(tgts) + "\n")

# drugs hitting those targets
if tgts:
    tids = tuple(t[1] for t in tgts)
    pholder = ",".join("?"*len(tids))
    drugs = conn.execute(f"""
        SELECT md.pref_name, md.molregno, md.max_phase, md.molecule_type, cs2.canonical_smiles
        FROM molecule_dictionary md
        JOIN activities a ON md.molregno = a.molregno
        JOIN assays ass ON a.assay_id = ass.assay_id
        LEFT JOIN compound_structures cs2 ON md.molregno = cs2.molregno
        WHERE ass.tid IN ({pholder})
        AND md.molecule_type = 'Small molecule'
        AND md.max_phase >= 1
        LIMIT 10
    """, tids).fetchall()
    sys.stdout.write("Drugs targeting LMNA: " + str(drugs) + "\n")

conn.close()

# binding CSV
with open('backend/data/processed/chembl_binding_scores.csv', encoding='utf-8') as f:
    br = list(csv.DictReader(f))
sys.stdout.write(f"Binding CSV: {len(br)} rows, cols={list(br[0].keys())}\n")
sys.stdout.write(f"Binding row0: {dict(br[0])}\n")

# DrugBank CSV
with open('backend/data/processed/drugbank_drug_smiles.csv', encoding='utf-8') as f:
    dr = list(csv.DictReader(f))
sys.stdout.write(f"DrugBank CSV: {len(dr)} rows, cols={list(dr[0].keys())}\n")
sys.stdout.write(f"DrugBank row0: {dict(dr[0])}\n")

sys.stdout.flush()
