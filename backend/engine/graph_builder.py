"""
Graph Builder
=============
Assembles a patient-specific knowledge subgraph at inference time.
Uses the static COMPOUND_INTERACTIONS and PATHWAY_GRAPH from knowledge_graph.py
to construct a HeteroData object for EirionHGT, OR returns a structured
feature dict for the rules-based multi-organ scorer when PyG is unavailable.
"""

import numpy as np
from typing import Dict, List, Optional

from engine.knowledge_graph import (
    COMPOUND_INTERACTIONS,
    PATHWAY_GRAPH,
    CONDITION_ORGAN_PENALTIES,
    get_gene_multiplier,
    detect_ddis,
)

# Phenotype → numeric encoding for GNN node features
PHENOTYPE_ENCODING = {
    "poor": 0.0,
    "intermediate": 0.33,
    "normal": 0.67,
    "ultra_rapid": 1.0,
    "unknown": 0.5,
    # SLCO1B1 specific
    "reduced": 0.25,
}

GENE_ORDER = [
    "cyp2d6_metabolizer",
    "cyp2c19_metabolizer",
    "cyp3a4_metabolizer",
    "cyp2c9_metabolizer",
    "cyp1a2_metabolizer",
    "slco1b1_function",
    "ugt1a1_function",
    "mthfr_c677t",
]

MTHFR_ENCODING = {"normal": 0.0, "heterozygous": 0.5, "homozygous": 1.0, "unknown": 0.25}


def encode_patient_features(request) -> np.ndarray:
    """
    Encodes the patient into a 20-dimensional feature vector for the GNN patient node.
    """
    p = request.patient
    ls = request.lifestyle
    labs = request.labs or type("Labs", (), {})()
    gen = request.genetics

    # Demographics (5)
    age_norm = (getattr(p, "age", 35) - 18) / 82
    sex_enc = 0.0 if getattr(p, "sex", "female") == "female" else 1.0
    bmi = getattr(p, "weight_kg", 70) / (((getattr(p, "height_cm", 170) / 100) ** 2) or 1)
    bmi_norm = min(bmi / 40, 1.0)
    n_conditions = min(len(getattr(request, "conditions", []) or []) / 5, 1.0)

    # Lifestyle (5)
    sugar_norm = min(getattr(ls, "sugar_g_per_day", 50) / 200, 1.0)
    sleep_norm = max(0, (getattr(ls, "sleep_hours_avg", 7) - 4) / 6)
    alcohol_norm = min(getattr(ls, "alcohol_drinks_per_week", 0) / 20, 1.0)
    stress_norm = (getattr(ls, "stress_level", 5) - 1) / 9
    # Derive activity encoding from exercise_mins_per_week thresholds
    _ex = getattr(ls, "exercise_mins_per_week", 150)
    if _ex >= 300:
        activity_enc = 1.0    # intense
    elif _ex >= 150:
        activity_enc = 0.67   # moderate
    elif _ex >= 60:
        activity_enc = 0.33   # light
    else:
        activity_enc = 0.0    # sedentary

    # Lab markers (6) — normalised against clinical danger threshold
    ast_norm = min((getattr(labs, "ast_u_per_l", None) or 25) / 80, 1.0)
    alt_norm = min((getattr(labs, "alt_u_per_l", None) or 25) / 80, 1.0)
    egfr_norm = max(0, min((getattr(labs, "egfr_ml_per_min", None) or 90) / 120, 1.0))
    hba1c_norm = min((getattr(labs, "hba1c_pct", None) or 5.0) / 9, 1.0)
    ldl_norm = min((getattr(labs, "ldl_mg_per_dl", None) or 100) / 200, 1.0)
    crp_norm = min((getattr(labs, "hscrp_mg_per_l", None) or 0.5) / 5, 1.0)

    # Genetics (4) — key genes
    cyp2d6 = PHENOTYPE_ENCODING.get(getattr(gen, "cyp2d6_metabolizer", "unknown"), 0.5)
    cyp2c19 = PHENOTYPE_ENCODING.get(getattr(gen, "cyp2c19_metabolizer", "unknown"), 0.5)
    slco1b1 = PHENOTYPE_ENCODING.get(getattr(gen, "slco1b1_function", "unknown"), 0.5)
    mthfr = MTHFR_ENCODING.get(getattr(gen, "mthfr_c677t", "unknown"), 0.25)

    features = np.array([
        age_norm, sex_enc, bmi_norm, n_conditions, 0.0,       # demographics (5)
        sugar_norm, sleep_norm, alcohol_norm, stress_norm, activity_enc,  # lifestyle (5)
        ast_norm, alt_norm, egfr_norm, hba1c_norm, ldl_norm, crp_norm,   # labs (6)
        cyp2d6, cyp2c19, slco1b1, mthfr,                                  # genetics (4)
    ], dtype=np.float32)
    return features  # shape (20,)


