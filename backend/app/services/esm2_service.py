"""
NVIDIA ESM2 embedding service.

Used in backend scoring to add protein-level similarity features.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.request
from typing import List, Optional

_SSL_CTX = ssl._create_unverified_context()

_DEFAULT_ENDPOINT = "https://integrate.api.nvidia.com/v1/esm2-650m"
_DEFAULT_TIMEOUT = 10
_EMBED_CACHE: dict[str, List[float]] = {}


def _get_env(name: str, default: str = "") -> str:
    try:
        from flask import current_app

        value = current_app.config.get(name)
        if value not in (None, ""):
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def _enabled() -> bool:
    return _get_env("ENABLE_ESM2", "true").lower() == "true"


def _api_key() -> str:
    return _get_env("NVIDIA_NIM_API_KEY", "")


def _endpoint() -> str:
    return _get_env("NVIDIA_ESM2_ENDPOINT", _DEFAULT_ENDPOINT)


def _timeout() -> int:
    raw = _get_env("NVIDIA_ESM2_TIMEOUT", str(_DEFAULT_TIMEOUT))
    try:
        return max(3, int(raw))
    except Exception:
        return _DEFAULT_TIMEOUT


def _post_json(url: str, headers: dict, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_embedding(data: dict) -> Optional[List[float]]:
    # Accept a few common response shapes.
    candidates = [
        data.get("embedding"),
        data.get("embeddings"),
        data.get("data", {}).get("embedding") if isinstance(data.get("data"), dict) else None,
        data.get("output", {}).get("embedding") if isinstance(data.get("output"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, list) and candidate and isinstance(candidate[0], (int, float)):
            return [float(x) for x in candidate]
    return None


def embed_protein_sequence(sequence: str, retries: int = 1) -> Optional[List[float]]:
    """
    Returns ESM2 embedding for a protein sequence or None on failure.
    """
    if not _enabled():
        return None
    key = _api_key()
    if not key:
        return None
    sequence = (sequence or "").strip().upper()
    if len(sequence) < 20:
        return None
    cached = _EMBED_CACHE.get(sequence)
    if cached:
        return cached

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"input": sequence}
    timeout = _timeout()

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            data = _post_json(_endpoint(), headers=headers, payload=payload, timeout=timeout)
            emb = _extract_embedding(data)
            if emb:
                _EMBED_CACHE[sequence] = emb
                return emb
            return None
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    print(f"[ESM2] embedding failed: {last_exc}")
    return None

