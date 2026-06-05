import sqlite3
import os
import re
import csv
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHEMBL_DB_PATH = BASE_DIR / "backend" / "data" / "raw" / "chembl" / "chembl_36_sqlite" / "chembl_36" / "chembl_36_sqlite" / "chembl_36.db"
MOCK_DB_PATH = BASE_DIR / "backend" / "app" / "services" / "mock_chembl.db"
GOLD_SET_TSV = BASE_DIR / "backend" / "data" / "processed" / "clinvar_gold_set.tsv"

print(f"ChEMBL DB Path: {CHEMBL_DB_PATH}")
print(f"Mock DB Path: {MOCK_DB_PATH}")
print(f"Gold Set TSV: {GOLD_SET_TSV}")

if not CHEMBL_DB_PATH.exists():
    print("Error: Source ChEMBL database not found!")
    exit(1)

# List of genes from DISEASE_TARGET_MAP
DISEASE_GENES = {
    # Progeria
    "LMNA", "ZMPSTE24", "FARNESYLTRANSFERASE", "FARNESYL-TRANSFERASE", "PROTEIN FARNESYLTRANSFERASE",
    "PRELAMIN", "PROGERIN", "LAMIN A", "LAMIN-A", "LAMIN C",
    "MTOR", "AKT", "PI3K", "PI 3-KINASE", "AUTOPHAGY", "MEK", "ERK", "AMPK",
    # Huntington
    "HTT", "SLC18A2", "DRD2", "DOPAMINE", "NMDA", "BDNF",
    # Covid
    "ACE2", "TMPRSS2", "CTSL", "IL6", "JAK", "STAT", "INTERFERON",
    # Sickle cell
    "HBB", "HBF", "BCL11A", "NITRIC OXIDE", "NOS", "HEMOGLOBIN"
}

# Add genes from ClinVar for relevant keywords
keywords = {"progeria", "huntington", "covid", "corona", "sickle"}
if GOLD_SET_TSV.exists():
    try:
        with open(GOLD_SET_TSV, "r", encoding="utf-8-sig") as f:
            r = csv.DictReader(f, delimiter="\t")
            for row in r:
                phenos = str(row.get("PhenotypeList", "")).lower()
                gene = str(row.get("GeneSymbol", "")).strip().upper()
                if not gene:
                    continue
                # If any keyword matches phenotype
                if any(kw in phenos for kw in keywords):
                    DISEASE_GENES.add(gene)
    except Exception as e:
        print(f"Error reading gold set TSV: {e}")

print(f"Total genes of interest: {len(DISEASE_GENES)}")
print(f"Genes: {sorted(list(DISEASE_GENES))}")

# Connect to source
src_conn = sqlite3.connect(CHEMBL_DB_PATH)
src_cursor = src_conn.cursor()

# Remove mock DB if exists to start fresh
if MOCK_DB_PATH.exists():
    os.remove(MOCK_DB_PATH)

# Connect to destination
dst_conn = sqlite3.connect(MOCK_DB_PATH)
dst_cursor = dst_conn.cursor()

# Helper to copy table schema and insert rows
def copy_table_data(table_name, select_query, params=()):
    # Get table schema
    src_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    create_sql = src_cursor.fetchone()[0]
    
    # Create table in destination
    dst_cursor.execute(create_sql)
    
    # Fetch rows from source
    src_cursor.execute(select_query, params)
    rows = src_cursor.fetchall()
    
    if not rows:
        print(f"Table {table_name}: 0 rows copied")
        return []
    
    # Insert into destination
    placeholders = ",".join(["?"] * len(rows[0]))
    dst_cursor.executemany(f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})", rows)
    dst_conn.commit()
    print(f"Table {table_name}: {len(rows)} rows copied")
    return rows

# 1. Copy component_synonyms for genes of interest
genes_list = list(DISEASE_GENES)
placeholders = ",".join(["?"] * len(genes_list))
syn_rows = copy_table_data(
    "component_synonyms",
    f"SELECT * FROM component_synonyms WHERE UPPER(component_synonym) IN ({placeholders}) AND syn_type = 'GENE_SYMBOL'",
    [g.upper() for g in genes_list]
)

# Extract component IDs
component_ids = list(set(r[1] for r in syn_rows))
print(f"Unique component IDs: {len(component_ids)}")

