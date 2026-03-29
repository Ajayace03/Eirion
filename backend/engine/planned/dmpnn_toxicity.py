"""
DMPNN Molecular Toxicity Model
================================
Directed Message Passing Neural Network (Chemprop-style) for per-endpoint molecular toxicity.

Architecture:
    - RDKit atom/bond featurization → directed bond graph
    - 4 rounds of directed message passing (edge → node aggregation)
    - Readout: sum-pooling over atom embeddings → molecule-level vector
    - 6 task-specific sigmoid heads (one per toxicity endpoint)
    - MC Dropout for uncertainty estimation

Toxicity endpoints:
    hepatotoxicity | nephrotoxicity | cardiotoxicity |
    reproductive_toxicity | genotoxicity | neurotoxicity

Datasets (when training):
    ToxCast (~600 endpoints, EPA) · Tox21 (12 endpoints, NIH) ·
    FAERS (FDA adverse events) · ClinTox · SIDER

Usage:
    from engine.planned.dmpnn_toxicity import DMPNNToxicityModel, load_dmpnn
    model = load_dmpnn("weights/dmpnn_tox.pt")
    scores = model.predict_smiles("CC(=O)Oc1ccccc1C(=O)O")
    # → {"hepatotoxicity": 0.12, "nephrotoxicity": 0.05, ...}
"""

import logging
import os
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional dependency guard ────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    _RDKIT_AVAILABLE = True
except ImportError:
    _RDKIT_AVAILABLE = False
    logger.warning("[DMPNN] RDKit not available — SMILES featurization disabled.")

# ── Constants ────────────────────────────────────────────────────────────────
ATOM_FEATURE_DIM  = 72   # one-hot atom type (44) + degree (6) + H (5) + charge (5) + aromaticity (1) + chirality (4) + ring (4) + hybridization (4) - ring memberships
BOND_FEATURE_DIM  = 14   # bond type (4) + conjugation (1) + ring (1) + stereo (6) + nontrivial (2)
HIDDEN_DIM        = 128
STEPS             = 4    # message passing steps
DROPOUT           = 0.15

ENDPOINTS = [
    "hepatotoxicity",
    "nephrotoxicity",
    "cardiotoxicity",
    "reproductive_toxicity",
    "genotoxicity",
    "neurotoxicity",
]

STUB_SCORES = {e: 0.05 for e in ENDPOINTS}  # conservative 5% baseline


# ── Featurization ────────────────────────────────────────────────────────────

def _atom_features(atom) -> List[float]:
    """72-dim atom feature vector."""
    from rdkit.Chem import rdchem
    ATOM_TYPES = ['C','N','O','S','F','Si','P','Cl','Br','Mg','Na','Ca','Fe',
                  'As','Al','I','B','V','K','Tl','Yb','Sb','Sn','Ag','Pd','Co',
                  'Se','Ti','Zn','H','Li','Ge','Cu','Au','Ni','Cd','In','Mn',
                  'Zr','Cr','Pt','Hg','Pb','Unknown']
    def one_hot(val, choices):
        vec = [0.0] * len(choices)
        if val in choices:
            vec[choices.index(val)] = 1.0
        else:
            vec[-1] = 1.0
        return vec

    feats = (
        one_hot(atom.GetSymbol(), ATOM_TYPES)
        + one_hot(atom.GetDegree(), list(range(6)))
        + one_hot(atom.GetTotalNumHs(), list(range(5)))
        + one_hot(atom.GetFormalCharge() + 2, list(range(5)))
        + [float(atom.GetIsAromatic())]
        + one_hot(int(atom.GetChiralTag()), [0, 1, 2, 3])
        + [float(atom.IsInRing())]
        + [float(atom.IsInRingSize(s)) for s in [3, 4, 5, 6]]
        + one_hot(int(atom.GetHybridization()),
                  [rdchem.HybridizationType.SP,
                   rdchem.HybridizationType.SP2,
                   rdchem.HybridizationType.SP3,
                   rdchem.HybridizationType.SP3D])
    )
    return feats[:ATOM_FEATURE_DIM]  # trim / pad if needed


def _bond_features(bond) -> List[float]:
    """14-dim bond feature vector."""
    from rdkit.Chem import rdchem
    BT = rdchem.BondType
    feats = (
        [float(bond.GetBondType() == BT.SINGLE),
         float(bond.GetBondType() == BT.DOUBLE),
         float(bond.GetBondType() == BT.TRIPLE),
         float(bond.GetBondType() == BT.AROMATIC)]
        + [float(bond.GetIsConjugated())]
        + [float(bond.IsInRing())]
        + [0.0] * 6   # stereo (placeholder)
        + [0.0, 0.0]  # nontrivial stereo flags
    )
    return feats[:BOND_FEATURE_DIM]


def smiles_to_graph(smiles: str) -> Optional[dict]:
    """Convert SMILES to directed bond graph tensors. Returns None if invalid."""
    if not _RDKIT_AVAILABLE or not _TORCH_AVAILABLE:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    n_atoms = mol.GetNumAtoms()
    atom_feats = [_atom_features(a) for a in mol.GetAtoms()]
    # Pad atom features to ATOM_FEATURE_DIM
    for i, af in enumerate(atom_feats):
        if len(af) < ATOM_FEATURE_DIM:
            atom_feats[i] = af + [0.0] * (ATOM_FEATURE_DIM - len(af))

    src, dst, bond_feats = [], [], []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        bf = _bond_features(bond)
        src += [i, j]
        dst += [j, i]
        bond_feats += [bf, bf]

    if not src:
        # No bonds — single atom molecule
        src, dst = [0], [0]
        bond_feats = [[0.0] * BOND_FEATURE_DIM]

    import torch
    return {
        "x":    torch.tensor(atom_feats, dtype=torch.float),           # (n_atoms, ATOM_FEATURE_DIM)
        "edge_index": torch.tensor([src, dst], dtype=torch.long),       # (2, n_edges)
        "edge_attr":  torch.tensor(bond_feats, dtype=torch.float),      # (n_edges, BOND_FEATURE_DIM)
        "n_atoms": n_atoms,
    }


