import csv

cnt = 0
matches = []
with open('./backend/data/processed/chembl_binding_scores.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if "corona" in row.get("target_name", "").lower() or "covid" in row.get("target_name", "").lower() or "sars" in row.get("target_name", "").lower():
            matches.append(row["target_name"])
            cnt += 1

print(f"Total matching target_names: {cnt}")
if matches:
    print("Example matches:", list(set(matches))[:10])
