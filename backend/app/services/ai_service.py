"""
NVIDIA-only AI service for drug repurposing intelligence.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.request
from typing import Any, Dict, List

_NVIDIA_NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
_NVIDIA_NIM_MODEL = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-405b-instruct")

_SSL_CTX = ssl._create_unverified_context()


def _external_ai_enabled() -> bool:
    try:
        from flask import current_app
        if current_app:
            return bool(current_app.config.get("EXTERNAL_AI_ENABLED", True))
    except Exception:
        pass
    return os.environ.get("EXTERNAL_AI_ENABLED", "true").lower() == "true"


def _get_nim_key() -> str:
    try:
        from flask import current_app
        key = current_app.config.get("NVIDIA_NIM_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return _NVIDIA_NIM_API_KEY


def _get_nim_model() -> str:
    try:
        from flask import current_app
        model = current_app.config.get("NVIDIA_NIM_MODEL", "")
        if model:
            return model
    except Exception:
        pass
    return _NVIDIA_NIM_MODEL


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 10) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json_with_retry(
    url: str,
    headers: dict,
    payload: dict,
    timeout: int = 10,
    retries: int = 2,
    backoff_sec: float = 1.0,
) -> dict:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return _post_json(url, headers=headers, payload=payload, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt >= retries:
                break
            time.sleep(backoff_sec * (attempt + 1))
    raise RuntimeError(f"NVIDIA NIM API error: {last_exc}")


def _generate(
    prompt: str,
    *,
    max_tokens: int = 2048,
    timeout: int = 25,
    retries: int = 2,
) -> str:
    if not _external_ai_enabled():
        raise RuntimeError("External AI is disabled for this environment")
    key = _get_nim_key()
    if not key:
        raise RuntimeError("NVIDIA_NIM_API_KEY not set")
    model = _get_nim_model()
    result = _post_json_with_retry(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        payload={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        },
        timeout=timeout,
        retries=retries,
        backoff_sec=1.5,
    )
    return result["choices"][0]["message"]["content"].strip()


_RECOGNIZE_CACHE: Dict[str, Dict[str, Any]] = {}
_GENE_CACHE: Dict[str, List[str]] = {}
_SUMMARY_CACHE: Dict[str, str] = {}


def recognize_disease(user_input: str) -> Dict[str, Any]:
    user_input_clean = user_input.strip().lower()
    cache_key = f"v2:{user_input_clean}"
    if cache_key in _RECOGNIZE_CACHE:
        return _RECOGNIZE_CACHE[cache_key]
    prompt = f"""You are STAGE 1: Disease Understanding Engine.
Convert input disease to canonical name and return strict JSON.
Include 3-8 HGNC gene symbols most relevant to this disease (genes array) so downstream mapping does not need a second model call.
{{
  "disease": "Canonical disease name",
  "icd_code": "Code",
  "genes": ["GENE1", "GENE2"],
  "key_targets": ["Target1", "Target2"],
  "pathways": ["Pathway1", "Pathway2"],
  "formal_description": "A 2-sentence formal biomedical definition."
}}
User Input: "{user_input}"
"""
    try:
        text = _generate(prompt, max_tokens=768, timeout=9, retries=1)
        text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text)
        result = json.loads(text)
        if not isinstance(result, dict):
            return {
                "disease": user_input,
                "icd_code": "",
                "genes": [],
                "key_targets": [],
                "pathways": [],
                "formal_description": "",
            }
        raw_genes = result.get("genes", [])
        if isinstance(raw_genes, list):
            result["genes"] = [g.strip().upper() for g in raw_genes if isinstance(g, str) and g.strip()]
        else:
            result["genes"] = []
        _RECOGNIZE_CACHE[cache_key] = result
        return result
    except Exception as exc:
        return {
            "disease": user_input,
            "icd_code": "",
            "genes": [],
            "key_targets": [],
            "pathways": [],
            "_error": str(exc),
        }


def generate_ai_candidates(disease_name: str) -> List[Dict[str, Any]]:
    if not _external_ai_enabled():
        return []
    prompt = f"""Identify drug repurposing candidates for: {disease_name}
Return strict JSON:
{{
  "candidates": [
    {{
      "drug_name": "Drug Name",
      "molregno": "CHEMBL_ID_OR_NULL",
      "max_phase": 4,
      "mechanism": "Mechanism of Action",
      "canonical_smiles": "SMILES_IF_KNOWN_OR_EMPTY",
      "target_name": "Biological Target",
      "confidence": 0.95,
      "reasoning": "Brief clinical rationale"
    }}
  ]
}}
"""
    try:
        text = _generate(prompt)
        text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)
        if not isinstance(data, dict):
            return []
        candidates = data.get("candidates", [])
        for c in candidates:
            c["source"] = "nvidia_ai"
            c["evidence_level"] = "AI-Predicted (External Knowledge)"
            c["score"] = c.get("confidence", 0.7)
        return candidates
    except Exception as exc:
        print(f"[AIService] AI candidate generation failed: {exc}")
        return []


def ai_disease_to_genes(disease_name: str) -> List[str]:
    disease_key = disease_name.strip().lower()
    if disease_key in _GENE_CACHE:
        return _GENE_CACHE[disease_key]
    if not _external_ai_enabled():
        return []
    prompt = f"""Given disease: {disease_name}
