"""
QUBO matrix construction from ML relevance scores and overlap penalty.
minimize x^T Q x: diagonal = -scores + cardinality penalty; off-diagonal = overlap + 2*mu.
"""
import numpy as np
from typing import List, Dict


def build_qubo(
    scores: List[float],
    overlap: np.ndarray,
    K: int,
    lam: float = 0.5,
    mu: float = 2.0,
    penalties: List[float] = None,
) -> Dict[tuple, float]:
    """
    Build QUBO dict for dimod / simulated annealing.
    Q[(i,j)] for i<=j; diagonal terms (i,i), off-diagonal (i,j).

    penalties: optional per-candidate penalty (positive = discourage selection).
               Non-drug-like molecules should have a large positive penalty.
    """
    N = len(scores)
    if overlap.shape[0] != N or overlap.shape[1] != N:
        overlap = np.zeros((N, N))
    if penalties is None:
        penalties = [0.0] * N
    Q = {}
    for i in range(N):
        Q[(i, i)] = -scores[i] + mu * (1 - 2 * K) + penalties[i]
        for j in range(i + 1, N):
            Q[(i, j)] = lam * float(overlap[i, j]) + 2 * mu
    return Q



def build_qubo_matrix(scores: List[float], overlap: np.ndarray, K: int, lam: float = 0.5, mu: float = 2.0) -> np.ndarray:  # noqa: E501
    """Return full N x N symmetric matrix (for numpy-based solvers)."""
    N = len(scores)
    Q = np.zeros((N, N))
    for i in range(N):
        Q[i, i] = -scores[i] + mu * (1 - 2 * K)
        for j in range(i + 1, N):
            v = lam * float(overlap[i, j]) + 2 * mu
            Q[i, j] = Q[j, i] = v
    return Q
