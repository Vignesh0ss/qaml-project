"""
Feature engineering for drug-target interaction model.
Converts SMILES to 2048-bit fingerprints and targets to 500-bit vectors.
"""
import numpy as np
import hashlib
from rdkit import Chem

from rdkit.Chem import AllChem

def get_fingerprint(smiles: str, n_bits: int = 2048) -> np.ndarray:
    """Convert SMILES to Morgan Fingerprint vector."""
    if not smiles or not isinstance(smiles, str):
        return np.zeros(n_bits, dtype=np.float32)
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits, dtype=np.float32)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=n_bits)
        return np.array(fp, dtype=np.float32)
    except Exception:
        return np.zeros(n_bits, dtype=np.float32)

def get_target_vector(target_id: str, dimension: int = 500) -> np.ndarray:
    """
    Deterministic target embedding using hashing.
    Provides a consistent 500-dim vector for any Target ID/Name.
    """
    if not target_id:
        return np.zeros(dimension, dtype=np.float32)
    
    # Use SHA-256 for high entropy
    h = hashlib.sha256(str(target_id).encode()).digest()
    
    # Convert digest to bit array or use as seed for reproducible random vector
    np.random.seed(int.from_bytes(h[:4], "big"))
    return np.random.normal(0, 0.1, dimension).astype(np.float32)
