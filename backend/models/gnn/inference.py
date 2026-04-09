import os
import pandas as pd
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from rdkit import Chem
from model import GCN
import warnings
warnings.filterwarnings("ignore")

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

DRUGBANK_CSV = os.path.join(PROCESSED_DIR, "drugbank_drug_smiles.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pth")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "top_candidates.csv")


def get_node_features(atom):
    return [
        atom.GetAtomicNum(),
        int(atom.GetChiralTag()),
        atom.GetDegree(),
        atom.GetFormalCharge(),
        1 if atom.GetIsAromatic() else 0
    ]


def get_edge_features(bond):
    bond_type = bond.GetBondType()
    if bond_type == Chem.rdchem.BondType.SINGLE:
        return [1]
    elif bond_type == Chem.rdchem.BondType.DOUBLE:
        return [2]
    elif bond_type == Chem.rdchem.BondType.TRIPLE:
        return [3]
    elif bond_type == Chem.rdchem.BondType.AROMATIC:
        return [4]
    return [0]


def smiles_to_graph(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    node_features = [get_node_features(atom) for atom in mol.GetAtoms()]
    x = torch.tensor(node_features, dtype=torch.float)

    edge_indices, edge_features = [], []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        edge_indices.extend([[i, j], [j, i]])
        e_feat = get_edge_features(bond)
        edge_features.extend([e_feat, e_feat])

    if edge_indices:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_features, dtype=torch.float)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 1), dtype=torch.float)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def main():
    print("Initializing Inference Engine...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load Model
    model = GCN(in_channels=5, hidden_channels=64, out_channels=1).to(device)
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    except Exception as e:
        print(f"Error loading weights: {e}")
        return

    model.eval()
    print("✅ Trained model loaded successfully.")

    # Load Database
    print(f"Loading DrugBank Database from {DRUGBANK_CSV}...")
    db = pd.read_csv(DRUGBANK_CSV)
    db = db.dropna(subset=['smiles', 'db_id', 'name'])
    total_drugs = len(db)
    print(f"Total valid drugs to screen: {total_drugs:,}")

    # Inference Loop
    batch_size = 500
    results = []

    print("\nStarting Virtual Screening (Featurizing and Predicting in batches)...")
    for start_idx in range(0, total_drugs, batch_size):
        end_idx = min(start_idx + batch_size, total_drugs)
        batch_df = db.iloc[start_idx:end_idx]

        batch_graphs = []
        valid_indices = []

        # 1. Featurize on the fly
        for idx, row in batch_df.iterrows():
            graph = smiles_to_graph(row['smiles'])
            if graph is not None:
                batch_graphs.append(graph)
                valid_indices.append(idx)

        if not batch_graphs:
            continue

        # 2. Predict
        loader = DataLoader(batch_graphs, batch_size=len(batch_graphs), shuffle=False)
        with torch.no_grad():
            for data in loader:
                data = data.to(device)
                preds = model(data.x, data.edge_index, data.batch)

                # Squeeze predictions to flatten them
                preds = preds.squeeze().cpu().numpy()

                # If only 1 graph was valid, it returns a 0-d array, so wrap in list
                if preds.ndim == 0:
                    preds = [preds.item()]
                else:
                    preds = preds.tolist()

                for i, pred_pIC50 in enumerate(preds):
                    original_row = db.loc[valid_indices[i]]
                    results.append({
                        'db_id': original_row['db_id'],
                        'name': original_row['name'],
                        'smiles': original_row['smiles'],
                        'predicted_pIC50': round(pred_pIC50, 4)
                    })

        print(f"Processed {end_idx:,} / {total_drugs:,} drugs...")

    # Compiling Results
    print("\nRanking candidates...")
    results_df = pd.DataFrame(results)

    # Sort descending (higher pIC50 = better binding affinity)
    results_df = results_df.sort_values(by='predicted_pIC50', ascending=False)

    # Save Top 100
    top_100 = results_df.head(100)
    top_100.to_csv(OUTPUT_CSV, index=False)

    print("\n==============================================")
    print("✅ VIRTUAL SCREENING COMPLETE")
    print("==============================================")
    print(f"1. Total Drugs Evaluated: {len(results_df):,}")
    print(f"2. Top 100 Candidates Saved To: {OUTPUT_CSV}")
    print(f"3. Highest Predicted pIC50 Score: {top_100.iloc[0]['predicted_pIC50']}")
    print(f"4. Lowest in Top 100: {top_100.iloc[99]['predicted_pIC50']}\n")


if __name__ == "__main__":
    main()
