import re

with open('backend/app/services/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''def load_candidates(disease_name: str = "", max_drugs: int = 300, allowed_targets=None):
    import csv, numpy as np
    drugs, scores, smiles_list = [], [], []
    
    if not BINDING_CSV.is_file():
        return drugs, np.array(scores), smiles_list

    with open(BINDING_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        count = 0
        for row in r:
            if count >= max_drugs:
                break
                
            target_name = row.get("target_name", "").lower()
            smiles = row.get("canonical_smiles", "").lower()
            
            # Dynamic Target Overlap Filtering natively at the DB load scope
            if allowed_targets:
                if not any(t in target_name or t in smiles for t in allowed_targets):
                    continue
            
            molregno = row.get("molregno", "")
            sc_raw = row.get("standard_value", "0")
            try:
                sc = float(sc_raw) if sc_raw and str(sc_raw).strip() else 0.0
            except:
                sc = 0.0
                
            if not is_drug_like(smiles, molregno=molregno, drug_name=target_name):
                continue
                
            drugs.append({
                "molregno": molregno,
                "canonical_smiles": smiles,
                "standard_value": str(sc),
                "target_name": row.get("target_name", ""),
                "target_chembl_id": row.get("target_chembl_id", "")
            })
            scores.append(sc)
            smiles_list.append(smiles)
            count += 1
            
    return drugs, np.array(scores), smiles_list
'''

# Regex to safely replace the old load_candidates completely up to get_overlap_matrix
content = re.sub(r'def load_candidates\(.*?\n\n\ndef get_overlap_matrix\(', new_func + '\n\ndef get_overlap_matrix(', content, flags=re.DOTALL)

with open('backend/app/services/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Pipeline loader rewritten to strictly use BINDING_CSV.")
