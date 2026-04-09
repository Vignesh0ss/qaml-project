"""Tests for QUBO builder."""
import numpy as np


def test_build_qubo():
    from quantum.qubo_builder import build_qubo
    scores = [0.8, 0.6, 0.4]
    overlap = np.zeros((3, 3))
    overlap[0, 1] = overlap[1, 0] = 0.5
    Q = build_qubo(scores, overlap, K=2, lam=0.5, mu=2.0)
    assert (0, 0) in Q
    assert (1, 1) in Q
    assert (0, 1) in Q
    assert Q[(0, 0)] < 0  # diagonal has -score term
    assert Q[(0, 1)] > 0  # off-diagonal penalty
