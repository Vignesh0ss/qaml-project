import os
import pandas as pd
import torch
from torch_geometric.data import Data
from rdkit import Chem

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

DRUGBANK_CSV = os.path.join(PROCESSED_DIR, "drugbank_drug_smiles.csv")
CHEMBL_CSV = os.path.join(PROCESSED_DIR, "chembl_binding_scores.csv")
FINAL_CSV = os.path.join(PROCESSED_DIR, "final_training_set.csv")
PT_OUTPUT = os.path.join(PROCESSED_DIR, "molecular_graphs.pt")


def get_node_features(atom):
    """
    Extracts node features for an atom.
    Features:
    - Atomic Number
    - Chirality (0, 1, 2, 3 mapped from GetChiralTag)
    - Degree
    - Formal Charge
    - Aromaticity (1 if aromatic, 0 otherwise)
    """
    return [
        atom.GetAtomicNum(),
        int(atom.GetChiralTag()),
        atom.GetDegree(),
        atom.GetFormalCharge(),
        1 if atom.GetIsAromatic() else 0
    ]


def get_edge_features(bond):
    """
    Extracts edge features for a bond.
    Features:
    - Bond Type (Single=1, Double=2, Triple=3, Aromatic=4)
    """
    bond_type = bond.GetBondType()
    if bond_type == Chem.rdchem.BondType.SINGLE:
        return [1]
    elif bond_type == Chem.rdchem.BondType.DOUBLE:
        return [2]
    elif bond_type == Chem.rdchem.BondType.TRIPLE:
        return [3]
    elif bond_type == Chem.rdchem.BondType.AROMATIC:
        return [4]
    else:
        return [0]


def smiles_to_graph(smiles, target_value):
    """
    Converts a SMILES string into a PyTorch Geometric Data object.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Node Features
    node_features = []
    for atom in mol.GetAtoms():
        node_features.append(get_node_features(atom))

    x = torch.tensor(node_features, dtype=torch.float)

    # Edge Index and Edge Features
    edge_indices = []
    edge_features = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()

        # PyTorch Geometric requires directed edges (undirected graph needs both directions)
        edge_indices.append([i, j])
        edge_indices.append([j, i])

        e_feat = get_edge_features(bond)
        edge_features.append(e_feat)
        edge_features.append(e_feat)

    if len(edge_indices) > 0:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_features, dtype=torch.float)
    else:
        # Handle molecules with no bonds (e.g., single atoms, salts)
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 1), dtype=torch.float)

    import math

    # Calculate pIC50 = -log10(value * 10^-9)
    # If the value is 0 or negative (invalid for logic), handle gracefully
    if target_value <= 0:
        return None

    pIC50 = -math.log10(target_value * 1e-9)

    y = torch.tensor([pIC50], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    return data


def main():
    print("Loading datasets...")
    db = pd.read_csv(DRUGBANK_CSV)
    chembl = pd.read_csv(CHEMBL_CSV)

    # Preprocessing to avoid issues if nulls were missed
    db = db.dropna(subset=['smiles'])
    chembl = chembl.dropna(subset=['canonical_smiles', 'standard_value'])

    print("Merging datasets on normalized SMILES...")
    merged = pd.merge(db, chembl, left_on="smiles", right_on="canonical_smiles", how="inner")

    # Keep essential columns to save memory in final CSV
    merged = merged[['db_id', 'name', 'smiles', 'target_chembl_id',
                     'target_name', 'standard_value', 'standard_units', 'standard_type']]
    merged.to_csv(FINAL_CSV, index=False)
    print(f"Merged dataset saved to {FINAL_CSV} with {len(merged):,} rows.")

    print("\nStarting featurization. Converting SMILES to PyTorch Geometric graphs...")
    graphs = []

    success: int = 0
    failed: int = 0

    for i, row in merged.iterrows():
        smiles = row['smiles']
        target_val = float(row['standard_value'])

        data = smiles_to_graph(smiles, target_val)
        if data is not None:
            graphs.append(data)
            success += 1  # type: ignore
        else:
            failed += 1  # type: ignore

        if (i + 1) % 500 == 0:
            print(f"Processed {i + 1}/{len(merged)} molecules...")

    print(f"\nFeaturization complete: {success} successfully converted, {failed} failed.")

    print("Saving processed graph dataset...")
    torch.save(graphs, PT_OUTPUT)
    print(f"✅ PyTorch Geometric dataset saved to {PT_OUTPUT}")


if __name__ == "__main__":
    main()
