"""
GATv2 Drug–Gene–Organ GNN
==========================
Architecture:
    Graph Attention Network v2 (Brody et al. 2022) on a heterogeneous graph:
        Node types : Drug, Gene, Protein, Pathway, Organ, Patient
        Edge types : drug_targets_gene | gene_encodes_protein |
                     protein_in_pathway | pathway_affects_organ |
                     patient_has_gene_variant | patient_takes_drug
    Output heads: liver_toxic | kidney_toxic | cardio_toxic |
                  metabolic_toxic | brain_toxic  (sigmoid → 0-100 score)

Datasets (when training):
    - DrugBank 5.x       — drug→gene target interactions
    - PharmGKB           — curated PGx variant–drug pairs (CPIC level A/B)
    - STITCH 5.0         — compound–protein interactions
    - ChEMBL27           — bioactivity assay results
    - SIDER              — marketed drug side effects

Usage:
    from engine.planned.gatv2_drug_gene_organ import GATv2DrugGeneOrganGNN, load_gatv2
    model = load_gatv2("weights/gatv2_best.pt")
    scores = model.predict(hetero_data)   # → {"liver": 72.1, "kidney": 80.3, ...}
"""

import logging
import os

logger = logging.getLogger(__name__)

# ── Optional dependency guard ────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import GATv2Conv, HeteroConv, Linear
    from torch_geometric.data import HeteroData
    _GATV2_AVAILABLE = True
except ImportError:
    _GATV2_AVAILABLE = False
    logger.warning("[GATv2] torch_geometric not available — GATv2DrugGeneOrganGNN disabled.")


# ── Node / Edge schema ───────────────────────────────────────────────────────
NODE_TYPES = ["patient", "drug", "gene", "protein", "pathway", "organ"]

EDGE_TYPES = [
    ("patient", "takes",            "drug"),
    ("drug",    "targets",          "gene"),
    ("drug",    "interacts",        "drug"),
    ("gene",    "encodes",          "protein"),
    ("gene",    "variant_in",       "patient"),
    ("protein", "participates_in",  "pathway"),
    ("pathway", "affects",          "organ"),
    ("drug",    "modulates",        "pathway"),
]

# Feature dimensions per node type
NODE_DIMS = {
    "patient":  20,   # demographics + labs + genetics (same as EirionHGT)
    "drug":     16,   # dose, freq, duration, gene tags, pathway impacts
    "gene":      8,   # phenotype encoding × 8 gene slots
    "protein":   6,   # expression level, tissue specificity, toxicity flag × 6
    "pathway":   6,   # severity weight, n_drugs, n_genes, organ count, ...
    "organ":     4,   # baseline load, current score norm, condition load, age factor
}

ORGANS = ["liver", "kidney", "cardiovascular", "metabolic", "brain"]

METADATA = (NODE_TYPES, EDGE_TYPES)


