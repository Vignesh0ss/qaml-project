import torch
from torch.nn import Linear
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch.nn import BatchNorm1d


class GCN(torch.nn.Module):
    def __init__(self, in_channels=5, hidden_channels=64, out_channels=1):
        super(GCN, self).__init__()
        torch.manual_seed(42)

        # 4 layers of GCNConv
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.bn1 = BatchNorm1d(hidden_channels)

        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.bn2 = BatchNorm1d(hidden_channels)

        self.conv3 = GCNConv(hidden_channels, hidden_channels)
        self.bn3 = BatchNorm1d(hidden_channels)

        self.conv4 = GCNConv(hidden_channels, hidden_channels)
        self.bn4 = BatchNorm1d(hidden_channels)

        # Linear layer for final continuous prediction (pIC50 score)
        self.lin = Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index, batch):
        # 1. Obtain node embeddings with BatchNorm and ReLU
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)

        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)

        x = self.conv3(x, edge_index)
        x = self.bn3(x)
        x = F.relu(x)

        x = self.conv4(x, edge_index)
        x = self.bn4(x)

        # 2. Readout layer (Global Mean Pooling) to turn atom data into a single molecular fingerprint
        x = global_mean_pool(x, batch)  # [batch_size, hidden_channels]

        # 3. Apply a final regressor
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin(x)

        return x
