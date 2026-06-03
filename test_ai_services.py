# -*- coding: utf-8 -*-
"""
Quick diagnostic: test all AI services connectivity.
"""
import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

_SSL_CTX = ssl._create_unverified_context()

def _post(url, headers, payload, timeout=15):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, {"_error": body}

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── 1. NVIDIA NIM (LLaMA 3.1 405B) ──────────────────────────
sep("1. NVIDIA NIM - LLaMA 3.1 405B")
nim_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
nim_model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-405b-instruct")
print(f"   API Key: {'SET (' + nim_key[:12] + '...)' if nim_key else 'NOT SET [X]'}")
print(f"   Model:   {nim_model}")

if nim_key:
    t0 = time.time()
    code, result = _post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {nim_key}"},
        payload={
            "model": nim_model,
            "messages": [{"role": "user", "content": "Respond with exactly: OK"}],
            "max_tokens": 10,
            "temperature": 0.0,
        },
        timeout=30,
    )
    elapsed = time.time() - t0
    if code == 200:
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        print(f"   [OK] Response: \"{reply}\"  ({elapsed:.1f}s)")
    else:
        err_detail = result.get("_error", str(result))[:300]
        print(f"   [FAIL] HTTP {code}  ({elapsed:.1f}s)")
        print(f"   Detail: {err_detail}")
        # If 404 on model, try listing available models
        if code in (404, 400):
            print(f"   >> Model '{nim_model}' may be retired. Testing alternate models...")
            for alt in ["meta/llama-3.1-70b-instruct", "meta/llama-3.3-70b-instruct", "nvidia/llama-3.1-nemotron-70b-instruct"]:
                c2, r2 = _post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {nim_key}"},
                    payload={
                        "model": alt,
                        "messages": [{"role": "user", "content": "Respond with exactly: OK"}],
                        "max_tokens": 10,
                        "temperature": 0.0,
                    },
                    timeout=30,
                )
                status = "OK" if c2 == 200 else f"FAIL ({c2})"
                print(f"      {alt}: [{status}]")
                if c2 == 200:
                    reply = r2.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    print(f"      -> \"{reply}\"")
                    break
else:
    print("   [SKIP] No API key")

# ── 2. NVIDIA ESM2 (Protein embeddings) ─────────────────────
sep("2. NVIDIA ESM2 - Protein Embeddings")
esm2_endpoint = os.environ.get("NVIDIA_ESM2_ENDPOINT", "https://integrate.api.nvidia.com/v1/esm2-650m")
enable_esm2 = os.environ.get("ENABLE_ESM2", "true").lower() == "true"
print(f"   Enabled:  {enable_esm2}")
print(f"   Endpoint: {esm2_endpoint}")

if nim_key and enable_esm2:
    test_seq = "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT"
    t0 = time.time()
    code, result = _post(
        esm2_endpoint,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {nim_key}"},
        payload={"input": test_seq},
        timeout=15,
    )
    elapsed = time.time() - t0
    if code == 200:
        emb = None
        for candidate in [result.get("embedding"), result.get("embeddings"),
                          result.get("data", {}).get("embedding") if isinstance(result.get("data"), dict) else None]:
            if isinstance(candidate, list) and candidate:
                emb = candidate
                break
        if emb:
            dim = len(emb) if isinstance(emb[0], (int, float)) else f"nested ({len(emb)} items)"
            print(f"   [OK] Embedding received: dim={dim}  ({elapsed:.1f}s)")
        else:
            print(f"   [WARN] Response OK but no embedding found. Keys: {list(result.keys())}  ({elapsed:.1f}s)")
    else:
        err_detail = result.get("_error", str(result))[:300]
        print(f"   [FAIL] HTTP {code}  ({elapsed:.1f}s)")
        print(f"   Detail: {err_detail}")
else:
    print(f"   [SKIP] {'disabled' if not enable_esm2 else 'no API key'}")

# ── 3. Gemini AI ─────────────────────────────────────────────
sep("3. Google Gemini AI")
gemini_key = os.environ.get("GEMINI_API_KEY", "")
print(f"   API Key: {'SET (' + gemini_key[:12] + '...)' if gemini_key else 'NOT SET [X]'}")

if gemini_key:
    t0 = time.time()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    code, result = _post(
        url,
        headers={"Content-Type": "application/json"},
        payload={
            "contents": [{"parts": [{"text": "Respond with exactly: OK"}]}],
            "generationConfig": {"maxOutputTokens": 10, "temperature": 0.0}
        },
        timeout=15,
    )
    elapsed = time.time() - t0
    if code == 200:
        reply = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        print(f"   [OK] Response: \"{reply}\"  ({elapsed:.1f}s)")
    else:
        err_detail = result.get("_error", str(result))[:300]
        print(f"   [FAIL] HTTP {code}  ({elapsed:.1f}s)")
        print(f"   Detail: {err_detail}")
else:
    print("   [SKIP] No API key")

# ── 4. MongoDB ───────────────────────────────────────────────
sep("4. MongoDB")
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/quantum_drug_repurposing")
print(f"   URI: {mongo_uri}")
try:
    from pymongo import MongoClient
    t0 = time.time()
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    info = client.server_info()
    elapsed = time.time() - t0
    db = client.get_default_database()
    collections = db.list_collection_names()
    print(f"   [OK] Connected (v{info['version']})  ({elapsed:.1f}s)")
    print(f"   Collections: {collections}")
except Exception as exc:
    print(f"   [FAIL] {exc}")

# ── 5. ML Model ─────────────────────────────────────────────
sep("5. ML Model (joblib)")
ml_path = os.environ.get("ML_MODEL_PATH", "backend/ml/artifacts/model.joblib")
print(f"   Path: {ml_path}")
if os.path.isfile(ml_path):
    try:
        import joblib
        model = joblib.load(ml_path)
        print(f"   [OK] Model loaded: {type(model).__name__}")
    except Exception as exc:
        print(f"   [FAIL] {exc}")
else:
    print(f"   [WARN] File not found (fallback random scoring will be used)")

# ── Summary ──────────────────────────────────────────────────
sep("SUMMARY")
print("   All connectivity checks complete.\n")