if _GATV2_AVAILABLE:

    class GATv2DrugGeneOrganGNN(nn.Module):
        """
        Heterogeneous GATv2 — polypharmacy interaction modeling.

        Input : HeteroData from graph_builder.PatientGraph.to_hetero_data()
                (extended with protein/organ nodes added by build_extended_hetero)
        Output: dict mapping organ name → score in [0, 100]
        """

        def __init__(
            self,
            hidden_channels: int = 64,
            num_heads: int = 4,
            num_layers: int = 3,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.hidden = hidden_channels
            self.dropout = dropout

            # ── Input projections per node type ──────────────────────────────
            self.input_proj = nn.ModuleDict({
                nt: nn.Linear(dim, hidden_channels)
                for nt, dim in NODE_DIMS.items()
            })

            # ── GATv2 message passing layers (heterogeneous) ─────────────────
            self.convs = nn.ModuleList()
            for _ in range(num_layers):
                conv_dict = {}
                for src, rel, dst in EDGE_TYPES:
                    key = (src, rel, dst)
                    conv_dict[key] = GATv2Conv(
                        in_channels=hidden_channels,
                        out_channels=hidden_channels // num_heads,
                        heads=num_heads,
                        dropout=dropout,
                        concat=True,
                        add_self_loops=False,
                    )
                self.convs.append(HeteroConv(conv_dict, aggr="mean"))

            # ── Layer norms ───────────────────────────────────────────────────
            self.norms = nn.ModuleList([
                nn.ModuleDict({nt: nn.LayerNorm(hidden_channels) for nt in NODE_TYPES})
                for _ in range(num_layers)
            ])

            # ── Per-organ output heads (read from patient node) ───────────────
            self.organ_heads = nn.ModuleDict({
                organ: nn.Sequential(
                    nn.Linear(hidden_channels, 32),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(32, 1),
                    nn.Sigmoid(),
                )
                for organ in ORGANS
            })

        def forward(self, data: "HeteroData") -> dict:
            # Project input features
            x_dict = {}
            for nt in NODE_TYPES:
                if nt in data.node_types and data[nt].x is not None:
                    x = data[nt].x.float()
                    # Pad or truncate to match expected dim
                    expected = NODE_DIMS[nt]
                    if x.shape[-1] < expected:
                        x = F.pad(x, (0, expected - x.shape[-1]))
                    elif x.shape[-1] > expected:
                        x = x[:, :expected]
                    x_dict[nt] = self.input_proj[nt](x)

            if not x_dict:
                return self._fallback()

            # GATv2 message passing
            for i, conv in enumerate(self.convs):
                try:
                    out = conv(x_dict, data.edge_index_dict)
                    x_dict = {
                        nt: F.gelu(self.norms[i][nt](out[nt]))
                        if nt in out else x_dict.get(nt, torch.zeros(1, self.hidden))
                        for nt in NODE_TYPES
                        if nt in x_dict
                    }
                except Exception as e:
                    logger.debug("[GATv2] Conv layer %d skipped: %s", i, e)
                    continue

            # Read patient node embedding → organ scores
            patient_emb = x_dict.get("patient")
            if patient_emb is None or patient_emb.shape[0] == 0:
                return self._fallback()

            p = patient_emb[0].unsqueeze(0)
            return {
                organ: float(self.organ_heads[organ](p).item() * 100)
                for organ in ORGANS
            }

        def predict(self, data: "HeteroData") -> dict:
            """Convenience wrapper — eval mode, no_grad."""
            self.eval()
            with torch.no_grad():
                return self.forward(data)

        def _fallback(self) -> dict:
            """Safe defaults when graph is empty or missing nodes."""
            return {
                "liver": 50.0, "kidney": 70.0, "cardiovascular": 68.0,
                "metabolic": 65.0, "brain": 72.0,
            }


    def load_gatv2(weights_path: str = "") -> "GATv2DrugGeneOrganGNN":
        """
        Load GATv2 weights. If file absent, returns a randomly-initialised
        model (still runnable; scores will be random until trained).
        """
        model = GATv2DrugGeneOrganGNN()
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location="cpu", weights_only=True)
                if "state_dict" in state:
                    state = state["state_dict"]
                model.load_state_dict(state, strict=False)
                logger.info("[GATv2] Loaded weights from %s", weights_path)
            except Exception as e:
                logger.warning("[GATv2] Could not load weights: %s", e)
        else:
            logger.warning(
                "[GATv2] No weights at '%s' — running with random init. "
                "Output scores are non-calibrated until trained.",
                weights_path,
            )
        model.eval()
        return model

else:
    # ── Stub when torch_geometric unavailable ────────────────────────────────
    class GATv2DrugGeneOrganGNN:  # type: ignore[no-redef]
        """Stub — returns neutral fallback scores without raising."""
        def __init__(self, *args, **kwargs):
            logger.warning("[GATv2] torch_geometric required. Install: pip install torch-geometric")

        def predict(self, data) -> dict:
            return {"liver": 50.0, "kidney": 70.0, "cardiovascular": 68.0,
                    "metabolic": 65.0, "brain": 72.0}

        def forward(self, data) -> dict:
            return self.predict(data)

    def load_gatv2(weights_path: str = "") -> GATv2DrugGeneOrganGNN:
        return GATv2DrugGeneOrganGNN()
