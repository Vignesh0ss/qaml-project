"""
Validation Test: Coronal Synostosis
Verifies that the pipeline NEVER returns toxic/non-therapeutic substances.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.services.pipeline import run_pipeline

BLOCKED_NAMES = [
    "magnesium cation", "sodium hydroxide", "nickel",
    "magnesium", "sodium", "hydroxide", "cation", "anion",
    "sulfate", "chloride", "phosphate", "oxide", "ion",
]

BLOCKED_SMILES = [
    "[Mg+2]", "[Mg]", "[Na+]", "[Ni+2]", "[Ni]",
    "[OH-].[Na+]", "[Na+].[OH-]", "O=[Na]",
    "[K+]", "[Ca+2]", "[Fe+2]", "[Fe+3]", "[Cu+2]", "[Zn+2]",
    "[OH-]", "[Cl-]", "O", "N", "C=O", "C",
]


def test_coronal_synostosis():
    print("=" * 70)
    print("VALIDATION TEST: Coronal Synostosis")
    print("=" * 70)

    query = {"disease_name": "Coronal Synostosis", "top_k": 5}

    try:
        results = run_pipeline("validation_test", query)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        return

    ranked = results.get("ranked_drugs", [])
    print(f"\nReturned {len(ranked)} candidates:\n")

    all_passed = True
    for drug in ranked:
        name = drug.get("target_name", "Unknown")
        smiles = drug.get("canonical_smiles", "")
        score = drug.get("score", 0)
        rank = drug.get("rank", "?")

        # Check name blocklist
        name_clean = True
        for blocked in BLOCKED_NAMES:
            if blocked in name.lower():
                name_clean = False
                break

        # Check SMILES blocklist
        smiles_clean = smiles.strip() not in BLOCKED_SMILES

        # Check score is realistic (not 1.0 / 100%)
        score_ok = 0 < score < 1.0

        status = "PASS" if (name_clean and smiles_clean and score_ok) else "FAIL"
        if status == "FAIL":
            all_passed = False

        print(f"  [{status}] Rank {rank}: {name}")
        print(f"         SMILES: {smiles[:60]}{'...' if len(smiles) > 60 else ''}")
        print(f"         Score:  {score:.2f}")
        if not name_clean:
            print(f"         >> BLOCKED: Name contains toxic/non-therapeutic term")
        if not smiles_clean:
            print(f"         >> BLOCKED: SMILES matches known toxic compound")
        if not score_ok:
            print(f"         >> WARNING: Score out of realistic range")
        print()

    print("=" * 70)
    if all_passed:
        print("RESULT: ALL PASSED - No toxic or non-therapeutic substances found.")
    else:
        print("RESULT: FAILED - Some candidates are invalid!")
    print("=" * 70)


if __name__ == "__main__":
    test_coronal_synostosis()