if not component_ids:
    print("Error: No component IDs found for genes!")
    exit(1)

# 2. Copy component_sequences for these component IDs
comp_placeholders = ",".join(["?"] * len(component_ids))
seq_rows = copy_table_data(
    "component_sequences",
    f"SELECT * FROM component_sequences WHERE component_id IN ({comp_placeholders})",
    component_ids
)

# Extract UniProt accessions
uniprots = list(set(r[1] for r in seq_rows if r[1]))
print(f"Unique UniProt accessions: {len(uniprots)}")

# 3. Copy target_components linking component_id to tid
tc_rows = copy_table_data(
    "target_components",
    f"SELECT * FROM target_components WHERE component_id IN ({comp_placeholders})",
    component_ids
)

tids = list(set(r[0] for r in tc_rows))
print(f"Unique target IDs (tids): {len(tids)}")

if not tids:
    print("Error: No target IDs found!")
    exit(1)

# 4. Copy target_dictionary for these tids
tids_placeholders = ",".join(["?"] * len(tids))
td_rows = copy_table_data(
    "target_dictionary",
    f"SELECT * FROM target_dictionary WHERE tid IN ({tids_placeholders})",
    tids
)

# 5. Copy assays for these tids
assay_rows = copy_table_data(
    "assays",
    f"SELECT * FROM assays WHERE tid IN ({tids_placeholders})",
    tids
)

assay_ids = list(set(r[0] for r in assay_rows))
print(f"Unique assay IDs: {len(assay_ids)}")

if not assay_ids:
    print("Warning: No assays found for target IDs!")

# 6. Copy activities for these assays
# Let's filter to keep the database size small: standard_type IN ('IC50', 'Ki', 'EC50', 'Kd') and standard_value > 0
activity_rows = []
if assay_ids:
    # Batch query in chunks of 999 to avoid SQLite limits if there are many assays
    chunk_size = 950
    for i in range(0, len(assay_ids), chunk_size):
        chunk = assay_ids[i:i+chunk_size]
        chunk_placeholders = ",".join(["?"] * len(chunk))
        src_cursor.execute(
            f"SELECT * FROM activities WHERE assay_id IN ({chunk_placeholders}) AND standard_type IN ('IC50', 'Ki', 'EC50', 'Kd') AND standard_value > 0",
            chunk
        )
        activity_rows.extend(src_cursor.fetchall())
    
    # Create activities table
    src_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activities'")
    create_sql = src_cursor.fetchone()[0]
    dst_cursor.execute(create_sql)
    
    if activity_rows:
        placeholders = ",".join(["?"] * len(activity_rows[0]))
        dst_cursor.executemany(f"INSERT OR IGNORE INTO activities VALUES ({placeholders})", activity_rows)
        dst_conn.commit()
    print(f"Table activities: {len(activity_rows)} rows copied")

# Extract molregnos from activities
molregnos = list(set(r[2] for r in activity_rows))
print(f"Unique molregnos: {len(molregnos)}")

# 7. Copy molecule_dictionary for these molregnos (with max_phase >= 1 and molecule_type = 'Small molecule')
mol_rows = []
if molregnos:
    chunk_size = 950
    for i in range(0, len(molregnos), chunk_size):
        chunk = molregnos[i:i+chunk_size]
        chunk_placeholders = ",".join(["?"] * len(chunk))
        src_cursor.execute(
            f"SELECT * FROM molecule_dictionary WHERE molregno IN ({chunk_placeholders}) AND molecule_type = 'Small molecule' AND max_phase >= 1",
            chunk
        )
        mol_rows.extend(src_cursor.fetchall())
        
    src_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='molecule_dictionary'")
    create_sql = src_cursor.fetchone()[0]
    dst_cursor.execute(create_sql)
    
    if mol_rows:
        placeholders = ",".join(["?"] * len(mol_rows[0]))
        dst_cursor.executemany(f"INSERT OR IGNORE INTO molecule_dictionary VALUES ({placeholders})", mol_rows)
        dst_conn.commit()
    print(f"Table molecule_dictionary: {len(mol_rows)} rows copied")

# Update list of molregnos to only keep the small molecule, max_phase >= 1 ones
filtered_molregnos = list(set(r[0] for r in mol_rows))
print(f"Filtered molregnos (small mol & phase >= 1): {len(filtered_molregnos)}")

