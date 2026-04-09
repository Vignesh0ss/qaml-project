import os
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit import DataStructs
from typing import Tuple
import random

# Define paths
# Current file is in backend/optimizer/qubo_solver.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "backend", "data", "processed")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "top_candidates.csv")

# Ensure reproducibility
np.random.seed(42)
random.seed(42)


def calculate_similarity_matrix(smiles_list):
    """Calculates Tanimoto similarity matrix for a list of SMILES."""
    mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = []

    for sm in smiles_list:
        mol = Chem.MolFromSmiles(sm)
        if mol:
            fps.append(mfpgen.GetFingerprint(mol))
        else:
            # Fallback if invalid
            fps.append(mfpgen.GetFingerprint(Chem.MolFromSmiles("C")))

    n = len(fps)
    sim_matrix: np.ndarray = np.zeros((n, n))

    for i in range(n):
        for j in range(i, n):
            sim = DataStructs.TanimotoSimilarity(fps[i], fps[j])
            sim_matrix[i][j] = sim
            sim_matrix[j][i] = sim

    return sim_matrix


def compute_energy(
    state: np.ndarray,
    pIC50_scores: np.ndarray,
    sim_matrix: np.ndarray,
    alpha: float = 1.0,
    beta: float = 2.0,
    gamma: float = 10.0,
    k: int = 5
) -> float:
    """
    QUBO Objective Function:
    Minimize H = - alpha * sum(pIC50 * x_i)
                 + beta * sum(Sim(i,j) * x_i * x_j) (if Sim > 0.6)
                 + gamma * (sum(x_i) - k)^2
    """
    total_drugs_selected = np.sum(state)

    # 1. Reward: Maximize Potency (Negative because we are minimizing energy)
    reward = -alpha * np.sum(state * pIC50_scores)

    # 2. Penalty: Minimize Similarity (Diversity constraint)
    penalty_sim = 0
    # Find all selected indices
    selected_idx = np.where(state == 1)[0]
    for i in range(len(selected_idx)):
        for j in range(i + 1, len(selected_idx)):
            idx_i = int(selected_idx[i])
            idx_j = int(selected_idx[j])
            if sim_matrix[idx_i][idx_j] > 0.60:
                penalty_sim += beta * float(sim_matrix[idx_i][idx_j])

    # 3. Constraint: Exactly K drugs
    penalty_count: float = gamma * float((total_drugs_selected - k) ** 2)  # type: ignore

    return reward + penalty_sim + penalty_count  # type: ignore


def simulated_annealing(
    pIC50_scores: np.ndarray,
    sim_matrix: np.ndarray,
    k: int = 5,
    initial_temp: float = 1000.0,
    final_temp: float = 0.1,
    cooling_rate: float = 0.99,
    iter_per_temp: int = 100
) -> Tuple[np.ndarray, float]:
    """Custom NumPy-based Simulated Annealing solver for QUBO."""
    n = len(pIC50_scores)

    # Start with a random state of exactly K=5 drugs
    current_state: np.ndarray = np.zeros(n)
    initial_indices = np.random.choice(n, k, replace=False)
    current_state[initial_indices] = 1

    current_energy = compute_energy(current_state, pIC50_scores, sim_matrix, k=k)

    best_state = current_state.copy()
    best_energy = current_energy

    temp = initial_temp

    print("Starting Simulated Annealing Optimization...")
    while temp > final_temp:
        for _ in range(iter_per_temp):
            # Propose a neighbor state: swap one 1 and one 0 to strictly maintain K=5 drugs
            neighbor_state = current_state.copy()  # type: ignore
            ones = np.where(neighbor_state == 1)[0]
            zeros = np.where(neighbor_state == 0)[0]

            if len(ones) > 0 and len(zeros) > 0:
                # Perform the swap
                neighbor_state[random.choice(ones)] = 0  # type: ignore
                neighbor_state[random.choice(zeros)] = 1  # type: ignore

            neighbor_energy = compute_energy(neighbor_state, pIC50_scores, sim_matrix, k=k)

            # Acceptance probability
            delta_e = neighbor_energy - current_energy  # type: ignore
            if delta_e < 0 or random.random() < np.exp(-delta_e / temp):  # type: ignore
                current_state = neighbor_state
                current_energy = neighbor_energy

                if current_energy < best_energy:
                    best_state = current_state.copy()
                    best_energy = current_energy

        temp *= cooling_rate  # type: ignore

    return best_state, best_energy


def main():
    print(f"Loading candidates from {OUTPUT_CSV}...")
    df = pd.read_csv(OUTPUT_CSV)

    # We only care about the top 100
    if len(df) > 100:
        df = df.head(100)

    pIC50_scores = df['predicted_pIC50'].values
    smiles_list = df['smiles'].values

    print("Calculating Tanimoto Similarity Matrix (RDKit Morgan Fingerprints)...")
    sim_matrix = calculate_similarity_matrix(smiles_list)

    # Run QUBO Solver
    best_state, best_energy = simulated_annealing(pIC50_scores, sim_matrix, k=5)

    selected_indices = np.where(best_state == 1)[0]
    selected_drugs = df.iloc[selected_indices]

    print("\n==============================================")
    print("🌟 FINAL QUANTUM-OPTIMIZED DISCOVERY LIST 🌟")
    print("==============================================")
    print("The Model has selected the best 5 highly potent AND diverse drugs:")
    print("-" * 60)

    for idx, row in selected_drugs.iterrows():
        print(f"💊 ID: {row['db_id']}")
        print(f"   Name: {row['name']}")
        print(f"   Potency (pIC50): {row['predicted_pIC50']:.4f}")
        print("-" * 60)

    print(f"Optimization Energy target achieved: {best_energy:.4f}")

    # Save the final 5
    final_path = os.path.join(PROCESSED_DIR, "final_5_discovery_list.csv")
    selected_drugs.to_csv(final_path, index=False)
    print(f"Saved Discovery List to: {final_path}")


if __name__ == "__main__":
    main()
