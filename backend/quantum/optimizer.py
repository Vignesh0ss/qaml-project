"""
Quantum/classical optimizer: Simulated Annealing for QUBO. Optional D-Wave.
"""
import hashlib
import numpy as np
import random
import time
from typing import List, Tuple, Dict

# Try dimod for BQM; fallback to numpy SA
try:
    from dimod import BinaryQuadraticModel, SimulatedAnnealingSampler
    DIMOD_AVAILABLE = True
except ImportError:
    DIMOD_AVAILABLE = False


def _numpy_simulated_annealing(
    Q: np.ndarray,
    K: int,
    num_reads: int = 1,
    initial_temp: float = 100.0,
    final_temp: float = 0.01,
    cooling_rate: float = 0.95,
    seed: int | None = None,
) -> Tuple[List[int], float]:
    N = Q.shape[0]
    if N == 0: return [], 0.0
    
    # Use local RNGs for deterministic and thread-safe behavior.
    py_rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # Initialize random state with exactly K ones
    current = np.zeros(N)
    idx = np_rng.choice(N, min(K, N), replace=False)
    current[idx] = 1

    # O(1) Energy Gradient Tracking
    q_x = Q @ current
    current_e = float(current @ q_x)
    best_s = current.copy()
    best_e = current_e
    
    # Adaptive iterations based on N
    iter_per_temp = max(20, min(100, N * 2))
    temp = initial_temp
    start_time = time.time()
    
    while temp > final_temp:
        if time.time() - start_time > 5.0:
            break
        for _ in range(iter_per_temp):
            ones = np.where(current == 1)[0]
            zeros = np.where(current == 0)[0]
            
            if len(ones) > 0 and len(zeros) > 0:
                i = py_rng.choice(ones.tolist())
                j = py_rng.choice(zeros.tolist())
                
                # Delta = Q[j,j] + Q[i,i] - 2*Q[i,j] + 2*(q_x[j] - q_x[i])
                delta = Q[j, j] + Q[i, i] - 2 * Q[i, j] + 2 * (q_x[j] - q_x[i])
                
                if delta < 0 or (temp > 0 and py_rng.random() < np.exp(-delta / temp)):
                    q_x += Q[:, j] - Q[:, i]  # Fast O(N) Gradient Update
                    current[i] = 0
                    current[j] = 1
                    current_e += delta
                    
                    if current_e < best_e:
                        best_s = current.copy()
                        best_e = current_e
        
        temp *= cooling_rate
        
    selected = [i for i in range(N) if best_s[i] == 1]
    return selected, best_e


class QuantumOptimizer:
    def __init__(self, use_cloud: bool = False):
        self.use_cloud = use_cloud
        self.sampler = None
        if DIMOD_AVAILABLE and not use_cloud:
            self.sampler = SimulatedAnnealingSampler()

    def optimize(
        self,
        Q: Dict[tuple, float],
        K: int,
        num_reads: int = 1000,
        seed: int | None = None,
    ) -> Tuple[List[int], float]:
        N = max(max(i, j) for i, j in Q.keys()) + 1
        if DIMOD_AVAILABLE and self.sampler is not None:
            bqm = BinaryQuadraticModel.from_qubo(Q)
            response = self.sampler.sample(bqm, num_reads=num_reads)
            best = response.first
            selected = [i for i, v in best.sample.items() if v == 1]
            return selected, float(best.energy)
        # Fallback: build matrix and numpy SA
        Qmat = np.zeros((N, N))
        for (i, j), v in Q.items():
            Qmat[i, j] = Qmat[j, i] = v
        return _numpy_simulated_annealing(Qmat, K, num_reads=1, seed=seed)


def _stable_qubo_seed(Q: Dict[tuple, float], K: int) -> int:
    # Stable seed from sorted QUBO terms + K so equal inputs give equal outputs.
    items = sorted((int(i), int(j), float(v)) for (i, j), v in Q.items())
    material = f"K={int(K)}|terms={items}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def optimize_qubo(
    Q: Dict[tuple, float],
    K: int,
    num_reads: int = 50,
    seed: int | None = None,
) -> Tuple[List[int], float]:
    """Optimize QUBO using simulated annealing (fallback) or dimod."""
    opt = QuantumOptimizer(use_cloud=False)
    effective_seed = _stable_qubo_seed(Q, K) if seed is None else int(seed)
    return opt.optimize(Q, K, num_reads, seed=effective_seed)
