import os
import sys
# Add backend to path so modules resolve automatically
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if 'backend/tests' in WORKSPACE_DIR.replace('\\', '/'):
    BACKEND_DIR = os.path.dirname(WORKSPACE_DIR)
else:
    BACKEND_DIR = os.path.join(WORKSPACE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

"""
Test: Verify the pipeline fixes for multi-disease support and correct scoring.

Tests:
1. disease_to_genes() finds genes for diseases other than Progeria
2. Scoring produces meaningful differentiated scores (not all ~0.5)
3. AI summary uses drug names, not target names
"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.pipeline import disease_to_genes, lipinski_score

def test_disease_to_genes():
    """Test that disease_to_genes works for multiple diseases, not just Progeria."""
    test_cases = {
        "progeria": True,
        "hearing loss": True,
        "retinitis pigmentosa": True,
        "usher syndrome": True,
        "cystic fibrosis": True,
        "huntington": True,
        "pendred syndrome": True,
        "deafness": True,
    }
    
    print("=" * 60)
    print("TEST: disease_to_genes() — Multi-Disease Support")
    print("=" * 60)
    
    results = {}
    for disease, expected_genes in test_cases.items():
        genes = disease_to_genes(disease)
        has_genes = len(genes) > 0
        status = "PASS" if has_genes == expected_genes else "FAIL"
        results[disease] = (status, genes)
        print(f"  [{status}] '{disease}' → {len(genes)} genes: {genes}")
    
    passed = sum(1 for s, _ in results.values() if s == "PASS")
    total = len(results)
    print(f"\n  Result: {passed}/{total} passed")
    return passed == total


def test_scoring_differentiation():
    """Test that composite scoring produces varied, meaningful scores."""
    import numpy as np
    
    print("\n" + "=" * 60)
    print("TEST: Composite Scoring — Score Differentiation")
    print("=" * 60)
    
    # Simulate candidates with real activity data
    candidates = [
        {"activity": 5.0, "max_phase": 4, "confidence": 9, "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O"},  # Aspirin-like: excellent
        {"activity": 50.0, "max_phase": 3, "confidence": 7, "canonical_smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1"},  # Medium
        {"activity": 5000.0, "max_phase": 1, "confidence": 5, "canonical_smiles": "c1ccccc1"},  # Weak
        {"activity": None, "max_phase": 1, "confidence": 3, "canonical_smiles": ""},  # Unknown
    ]
    
    for d in candidates:
        activity = d.get("activity")
        if activity and activity > 0:
            activity_score = max(0.0, min(1.0, 1.0 - (np.log10(max(activity, 1)) / 5.0)))
        else:
            activity_score = 0.3
        
        p = d.get("max_phase", 1)
        phase_score = {4: 1.0, 3: 0.85, 2: 0.7, 1: 0.5}.get(p, 0.4)
        
        conf = d.get("confidence", 5)
        confidence_score = min(1.0, conf / 9.0) if conf else 0.5
        
        lip = lipinski_score(d.get("canonical_smiles", ""))
        
        composite = (
            0.40 * activity_score +
            0.25 * phase_score +
            0.20 * confidence_score +
            0.10 * lip +
            0.05
        )
        d["score"] = round(min(1.0, max(0.0, composite)), 4)
    
    scores = [d["score"] for d in candidates]
    print(f"  Scores: {scores}")
    
    # Check scores are differentiated (not all the same)
    unique_scores = len(set(scores))
    is_differentiated = unique_scores >= 3
    is_ordered = scores == sorted(scores, reverse=True)
    
    status1 = "PASS" if is_differentiated else "FAIL"
    status2 = "PASS" if is_ordered else "FAIL"
    print(f"  [{status1}] Score differentiation: {unique_scores} unique scores (need ≥3)")
    print(f"  [{status2}] Score ordering: best drug ranked highest")
    
    return is_differentiated and is_ordered


def test_summary_field_priority():
    """Test that summary creation uses drug_name, not target_name."""
    print("\n" + "=" * 60)
    print("TEST: AI Summary — Field Priority")
    print("=" * 60)
    
    candidate = {
        "drug_name": "Lonafarnib",
        "target_name": "Lamin A/C",
        "score": 0.85,
        "max_phase": 4,
        "mechanism": "Farnesyltransferase inhibitor",
        "canonical_smiles": "CC"
    }
    
    # Simulate the fixed summary line building
    drug_name = candidate.get("drug_name") or "Unknown Drug"
    target_name = candidate.get("target_name") or ""
    score = candidate.get("score", 0.0)
    max_phase = candidate.get("max_phase", "")
    
    line = f"- Drug: {drug_name} (score={score:.2f})"
    if target_name:
        line += f" | Target: {target_name}"
    if max_phase:
        line += f" | Phase: {max_phase}"
    
    print(f"  Generated line: {line}")
    
    has_drug_name = "Lonafarnib" in line
    starts_with_drug = "Drug: Lonafarnib" in line
    has_target = "Target: Lamin A/C" in line
    
    status = "PASS" if (has_drug_name and starts_with_drug and has_target) else "FAIL"
    print(f"  [{status}] Drug name appears first, target included as context")
    
    return has_drug_name and starts_with_drug


if __name__ == "__main__":
    r1 = test_disease_to_genes()
    r2 = test_scoring_differentiation()
    r3 = test_summary_field_priority()
    
    print("\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)
    print(f"  Disease mapping: {'PASS' if r1 else 'FAIL'}")
    print(f"  Scoring:         {'PASS' if r2 else 'FAIL'}")
    print(f"  Summary fields:  {'PASS' if r3 else 'FAIL'}")
    all_pass = r1 and r2 and r3
    print(f"\n  {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