def encode_compound_features(item, genetics: dict) -> np.ndarray:
    """
    Encodes a RegimenItem into a 16-dim compound feature vector.
    """
    compound_data = COMPOUND_INTERACTIONS.get(item.compound_id if hasattr(item, "compound_id") else item, {})
    dose = getattr(item, "dose_mg", 300) if hasattr(item, "dose_mg") else 300
    freq = getattr(item, "frequency_per_day", 1) if hasattr(item, "frequency_per_day") else 1
    duration = getattr(item, "duration_months", None) if hasattr(item, "duration_months") else None

    # Compute genetics multiplier
    gene_mult = 1.0
    for gene_int in compound_data.get("gene_interactions", []):
        m = get_gene_multiplier(gene_int, genetics)
        if m > gene_mult:
            gene_mult = m

    # Risk tags encoding (6 bits)
    risk_tags = set(compound_data.get("risk_tags", []))
    tag_cyp2d6 = 1.0 if "CYP2D6_substrate" in risk_tags else 0.0
    tag_cyp2c19 = 1.0 if "CYP2C19_substrate" in risk_tags else 0.0
    tag_slco1b1 = 1.0 if "SLCO1B1_substrate" in risk_tags else 0.0
    tag_herb = 1.0 if "herb_hepatotoxic_reports" in risk_tags else 0.0
    tag_fat_sol = 1.0 if "fat_soluble" in risk_tags else 0.0
    tag_protective = 1.0 if compound_data.get("is_protective", False) else 0.0

    # Pathway activation summary (4 aggregated)
    pathway_acts = compound_data.get("pathway_activations", [])
    liver_delta = sum(abs(p["delta"]) for p in pathway_acts if "liver" in PATHWAY_GRAPH.get(p["pathway"], {}).get("organs", []))
    kidney_delta = sum(abs(p["delta"]) for p in pathway_acts if "kidney" in PATHWAY_GRAPH.get(p["pathway"], {}).get("organs", []))
    cardio_delta = sum(abs(p["delta"]) for p in pathway_acts if "cardiovascular" in PATHWAY_GRAPH.get(p["pathway"], {}).get("organs", []))
    meta_delta = sum(abs(p["delta"]) for p in pathway_acts if "metabolic" in PATHWAY_GRAPH.get(p["pathway"], {}).get("organs", []))

    features = np.array([
        min(dose / 2000, 1.0),                          # dose normalised
        min(freq / 4, 1.0),                             # frequency normalised
        min((duration or 6) / 24, 1.0),                 # duration normalised
        min(gene_mult, 2.0) / 2.0,                      # genetic load multiplier
        tag_cyp2d6, tag_cyp2c19, tag_slco1b1,           # CYP tags (3)
        tag_herb, tag_fat_sol, tag_protective,           # other tags (3)
        min(liver_delta / 3, 1.0),                      # pathway impact per organ (4)
        min(kidney_delta / 3, 1.0),
        min(cardio_delta / 3, 1.0),
        min(meta_delta / 3, 1.0),
        0.0, 0.0,                                        # padding to 16
    ], dtype=np.float32)
    return features  # shape (16,)


