import sys
sys.path.insert(0, './backend')
from app.services.pipeline import run_pipeline

q = {"disease_name": "Usher syndrome", "top_k": 5}
res = run_pipeline("test-123", q)
print("\nPipeline Result:")
for drug in res["ranked_drugs"]:
    print(f"Rank {drug['rank']}: Target - {drug['target_name']} | Score: {drug['score']}")