Return strict JSON:
{{
  "genes": ["GENE1", "GENE2", "GENE3"],
  "rationale": "Brief explanation of gene-disease connection"
}}
Only official HGNC symbols.
"""
    try:
        text = _generate(prompt)
        text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)
        genes = data.get("genes", [])
        if not isinstance(genes, list):
            genes = []
        genes = [g.strip().upper() for g in genes if isinstance(g, str) and g.strip()]
        _GENE_CACHE[disease_key] = genes
        return genes
    except Exception as exc:
        print(f"[AIService] AI gene discovery failed: {exc}")
        return []


def generate_medical_summary(disease_name: str, top_candidates: List[Dict[str, Any]], ai_powered: bool = False) -> str:
    candidate_names = sorted([(c.get("drug_name") or c.get("target_name") or "Unknown") for c in top_candidates[:5]])
    cache_key = f"v2:{disease_name.lower()}:{'|'.join(candidate_names)}"
    if cache_key in _SUMMARY_CACHE:
        return _SUMMARY_CACHE[cache_key]

    candidate_lines = []
    for candidate in top_candidates[:5]:
        drug_name = candidate.get("drug_name") or "Unknown Drug"
        target_name = candidate.get("target_name") or ""
        mechanism = candidate.get("mechanism", "")
        score = candidate.get("score", 0.0)
        candidate_lines.append(f"- Drug: {drug_name} (score={score:.2f}) | Target: {target_name} | Mechanism: {mechanism}")

    source_note = (
        "Note: local disease mapping was sparse, so candidates include NVIDIA AI-assisted suggestions.\n\n"
        if ai_powered
        else ""
    )

    prompt = f"""Validate and summarize these candidates for the user's disease query: "{disease_name}".
Return strict JSON:
{{
  "validated_candidates": [{{"drug_name":"","status":"VALID | REJECTED","reason":"","approval_status":"","targets":[],"mechanism":"","disease_relevance":"","confidence":"High | Moderate | Low"}}],
  "summary": {{
    "total_input": 0,
    "valid_count": 0,
    "rejected_count": 0,
    "query_analysis": "3-6 sentences: how this query/disease relates to the candidate list, what the pipeline scores imply, and limitations (not clinical advice).",
    "notes": "Optional extra caveats, conflicts, or follow-up study ideas."
  }}
}}
Candidates:
{chr(10).join(candidate_lines)}
"""
    try:
        res = _generate(prompt)
        text = re.sub(r"^```[a-z]*\n?", "", res.strip(), flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)
        if isinstance(data, dict):
            summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
            validated = data.get("validated_candidates", [])
            if not isinstance(validated, list):
                validated = []

            parts: List[str] = []
            if source_note.strip():
                parts.append(source_note.strip())

            parts.append(f"Query / disease focus: {disease_name}")

            qa = str(summary.get("query_analysis", "") or "").strip()
            if qa:
                parts.append(qa)

            if validated:
                parts.append("Per-candidate review:")
                for vc in validated[:8]:
                    if not isinstance(vc, dict):
                        continue
                    dn = str(vc.get("drug_name", "") or "Unknown").strip()
                    st = str(vc.get("status", "") or "").strip()
                    reason = str(vc.get("reason", "") or "").strip()
                    rel = str(vc.get("disease_relevance", "") or "").strip()
                    conf = str(vc.get("confidence", "") or "").strip()
                    mech = str(vc.get("mechanism", "") or "").strip()
                    line_bits = [f"• {dn} — {st}"]
                    if conf:
                        line_bits[0] += f" (confidence: {conf})"
                    parts.append(" ".join(line_bits))
                    detail_lines = []
                    if rel:
                        detail_lines.append(f"  Relevance: {rel}")
                    if mech:
                        detail_lines.append(f"  Mechanism: {mech}")
                    if reason:
                        detail_lines.append(f"  Rationale: {reason}")
                    parts.extend(detail_lines)

            notes = str(summary.get("notes", "") or "").strip()
            if notes and notes.lower() != qa.lower():
                parts.append(f"Additional notes: {notes}")

            ti = summary.get("total_input", 0)
            vc = summary.get("valid_count", 0)
            rc = summary.get("rejected_count", 0)
            parts.append(
                f"Validation summary: {vc} accepted, {rc} rejected, from {ti} candidates reviewed."
            )
            final_summary = "\n\n".join(parts).strip()
        else:
            final_summary = source_note + text if source_note else text
        _SUMMARY_CACHE[cache_key] = final_summary
        return final_summary
    except Exception as exc:
        print(f"[AIService] Medical summary generation failed: {exc}")
        fallback = (
            "AI summary is temporarily unavailable due to NVIDIA provider/network latency. "
            "Pipeline results remain valid; please retry summary generation shortly."
        )
        _SUMMARY_CACHE[cache_key] = fallback
        return fallback