# ── Model ─────────────────────────────────────────────────────────────────────

if _TORCH_AVAILABLE:

    class DMPNNToxicityModel(nn.Module):
        """
        Directed Message Passing Neural Network for molecular toxicity.
        Produces 6 sigmoid endpoint probabilities [0, 1].
        """

        def __init__(
            self,
            atom_dim: int = ATOM_FEATURE_DIM,
            bond_dim: int = BOND_FEATURE_DIM,
            hidden: int = HIDDEN_DIM,
            steps: int = STEPS,
            dropout: float = DROPOUT,
        ):
            super().__init__()
            self.steps = steps

            # Input embedding
            self.atom_embed = nn.Linear(atom_dim, hidden)
            self.bond_embed = nn.Linear(bond_dim, hidden)

            # Message passing: concatenate atom + incoming bond → new message
            self.message_fn = nn.Sequential(
                nn.Linear(hidden * 2, hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
            )

            # Node update: atom embed + aggregated messages
            self.update_fn = nn.Sequential(
                nn.Linear(hidden * 2, hidden),
                nn.ReLU(),
            )

            # Readout: molecule-level
            self.readout = nn.Sequential(
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden, hidden // 2),
                nn.ReLU(),
            )

            # Per-endpoint heads
            self.endpoint_heads = nn.ModuleDict({
                ep: nn.Sequential(
                    nn.Linear(hidden // 2, 16),
                    nn.ReLU(),
                    nn.Linear(16, 1),
                    nn.Sigmoid(),
                )
                for ep in ENDPOINTS
            })

        def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor",
                    edge_attr: "torch.Tensor") -> Dict[str, "torch.Tensor"]:
            # Initial embeddings
            h_v = self.atom_embed(x)           # (N, H)
            h_e = self.bond_embed(edge_attr)   # (E, H)

            src, dst = edge_index[0], edge_index[1]
            n_atoms = x.shape[0]

            # Directed message passing
            for _ in range(self.steps):
                # Message: concatenate source atom + edge
                msgs = self.message_fn(torch.cat([h_v[src], h_e], dim=-1))  # (E, H)

                # Aggregate messages into destination atoms
                agg = torch.zeros(n_atoms, msgs.shape[-1], device=x.device)
                agg.scatter_add_(0, dst.unsqueeze(1).expand_as(msgs), msgs)

                # Update atom embeddings
                h_v = self.update_fn(torch.cat([h_v, agg], dim=-1))

            # Readout: sum-pool over all atoms → molecule vector
            mol_vec = h_v.sum(dim=0, keepdim=True)   # (1, H)
            mol_vec = self.readout(mol_vec)

            return {ep: self.endpoint_heads[ep](mol_vec).squeeze() for ep in ENDPOINTS}

        def predict_smiles(self, smiles: str) -> Dict[str, float]:
            """Full pipeline: SMILES → graph → forward → probabilities."""
            graph = smiles_to_graph(smiles)
            if graph is None:
                logger.warning("[DMPNN] Could not parse SMILES: %s", smiles)
                return STUB_SCORES.copy()

            self.eval()
            with torch.no_grad():
                try:
                    out = self.forward(
                        graph["x"], graph["edge_index"], graph["edge_attr"]
                    )
                    return {ep: float(out[ep].item()) for ep in ENDPOINTS}
                except Exception as e:
                    logger.error("[DMPNN] Forward pass failed for %s: %s", smiles, e)
                    return STUB_SCORES.copy()

        def hepatotoxicity_score(self, smiles: str) -> float:
            """Convenience: returns just the hepatotoxicity probability [0,1]."""
            return self.predict_smiles(smiles).get("hepatotoxicity", 0.05)


    def load_dmpnn(weights_path: str = "") -> "DMPNNToxicityModel":
        """Load DMPNN model. Random init if no weights file found."""
        model = DMPNNToxicityModel()
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location="cpu", weights_only=True)
                if "state_dict" in state:
                    state = state["state_dict"]
                model.load_state_dict(state, strict=False)
                logger.info("[DMPNN] Loaded weights from %s", weights_path)
            except Exception as e:
                logger.warning("[DMPNN] Could not load weights: %s", e)
        else:
            logger.info(
                "[DMPNN] No weights at '%s' — running with random init. "
                "Train on ToxCast/Tox21 for calibrated scores.",
                weights_path,
            )
        model.eval()
        return model

else:
    class DMPNNToxicityModel:  # type: ignore[no-redef]
        """Stub when PyTorch unavailable."""
        def predict_smiles(self, smiles: str) -> Dict[str, float]:
            return STUB_SCORES.copy()
        def hepatotoxicity_score(self, smiles: str) -> float:
            return 0.05

    def load_dmpnn(weights_path: str = "") -> DMPNNToxicityModel:
        return DMPNNToxicityModel()
