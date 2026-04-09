import re
with open('backend/app/services/pipeline.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'def load_candidates(disease_name: str, max_drugs: int = 150) -> Tuple[List[Dict[str, Any]], np.ndarray, List[str]]:',
    'def load_candidates(disease_name: str, max_drugs: int = 150, allowed_targets=None) -> Tuple[List[Dict[str, Any]], np.ndarray, List[str]]:'
)

old_loop = '''    if BINDING_CSV.is_file():
        with open(BINDING_CSV, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for i, row in enumerate(r):
                if i >= max_drugs:
                    break'''

new_loop = '''    if BINDING_CSV.is_file():
        with open(BINDING_CSV, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            count = 0
            for row in r:
                if count >= max_drugs:
                    break
                target_name = row.get("target_name", "").lower()
                smiles = row.get("canonical_smiles", "").lower()
                if allowed_targets and not any(t in target_name or t in smiles for t in allowed_targets):
                    continue
                count += 1'''

code = code.replace(old_loop, new_loop)

with open('backend/app/services/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patched.")