class PatientGraph:
    """
    Structured patient graph — works both for GNN (when PyG available)
    and as a structured feature bundle for the rules-based multi-organ scorer.
    """

    def __init__(self, request):
        self.request = request
        self.genetics_dict = {}
        gen = request.genetics
        if gen:
            self.genetics_dict = {
                "cyp2d6_metabolizer": getattr(gen, "cyp2d6_metabolizer", "unknown"),
                "cyp2c19_metabolizer": getattr(gen, "cyp2c19_metabolizer", "unknown"),
                "cyp3a4_metabolizer": getattr(gen, "cyp3a4_metabolizer", "unknown"),
                "cyp2c9_metabolizer": getattr(gen, "cyp2c9_metabolizer", "unknown"),
                "cyp1a2_metabolizer": getattr(gen, "cyp1a2_metabolizer", "unknown"),
                "slco1b1_function": getattr(gen, "slco1b1_function", "unknown"),
                "ugt1a1_function": getattr(gen, "ugt1a1_function", "unknown"),
                "mthfr_c677t": getattr(gen, "mthfr_c677t", "unknown"),
            }

        # Patient features
        self.patient_features = encode_patient_features(request)

        # Per-compound features + gene interactions
        self.compound_data = []
        for item in request.regimen:
            comp_id = item.compound_id
            cg = COMPOUND_INTERACTIONS.get(comp_id, {})
            gene_mult = 1.0
            for gi in cg.get("gene_interactions", []):
                m = get_gene_multiplier(gi, self.genetics_dict)
                if m > gene_mult:
                    gene_mult = m

            self.compound_data.append({
                "compound_id": comp_id,
                "display_name": cg.get("display_name", comp_id),
                "dose_mg": getattr(item, "dose_mg", 300),
                "frequency_per_day": getattr(item, "frequency_per_day", 1),
                "gene_multiplier": gene_mult,
                "pathway_activations": cg.get("pathway_activations", []),
                "gene_interactions": cg.get("gene_interactions", []),
                "risk_tags": cg.get("risk_tags", []),
                "is_protective": cg.get("is_protective", False),
                "features": encode_compound_features(item, self.genetics_dict),
            })

        # Condition data
        self.condition_data = []
        for cond in (getattr(request, "conditions", None) or []):
            cd = CONDITION_ORGAN_PENALTIES.get(cond.condition_id, {})
            severity = getattr(cond, "severity", "mild")
            mult = cd.get("severity_multiplier", {}).get(severity, 1.0)
            organs = cd.get("organs", {})
            self.condition_data.append({
                "condition_id": cond.condition_id,
                "severity": severity,
                "organs": {organ: penalty * mult for organ, penalty in organs.items()},
                "pathway_activations": cd.get("pathway_activations", []),
            })

        # DDIs
        self.ddis = detect_ddis([{"compound_id": item.compound_id} for item in request.regimen])

    def to_hetero_data(self):
        """Convert to PyG HeteroData for GNN inference (if PyG available)."""
        try:
            import torch
            from torch_geometric.data import HeteroData
        except ImportError:
            return None

        data = HeteroData()
        # Patient node (1 patient)
        data["patient"].x = torch.tensor(self.patient_features, dtype=torch.float).unsqueeze(0)

        # Compound nodes
        if self.compound_data:
            feats = torch.tensor(
                np.stack([c["features"] for c in self.compound_data]), dtype=torch.float
            )
            data["compound"].x = feats

            # patient → compound edges
            n_comp = len(self.compound_data)
            src = torch.zeros(n_comp, dtype=torch.long)   # patient 0 → all compounds
            dst = torch.arange(n_comp, dtype=torch.long)
            data["patient", "takes", "compound"].edge_index = torch.stack([src, dst])
        else:
            data["compound"].x = torch.zeros((1, 16), dtype=torch.float)

        # Gene nodes (8 genes)
        gene_feats = np.array([
            [PHENOTYPE_ENCODING.get(self.genetics_dict.get(g, "unknown"), 0.5)] * 8
            for g in GENE_ORDER
        ], dtype=np.float32)
        data["gene"].x = torch.tensor(gene_feats, dtype=torch.float)

        # Disease nodes
        if self.condition_data:
            disease_feats = np.zeros((len(self.condition_data), 6), dtype=np.float32)
            for i, cd in enumerate(self.condition_data):
                disease_feats[i][0] = cd["organs"].get("liver", 0) / 10
                disease_feats[i][1] = cd["organs"].get("kidney", 0) / 10
                disease_feats[i][2] = cd["organs"].get("cardiovascular", 0) / 10
                disease_feats[i][3] = cd["organs"].get("metabolic", 0) / 10
                disease_feats[i][4] = {"mild": 0.33, "moderate": 0.67, "severe": 1.0}.get(cd["severity"], 0.33)
            data["disease"].x = torch.tensor(disease_feats, dtype=torch.float)
        else:
            data["disease"].x = torch.zeros((1, 6), dtype=torch.float)

        # Pathway nodes (14 pathways)
        pathway_feats = np.zeros((len(PATHWAY_GRAPH), 6), dtype=np.float32)
        data["pathway"].x = torch.tensor(pathway_feats, dtype=torch.float)

        return data
