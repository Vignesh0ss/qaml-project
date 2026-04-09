import os
import torch
from torch.nn import MSELoss
from torch_geometric.loader import DataLoader
from sklearn.model_selection import train_test_split
from model import GCN

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
PT_FILE = os.path.join(PROCESSED_DIR, "molecular_graphs.pt")
MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pth")


def main():
    print("Loading molecular graphs...")
    try:
        graphs = torch.load(PT_FILE, weights_only=False)
        print(f"Loaded {len(graphs)} graphs successfully.")
    except Exception as e:
        print(f"Error loading graphs: {e}")
        return

    # Check if GPU is available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Data Split (80% Train, 20% Test)
    print("Splitting data into 80% Training and 20% Testing...")
    train_graphs, test_graphs = train_test_split(graphs, test_size=0.2, random_state=42)

    # Create DataLoaders
    train_loader = DataLoader(train_graphs, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_graphs, batch_size=64, shuffle=False)

    # Initialize the model, optimizer, and loss function
    # in_channels=5 because we have 5 node features (Atomic Num, Chirality, Degree, Formal Charge, Aromaticity)
    model = GCN(in_channels=5, hidden_channels=64, out_channels=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)
    criterion = MSELoss()

    def train():
        model.train()
        total_loss = 0
        for data in train_loader:
            data = data.to(device)
            optimizer.zero_grad()

            # Forward pass
            out = model(data.x, data.edge_index, data.batch)

            # Since standard_value is our target, predict the continuous value
            loss = criterion(out.squeeze(), data.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * data.num_graphs
        return total_loss / len(train_loader.dataset)

    def test(loader):
        model.eval()
        total_loss = 0
        with torch.no_grad():
            for data in loader:
                data = data.to(device)
                out = model(data.x, data.edge_index, data.batch)
                loss = criterion(out.squeeze(), data.y)
                total_loss += loss.item() * data.num_graphs
        return total_loss / len(loader.dataset)

    print("\nStarting training loop...")
    epochs = 100
    for epoch in range(1, epochs + 1):
        train_loss = train()
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch:02d}: Loss: {train_loss:.4f}")

    final_test_loss = test(test_loader)
    print("\nTraining Complete.")
    print(f"Final Test Loss: {final_test_loss:.4f}")

    print(f"\nSaving trained model to {MODEL_SAVE_PATH}...")
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print("✅ Model successfully saved.")


if __name__ == "__main__":
    main()
