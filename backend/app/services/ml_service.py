"""
ML inference: score drug-gene relevance. Uses cached model or fallback scores.
"""
import os
import json
import hashlib
import numpy as np
from typing import List, Optional, Dict, Any
from .audit_service import AuditLogger

# Optional: joblib model, Redis cache
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


class MLService:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.version = "0.0.0"
        if model_path and os.path.isfile(model_path) and JOBLIB_AVAILABLE:
            try:
                self.model = joblib.load(model_path)
                self.version = getattr(self.model, "version", "1.0")
            except Exception:
                pass

    def score_drugs(
        self,
        task_id: str,
        gene_vec: np.ndarray,
        drug_fingerprints: List[np.ndarray],
        redis_client=None,
        db=None,
    ) -> List[float]:
        # FR-ML-06: Log ML_INFERENCE_START
        AuditLogger.log(db, task_id, "ML_INFERENCE_START", {"gene_vec_sum": float(np.sum(gene_vec))}, {})

        cache_key = None
        if redis_client and gene_vec is not None:
            try:
                cache_key = "infer:" + hashlib.sha256(
                    json.dumps({"g": gene_vec.tolist()}, sort_keys=True).encode()
                ).hexdigest()
                cached = redis_client.get(cache_key)
                if cached:
                    scores = json.loads(cached)
                    AuditLogger.log(db, task_id, "ML_INFERENCE_COMPLETE", {"cache": "HIT"}, {"score_count": len(scores)})
                    return scores
            except Exception:
                pass

        if self.model is not None and gene_vec is not None and drug_fingerprints:
            try:
                # FR-ML-02: Enforce 2548-dim (500 + 2048)
                X = []
                for fp in drug_fingerprints:
                    # Pad or truncate to ensure dimensions
                    g = gene_vec[:500] if len(gene_vec) >= 500 else np.pad(gene_vec, (0, 500 - len(gene_vec)))
                    d = fp[:2048] if len(fp) >= 2048 else np.pad(fp, (0, 2048 - len(fp)))
                    X.append(np.concatenate([g, d]))
                
                X = np.array(X)
                if X.shape[1] != 2548:
                    raise ValueError(f"Feature vector dimension mismatch: expected 2548, got {X.shape[1]}")
                
                scores = self.model.predict_proba(X)[:, 1].tolist()
            except Exception as e:
                print(f"[MLService] Error: {e}")
                scores = [0.5] * len(drug_fingerprints)
        else:
            # Fallback
            n = len(drug_fingerprints) if drug_fingerprints else 10
            np.random.seed(42)
            scores = (np.random.rand(n) * 0.3 + 0.4).tolist()

        if redis_client and cache_key and scores:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(scores))
            except Exception:
                pass
        
        # FR-ML-06: Log ML_INFERENCE_COMPLETE
        AuditLogger.log(db, task_id, "ML_INFERENCE_COMPLETE", {"cache": "MISS"}, {"score_count": len(scores)})
        return scores
