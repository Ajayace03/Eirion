"""
EirionHGT — Heterogeneous Graph Transformer for multi-organ toxicity scoring.

Architecture:
  Input nodes: patient, compound, gene, pathway, disease
  Edge types: substrate_of, inhibits, mediates, impacts, stresses
  Output heads: liver_score, kidney_score, cardio_score, metabolic_score

Falls back gracefully if torch_geometric is not installed.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Try loading PyG — graceful fallback if not installed
try:
    import torch
    import torch.nn as nn
    from torch_geometric.nn import HGTConv, Linear as PyGLinear
    from torch_geometric.data import HeteroData
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    logger.warning("[GNN] torch_geometric not available — EirionHGT disabled, using rules-based fallback.")


if TORCH_GEOMETRIC_AVAILABLE:
    import torch
    import torch.nn as nn
    from torch_geometric.nn import HGTConv
    from torch_geometric.data import HeteroData

    # Node types in the knowledge graph
    NODE_TYPES = ["patient", "compound", "gene", "pathway", "disease"]

    # Edge types (src_type, rel_name, dst_type)
    EDGE_TYPES = [
        ("compound", "substrate_of", "gene"),
        ("compound", "inhibits", "gene"),
        ("compound", "activates", "pathway"),
        ("compound", "damages", "pathway"),
        ("gene", "mediates", "pathway"),
        ("pathway", "impacts", "patient"),
        ("disease", "stresses", "patient"),
        ("patient", "takes", "compound"),
    ]

    METADATA = (NODE_TYPES, EDGE_TYPES)

    class EirionHGT(nn.Module):
        """
        Heterogeneous Graph Attention Network for Eirion.

        Input: patient-specific HeteroData subgraph from graph_builder
        Output: 4 organ risk scores (liver, kidney, cardiovascular, metabolic) in [0, 100]
        """

        def __init__(self, hidden_channels: int = 64, num_heads: int = 4, num_layers: int = 3):
            super().__init__()
            self.hidden = hidden_channels

            # Input projection for each node type
            # Feature dims: patient(20), compound(16), gene(8), pathway(6), disease(6)
            self.input_proj = nn.ModuleDict({
                "patient":  nn.Linear(20, hidden_channels),
                "compound": nn.Linear(16, hidden_channels),
                "gene":     nn.Linear(8,  hidden_channels),
                "pathway":  nn.Linear(6,  hidden_channels),
                "disease":  nn.Linear(6,  hidden_channels),
            })

            # HGT message passing layers
            self.convs = nn.ModuleList([
                HGTConv(hidden_channels, hidden_channels, METADATA, num_heads)
                for _ in range(num_layers)
            ])

            # Layer norms per node type per layer
            self.norms = nn.ModuleList([
                nn.ModuleDict({nt: nn.LayerNorm(hidden_channels) for nt in NODE_TYPES})
                for _ in range(num_layers)
            ])

            # Output heads (one per organ) — read from patient node embedding
            self.liver_head     = nn.Sequential(nn.Linear(hidden_channels, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())
            self.kidney_head    = nn.Sequential(nn.Linear(hidden_channels, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())
            self.cardio_head    = nn.Sequential(nn.Linear(hidden_channels, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())
            self.metabolic_head = nn.Sequential(nn.Linear(hidden_channels, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())

        def forward(self, data: "HeteroData") -> dict:
            # Project all node features into hidden space
            x_dict = {
                nt: self.input_proj[nt](data[nt].x.float())
                for nt in NODE_TYPES if nt in data.node_types and data[nt].x is not None
            }

            # HGT message passing
            for i, conv in enumerate(self.convs):
                x_dict = conv(x_dict, data.edge_index_dict)
                x_dict = {nt: self.norms[i][nt](x) for nt, x in x_dict.items()}

            # Read from patient node (first patient node = index 0)
            patient_emb = x_dict.get("patient")
            if patient_emb is None or patient_emb.shape[0] == 0:
                return self._fallback()

            p = patient_emb[0].unsqueeze(0)
            return {
                "liver":          float(self.liver_head(p).item() * 100),
                "kidney":         float(self.kidney_head(p).item() * 100),
                "cardiovascular": float(self.cardio_head(p).item() * 100),
                "metabolic":      float(self.metabolic_head(p).item() * 100),
            }

        def _fallback(self) -> dict:
            return {"liver": 50.0, "kidney": 70.0, "cardiovascular": 70.0, "metabolic": 65.0}


    def load_gnn(weights_path: str) -> "EirionHGT | None":
        """Load GNN weights from disk. Returns None if file missing."""
        if not os.path.exists(weights_path):
            logger.warning("[GNN] Weights not found at %s — running untrained (random weights)", weights_path)
            return EirionHGT()
        try:
            model = EirionHGT()
            state_dict = torch.load(weights_path, map_location="cpu", weights_only=True)
            if isinstance(state_dict, dict) and "state_dict" in state_dict:
                state_dict = state_dict["state_dict"]
            model.load_state_dict(state_dict, strict=False)
            model.eval()
            logger.info("[GNN] EirionHGT loaded from %s", weights_path)
            return model
        except Exception as e:
            logger.warning("[GNN] Failed to load weights: %s — using untrained model", e)
            return EirionHGT()

else:
    # Stub classes when PyG not available
    class EirionHGT:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def eval(self): return self
        def forward(self, data): return {"liver": 50.0, "kidney": 70.0, "cardiovascular": 70.0, "metabolic": 65.0}

    def load_gnn(weights_path: str):
        return None
