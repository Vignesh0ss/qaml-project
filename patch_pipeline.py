import re, os

FILE = 'backend/app/services/pipeline.py'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

new_proc = '''def run_pipeline(
    task_id: str,
    query: Dict[str, Any],
    db=None,
) -> Dict[str, Any]:
    disease_name = query.get("disease_name", "")
    requested_disease_name = disease_name
    top_k = int(query.get("top_k", 5))
    top_k = max(1, min(50, top_k))
    user_id = query.get("user_id")

    # 1) Disease Mapping (Stage 1 AI)
    gemini_recognised: dict = {}
    disease_targets = {
        "als": ["sod1", "tdp-43", "fus"],
        "dyslexia": ["dcdc2", "kiaa0319", "robo1"],
    }
    allowed_targets = disease_targets.get(disease_name.lower(), [])

    try:
        from app.services.gemini_service import recognize_disease
        gemini_recognised = recognize_disease(disease_name)
        canonical = gemini_recognised.get("disease") or disease_name
        if canonical and canonical.lower() != disease_name.lower():
            print(f"[Pipeline] Gemini mapped '{disease_name}' -> '{canonical}'")
            disease_name = canonical
        
        # Task 3: Combine manual disease mapping with AI extracted targets
        if "key_targets" in gemini_recognised:
            for t in gemini_recognised["key_targets"]:
                if isinstance(t, str):
                    allowed_targets.append(t.lower())
    except Exception as _ge:
        print(f"[Pipeline] Gemini disease recognition skipped: {_ge}")

    # 2) Load Candidates (Filtered DB)
    drugs, scores, smiles_list = load_candidates(disease_name=disease_name, max_drugs=300)
    if not drugs:
        raise RuntimeError(f"No scientifically valid candidates found in databases for '{disease_name}'. Upstream filtering or data source missing.")

    # 3) Pre-Validation (STRICT) & Disease Target Filtering
    rejected_drugs = []
    valid_candidates = []
    valid_scores = []
    valid_smiles = []

    for idx, d in enumerate(drugs):
        name = d.get("target_name", "").lower()
        smiles = d.get("canonical_smiles", "").lower()
        
        is_radiopharm = "technetium" in name or "tc-99" in name or "[99tc]" in smiles or "radio" in name
        is_inorganic = "talc" in name or "silicate" in name or "silodrate" in name or "almasilate" in name or (len(smiles) < 5 and "c" not in smiles)
        has_known_target = bool(d.get("target_chembl_id") or name)
        
        # Base validation check
        passes_drug_like = is_drug_like(smiles, molregno=d.get("molregno"), drug_name=name)

        is_valid = True
        reason = ""
        
        if is_radiopharm:
            is_valid, reason = False, "Diagnostic / Radiopharmaceutical"
        elif is_inorganic or not passes_drug_like:
            is_valid, reason = False, "Inorganic, Metal, or Non-Therapeutic compound"
        elif not has_known_target:
            is_valid, reason = False, "Unknown biological target"
        elif allowed_targets:
            # Check overlap
            overlap = any(t in name or t in smiles for t in allowed_targets)
            if not overlap:
                is_valid, reason = False, "No known relevance to disease targets"
        
        # Task 7: Debug Logging
        if is_valid:
            print(f"[DEBUG] {{\"name\": \"{name}\", \"is_valid\": True, \"target_overlap\": True}}")
            valid_candidates.append(d)
            valid_scores.append(scores[idx])
            valid_smiles.append(smiles)
        else:
            print(f"[DEBUG] {{\"name\": \"{name}\", \"is_valid\": False, \"reason\": \"{reason}\"}}")
            rejected_drugs.append({
                "molregno": d.get("molregno"),
                "name": name,
                "reason": reason
            })

    # Abort if less than top_k valid candidates (Task 2 & 5)
    if len(valid_candidates) < top_k:
        early_res =  {
            "task_id": task_id,
            "disease_name": requested_disease_name,
            "message": "No valid drug repurposing candidates found",
            "reason": "No biologically relevant drugs passed filtering",
            "rejected_drugs": rejected_drugs
        }
        if db is not None:
            db["results"].insert_one(early_res)
            db["queries"].update_one({"task_id": task_id}, {"": {"status": "done"}})
        return early_res

    drugs = valid_candidates
    scores = np.array(valid_scores)
    smiles_list = valid_smiles
    N = len(drugs)

    # 4) QUBO Optimization
    relevance = (scores - scores.min()) / (scores.max() - scores.min()) if scores.max() > scores.min() else np.ones(N) * 0.5
    relevance = np.clip(relevance, 0.05, 0.95)
    relevance = 0.10 + relevance * 0.75
    relevance_list = [round(float(v), 2) for v in relevance]

    overlap_mat = get_overlap_matrix(smiles_list, size=N)
    drug_penalties = [0.0] * N  # Since all remaining are pre-validated, no strict penalties needed here

    from quantum.qubo_builder import build_qubo
    from quantum.optimizer import optimize_qubo
    Q = build_qubo(relevance_list, overlap_mat, K=top_k, penalties=drug_penalties)
    selected_idx, energy = optimize_qubo(Q, K=top_k, num_reads=250)

    # 5) Post-Validation (Rank selected candidates)
    ranked = []
    for r, idx in enumerate(selected_idx):
        idx = int(idx)
        if idx < len(drugs):
            d = dict(drugs[idx])
            d["rank"] = r + 1
            d["score"] = relevance_list[idx]
            ranked.append(d)

    # 6) AI Explanation
    gemini_summary = ""
    try:
        from app.services.gemini_service import generate_medical_summary
        gemini_summary = generate_medical_summary(disease_name, ranked, gemini_powered=False)
    except Exception as _gs:
        print(f"[Pipeline] Gemini summary skipped: {_gs}")
        gemini_summary = f"AI summary generation failed: {_gs}"

    results = {
        "task_id": task_id,
        "disease_name": requested_disease_name,
        "disease_info": gemini_recognised,
        "top_k": top_k,
        "qubo_energy": float(energy),
        "ranked_drugs": ranked,
        "rejected_drugs": rejected_drugs,
        "gemini_summary": gemini_summary,
        "gemini_powered": False,
        "model_version": "pipeline_v2",
    }

    if db is not None:
        from app.services.audit_service import log
        log(db, task_id, "PIPELINE_COMPLETE", inputs=query, outputs=results, user_id=user_id, model_version="pipeline_v2")
        db["results"].insert_one(results)
        db["queries"].update_one({"task_id": task_id}, {"": {"status": "done"}})

    return results
'''

# Standard regex replacement
content = re.sub(r'def run_pipeline\(.*?return results', new_proc, content, flags=re.DOTALL)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print('Success.')
