import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline import run_pipeline

print("--- Testing Pipeline v3: Progeria ---")

query = {"disease_name": "Progeria", "top_k": 10}
task_id = "test_123"

try:
    result = run_pipeline(task_id, query)
    drugs = result.get("ranked_drugs", [])
    print(f"DONE. Found {len(drugs)} candidates.")
    
    # 1. No proteins
    proteins = [d['drug_name'] for d in drugs if any(p in d['drug_name'].lower() for p in ['mtor', 'pi3k', 'kinase', 'protein', 'complex'])]
    if proteins:
        print(f"FAILURE: Proteins found in drug list: {proteins}")
    else:
        print("SUCCESS: No proteins found.")

    # 2. No duplicates
    molregnos = [d.get("molregno") for d in drugs]
    if len(molregnos) != len(set(molregnos)):
        print("FAILURE: Duplicates found.")
    else:
        print("SUCCESS: No duplicates found.")

    # 3. Confidence labels
    if all('confidence_label' in d for d in drugs):
        print("SUCCESS: All drugs have confidence labels.")
    else:
        print("FAILURE: Some drugs are missing confidence labels.")

    # 4. Phase and identifiers
    print("\n--- Top 2 Candidates ---")
    for d in drugs[:2]:
        print(f"Name: {d['drug_name']}")
        print(f"Rank: {d['rank']}")
        print(f"Phase: {d['max_phase']}")
        print(f"Confidence: {d['confidence_label']}")
        print(f"Reasoning: {d['reasoning']}")
        print("-" * 20)

except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