# 8. Copy compound_structures for the filtered molregnos
struct_rows = []
if filtered_molregnos:
    chunk_size = 950
    for i in range(0, len(filtered_molregnos), chunk_size):
        chunk = filtered_molregnos[i:i+chunk_size]
        chunk_placeholders = ",".join(["?"] * len(chunk))
        src_cursor.execute(
            f"SELECT * FROM compound_structures WHERE molregno IN ({chunk_placeholders}) AND canonical_smiles IS NOT NULL",
            chunk
        )
        struct_rows.extend(src_cursor.fetchall())
        
    src_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='compound_structures'")
    create_sql = src_cursor.fetchone()[0]
    dst_cursor.execute(create_sql)
    
    if struct_rows:
        placeholders = ",".join(["?"] * len(struct_rows[0]))
        dst_cursor.executemany(f"INSERT OR IGNORE INTO compound_structures VALUES ({placeholders})", struct_rows)
        dst_conn.commit()
    print(f"Table compound_structures: {len(struct_rows)} rows copied")

# 9. Copy component_class for family expansion
class_rows = []
if component_ids:
    chunk_size = 950
    for i in range(0, len(component_ids), chunk_size):
        chunk = component_ids[i:i+chunk_size]
        chunk_placeholders = ",".join(["?"] * len(chunk))
        src_cursor.execute(
            f"SELECT * FROM component_class WHERE component_id IN ({chunk_placeholders})",
            chunk
        )
        class_rows.extend(src_cursor.fetchall())
        
    src_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='component_class'")
    create_sql = src_cursor.fetchone()[0]
    dst_cursor.execute(create_sql)
    
    if class_rows:
        placeholders = ",".join(["?"] * len(class_rows[0]))
        dst_cursor.executemany(f"INSERT OR IGNORE INTO component_class VALUES ({placeholders})", class_rows)
        dst_conn.commit()
    print(f"Table component_class: {len(class_rows)} rows copied")

# Get protein class IDs for family expansion
class_ids = list(set(r[1] for r in class_rows if r[1]))
print(f"Protein class IDs: {class_ids}")

# Fetch target components in the same family, and their targets & assays
family_tids = []
if class_ids:
    class_placeholders = ",".join(["?"] * len(class_ids))
    src_cursor.execute(
        f"""
        SELECT DISTINCT tc.tid, tc.component_id, cc.protein_class_id
        FROM target_components tc
        JOIN component_class cc ON tc.component_id = cc.component_id
        WHERE cc.protein_class_id IN ({class_placeholders})
        """,
        class_ids
    )
    fam_tc_results = src_cursor.fetchall()
    
    # Insert extra target_components and component_class rows for family members
    for row in fam_tc_results:
        dst_cursor.execute("INSERT OR IGNORE INTO target_components (tid, component_id) VALUES (?, ?)", (row[0], row[1]))
        dst_cursor.execute("INSERT OR IGNORE INTO component_class (component_id, protein_class_id) VALUES (?, ?)", (row[1], row[2]))
        family_tids.append(row[0])
    dst_conn.commit()
    
    family_tids = list(set(family_tids))
    print(f"Unique family tids: {len(family_tids)}")
    
    # Copy target_dictionary rows for family tids
    fam_tids_to_copy = [tid for tid in family_tids if tid not in tids]
    if fam_tids_to_copy:
        chunk_size = 950
        for i in range(0, len(fam_tids_to_copy), chunk_size):
            chunk = fam_tids_to_copy[i:i+chunk_size]
            chunk_placeholders = ",".join(["?"] * len(chunk))
            src_cursor.execute(f"SELECT * FROM target_dictionary WHERE tid IN ({chunk_placeholders})", chunk)
            f_td_rows = src_cursor.fetchall()
            if f_td_rows:
                placeholders = ",".join(["?"] * len(f_td_rows[0]))
                dst_cursor.executemany(f"INSERT OR IGNORE INTO target_dictionary VALUES ({placeholders})", f_td_rows)
        dst_conn.commit()
        print(f"Copied {len(fam_tids_to_copy)} family target_dictionary rows")

# Close connections
src_conn.close()
dst_conn.close()

print(f"Mock DB generation completed successfully. Size: {os.path.getsize(MOCK_DB_PATH) / 1024 / 1024:.2f} MB")
