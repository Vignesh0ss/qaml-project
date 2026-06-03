"""
Experimental unknown-disease inference and weighted drug suggestion service.
Research-only mode.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.request
from typing import Any, Dict, List, Set, Tuple

def validate_experimental_payload(payload: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    symptoms = payload.get("symptoms") or []
    if not isinstance(symptoms, list) or not [s for s in symptoms if str(s).strip()]:
        raise ValueError("At least one symptom is required.")

    age = payload.get("age")
    if age is not None:
        a = _safe_float(age, -1)
        if a < 0 or a > 120:
            warnings.append("Age is outside expected range (0-120).")

    duration = payload.get("duration_days")
    if duration is not None:
        d = _safe_float(duration, -1)
        if d < 0:
            warnings.append("Duration days cannot be negative.")
        elif d > 3650:
            warnings.append("Duration days is very high; please verify units.")

    blood = (payload.get("lab_results") or {}).get("blood_test") or {}
    for k, v in blood.items():
        if v is None or (isinstance(v, str) and not str(v).strip()):
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv < 0:
            warnings.append(f"Lab value '{k}' is negative and may be invalid.")
    return warnings


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _normalize_probs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    total = sum(max(0.0, _safe_float(x.get("prob", 0.0))) for x in items)
    if total <= 0:
        n = max(1, len(items))
        out = []
        for x in items:
            disease = x.get("disease", "Unknown")
            out.append(
                {
                    "disease": disease,
                    "prob": round(1.0 / n, 4),
                    "recommended_drugs": [],
                }
            )
        return out
    out = []
    for x in items:
        disease = x.get("disease", "Unknown")
        out.append(
            {
                "disease": disease,
                "prob": round(max(0.0, _safe_float(x.get("prob", 0.0))) / total, 4),
                "recommended_drugs": [],
            }
        )
    return out


# Rule-based disease rows (symptoms + known gene associations). Used for classification and ChEMBL gene fallback.
EXPERIMENTAL_DISEASE_DB: List[Tuple[str, set[str], set[str]]] = [
    ("Sickle Cell Anemia", {"fatigue", "joint pain", "bone pain", "pale skin", "anemia"}, {"HBB"}),
    ("Thalassemia", {"fatigue", "pale skin", "weakness", "anemia"}, {"HBB"}),
    ("Progeria", {"growth delay", "hair loss", "skin tightening", "joint stiffness"}, {"LMNA", "ZMPSTE24"}),
    ("Huntington's disease", {"chorea", "memory loss", "behavioral changes", "motor issues"}, {"HTT"}),
    ("Iron Deficiency", {"fatigue", "dizziness", "pale skin", "weakness"}, set()),
]

DISEASE_FALLBACK_GENES: Dict[str, Set[str]] = {name: genes for name, _, genes in EXPERIMENTAL_DISEASE_DB}

# When ChEMBL is unavailable or mapping fails — literature-aligned placeholders (same spirit as pipeline fallbacks).
_STATIC_DISEASE_DRUGS: Dict[str, List[str]] = {
    "sickle cell anemia": ["Hydroxyurea", "Voxelotor", "L-Glutamine", "Crizanlizumab"],
    "thalassemia": ["Deferasirox", "Deferiprone", "Deferoxamine"],
    "iron deficiency": ["Ferrous sulfate", "Ferric carboxymaltose", "Iron sucrose"],
    "progeria": ["Lonafarnib", "Zoledronate", "Pravastatin"],
    "huntington": ["Tetrabenazine", "Deutetrabenazine", "Risperidone"],
}


def _static_drug_names_for_disease(canonical_name: str) -> List[str]:
    q = canonical_name.strip().lower()
    if "sickle" in q:
        return list(_STATIC_DISEASE_DRUGS["sickle cell anemia"])
    if "thalass" in q:
        return list(_STATIC_DISEASE_DRUGS["thalassemia"])
    if "iron" in q and "deficien" in q:
        return list(_STATIC_DISEASE_DRUGS["iron deficiency"])
    if "progeria" in q:
        return list(_STATIC_DISEASE_DRUGS["progeria"])
    if "huntington" in q:
        return list(_STATIC_DISEASE_DRUGS["huntington"])
    return []


def fetch_chembl_drug_names_for_disease(
    disease_name: str,
    fallback_genes: Set[str],
    limit: int = 8,
    existing_conn: sqlite3.Connection | None = None,
) -> List[str]:
    """
    Disease → ClinVar genes ∪ fallback genes → UniProt → ChEMBL TIDs → approved small-molecule drugs.
    No LLM calls; uses the same ChEMBL path as the main pipeline.
    """
    from app.services import pipeline as pl

    conn = existing_conn if existing_conn else pl._chembl_conn()
    if conn is None:
        return _static_drug_names_for_disease(disease_name)

    try:
        def _search():
            try:
                genes: Set[str] = set(pl.disease_to_genes(disease_name.lower()))
                genes |= set(fallback_genes)
                if not genes:
                    return None

                uniprots = pl.genes_to_uniprots(genes, conn)
                if not uniprots:
                    return None
                try:
                    tids = pl.uniprots_to_tids(uniprots, conn)
                except Exception:
                    return None
                if not tids:
                    return None
                drugs, _rej = pl.get_drugs_by_tids(tids, conn)
                seen: Set[str] = set()
                out: List[str] = []
                for d in drugs:
                    n = str(d.get("drug_name", "")).strip()
                    if not n:
                        continue
                    k = n.lower()
                    if k in seen:
                        continue
                    seen.add(k)
                    out.append(n)
                    if len(out) >= limit:
                        break
                return out
            except Exception:
                return None

        # Use a tight 3.0s timeout for experimental mode to keep response < 5s
        res = pl.run_with_timeout(_search, timeout=3.0, stage_name=f"ChEMBL-{disease_name}")
        return res if res else _static_drug_names_for_disease(disease_name)
    finally:
        if not existing_conn:
            try:
                conn.close()
            except Exception:
                pass


def attach_database_drug_recommendations(
    predictions: List[Dict[str, Any]],
    per_disease_k: int = 5,
) -> List[Dict[str, Any]]:
    """Attach per-disease drug name lists from ChEMBL (no AI)."""
    from app.services import pipeline as pl
    enriched: List[Dict[str, Any]] = []
    print(f"[Experimental] Enriching {len(predictions or [])} predictions with drugs...")
    conn = pl._chembl_conn()
    try:
        for p in predictions or []:
            disease = str(p.get("disease", "")).strip()
            fallback = DISEASE_FALLBACK_GENES.get(disease, set())
            print(f"[Experimental] Fetching drugs for {disease}...")
            start = time.time()
            names = fetch_chembl_drug_names_for_disease(
                disease, fallback, limit=per_disease_k, existing_conn=conn
            ) if disease else []
            print(f"[Experimental] Fetched {len(names)} drugs in {time.time()-start:.2f}s")
            item = dict(p)
            item["recommended_drugs"] = names
            enriched.append(item)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    return enriched


def format_experimental_summary_text(
    predictions: List[Dict[str, Any]],
    recommended_drugs: List[Dict[str, Any]],
) -> str:
    """Deterministic report text (no LLM)."""
    lines: List[str] = []
    lines.append(
        "Summary (database-backed experimental mode): disease probabilities come from symptom, gene, "
        "and lab heuristics; drug names come from ChEMBL via gene→target mapping where possible."
    )
    lines.append("")
    lines.append("Predicted diseases (relative weights):")
    for p in predictions[:6]:
        dn = str(p.get("disease", "Unknown"))
        prob = _safe_float(p.get("prob"), 0.0)
        lines.append(f"  • {dn}: {round(prob * 100, 1)}%")
    lines.append("")
    lines.append("Suggested drugs (merged across diseases; not prescribing advice):")
    for d in recommended_drugs[:8]:
        lines.append(
            f"  • {d.get('drug_name')} — score {d.get('final_score')} "
            f"({', '.join(d.get('source_diseases') or [])})"
        )
    lines.append("")
    lines.append("Caution: research prototype only; clinical validation required.")
    return "\n".join(lines)


def classify_unknown_disease(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    symptoms = {str(s).strip().lower() for s in (payload.get("symptoms") or []) if str(s).strip()}
    genes = {str(g).strip().upper() for g in (payload.get("gene_patterns") or []) if str(g).strip()}

    blood = (payload.get("lab_results") or {}).get("blood_test") or {}
    hb = _safe_float(blood.get("hemoglobin"), -1.0)
    wbc = _safe_float(blood.get("wbc"), -1.0)
    rbc_raw = blood.get("red_blood_cells") or blood.get("rbc")
    try:
        rbc = float(rbc_raw) if rbc_raw is not None and str(rbc_raw).strip() != "" else -1.0
    except (TypeError, ValueError):
        rbc = -1.0

    scored: List[Dict[str, Any]] = []
    for name, disease_symptoms, disease_genes in EXPERIMENTAL_DISEASE_DB:
        s_overlap = len(symptoms & disease_symptoms)
        s_score = s_overlap / max(1, len(disease_symptoms))
        g_score = 1.0 if (genes & disease_genes) else 0.0
        lab_score = 0.0
        if name in {"Sickle Cell Anemia", "Thalassemia", "Iron Deficiency"} and hb > 0:
            if hb < 9:
                lab_score += 0.9
            elif hb < 11:
                lab_score += 0.5
        if name == "Iron Deficiency" and wbc > 0:
            if 4000 <= wbc <= 11000:
                lab_score += 0.15
        if name in {"Sickle Cell Anemia", "Thalassemia", "Iron Deficiency"} and rbc > 0 and rbc < 4.0:
            lab_score += 0.4
        score = (0.6 * s_score) + (0.3 * g_score) + (0.1 * min(1.0, lab_score))
        scored.append({"disease": name, "prob": score})

    scored.sort(key=lambda x: x["prob"], reverse=True)
    top = scored[:3]
    return _normalize_probs(top)


def _gene_compatibility_boost(target_text: str, patient_genes: set[str]) -> float:
    t = (target_text or "").upper()
    if not patient_genes:
        return 0.0
    return 0.2 if any(g in t for g in patient_genes) else 0.05


def combine_weighted_drugs(
    predictions: List[Dict[str, Any]],
    per_disease_results: Dict[str, Dict[str, Any]],
    patient_genes: set[str],
) -> List[Dict[str, Any]]:
    combined: Dict[str, Dict[str, Any]] = {}
    for pred in predictions:
        disease = str(pred.get("disease", "Unknown"))
        prob = _safe_float(pred.get("prob"), 0.0)
        results = per_disease_results.get(disease, {})
        ranked = results.get("ranked_drugs") or []
        for d in ranked[:10]:
            name = str(d.get("drug_name") or d.get("target_name") or d.get("molregno") or "").strip()
            if not name:
                continue
            base_score = _safe_float(d.get("score"), 0.0)
            weighted = (prob * base_score) + _gene_compatibility_boost(str(d.get("target_name", "")), patient_genes)
            src = combined.setdefault(
                name,
                {
                    "drug_name": name,
                    "final_score": 0.0,
                    "source_diseases": set(),
                    "target": d.get("target_name", ""),
                    "confidence": "low",
                },
            )
            src["final_score"] += weighted
            src["source_diseases"].add(disease)
            target_type = str(d.get("target_type", "indirect")).lower()
            if target_type == "direct":
                src["confidence"] = "high"
            elif target_type == "pathway" and src["confidence"] != "high":
                src["confidence"] = "medium"

    out: List[Dict[str, Any]] = []
    for _, item in combined.items():
        out.append(
            {
                "drug_name": item["drug_name"],
                "final_score": round(float(item["final_score"]) * 0.8, 4),  # unknown-disease penalty
                "source_diseases": sorted(list(item["source_diseases"])),
                "target": item["target"],
                "confidence": item["confidence"].upper(),
            }
        )
    out.sort(key=lambda x: x["final_score"], reverse=True)
    return out[:10]


def generate_experimental_summary(
    predictions: List[Dict[str, Any]],
    recommended_drugs: List[Dict[str, Any]],
    experimental_api_key: str = "",
) -> str:
    key = (experimental_api_key or "").strip() or os.environ.get("EXPERIMENTAL_NVIDIA_NIM_API_KEY", "").strip() or os.environ.get("NVIDIA_NIM_API_KEY", "").strip()
    if not key:
        return "AI summary unavailable (missing experimental NVIDIA API key)."
    model = os.environ.get("EXPERIMENTAL_NVIDIA_NIM_MODEL", os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-405b-instruct"))
    prompt = (
        "You are a biomedical research assistant. This is experimental inference, not clinical advice.\n"
        f"Predicted diseases: {json.dumps(predictions)}\n"
        f"Recommended drugs: {json.dumps(recommended_drugs[:5])}\n"
        "Write a concise summary with: (1) why diseases were ranked, (2) why drugs were suggested, "
        "(3) one caution note. Keep under 180 words."
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.1,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    ssl_ctx = ssl._create_unverified_context()
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                text = re.sub(r"\s+", " ", str(text)).strip()
                if text:
                    return text
        except Exception as exc:
            last_exc = exc
            time.sleep(1.0 * (attempt + 1))
    return f"AI summary unavailable due to NVIDIA provider/network latency ({last_exc})."

