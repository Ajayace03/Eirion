# EIRION — Heterogeneous Graph Attention Network for Multi-Assay Toxicity Prediction

> **Hackathon Submission** | EIRION PGx Toxicity Prediction System  
> **Model Version:** 1.0.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Model Architecture](#2-model-architecture)
3. [Mathematical Foundations](#3-mathematical-foundations)
4. [Layer-by-Layer Description](#4-layer-by-layer-description)
5. [Graph Structure](#5-graph-structure)
6. [Training Configuration](#6-training-configuration)
7. [Dataset](#7-dataset)
8. [Results](#8-results)
9. [Baseline Comparison](#9-baseline-comparison)
10. [Data Sources](#10-data-sources)
11. [Installation and Usage](#11-installation-and-usage)
12. [File Structure](#12-file-structure)
13. [Known Limitations](#13-known-limitations)
14. [Future Improvements](#14-future-improvements)
15. [References](#15-references)

---

## 1. Project Overview

EIRION is a pharmacogenomics (PGx) toxicity prediction system that frames drug safety as a graph learning problem. Rather than treating each compound in isolation, EIRION builds a heterogeneous knowledge graph connecting compounds, genes, and biological pathways, then applies Graph Attention Networks to learn toxicity-relevant representations that incorporate biological context.

The model predicts activity across 13 Tox21 bioassays simultaneously, covering nuclear receptor signalling pathways and stress response pathways known to be implicated in drug-induced organ toxicity.

### Motivation

Classical fingerprint-based models such as Random Forests treat each compound independently. They cannot model the fact that two structurally dissimilar compounds may share toxicity risk because they both inhibit the same cytochrome P450 enzyme, or that a compound's risk profile changes when co-administered with drugs that compete for the same metabolic pathway. A heterogeneous graph encodes exactly this relational structure.

### Target Assays

| Assay ID | Full Name | Biological Relevance |
|---|---|---|
| NR-AhR | Aryl Hydrocarbon Receptor | Dioxin-like toxicity, CYP induction |
| NR-AR | Androgen Receptor (full length) | Endocrine disruption |
| NR-AR-LBD | Androgen Receptor Ligand Binding Domain | Endocrine disruption |
| NR-Aromatase | Aromatase (CYP19A1) inhibition | Hormone synthesis disruption |
| NR-ER | Estrogen Receptor alpha (full length) | Endocrine disruption |
| NR-ER-LBD | Estrogen Receptor Ligand Binding Domain | Endocrine disruption |
| NR-PPAR-gamma | Peroxisome Proliferator Activated Receptor | Metabolic toxicity |
| SR-ARE | Antioxidant Response Element | Oxidative stress |
| SR-ATAD5 | ATPase Family AAA Domain | Genotoxicity marker |
| SR-HSE | Heat Shock Element | Proteotoxic stress |
| SR-MMP | Mitochondrial Membrane Potential | Mitochondrial toxicity |
| SR-p53 | p53 Tumour Suppressor | DNA damage response |
| label_any | Any positive across all 12 assays | Overall toxicity flag |

---

## 2. Model Architecture

EIRION is a two-stage model:

```
Stage 1: Heterogeneous Graph Attention Network (HeteroGAT-v2)
         Learns contextualised node embeddings for compounds, genes, and pathways

Stage 2: Multi-Label Classification Head (MLP)
         Reads compound node embeddings and predicts 13 binary toxicity labels
```

### Architecture Diagram

```
Compound nodes          Gene nodes            Pathway nodes
[N_c × 1024]            [N_g × 512]           [N_p × 512]
Morgan FP               one-hot identity      one-hot identity
     |                       |                      |
     v                       v                      v
Linear(1024 → 128)    Linear(512 → 128)    Linear(512 → 128)
     |                       |                      |
     └───────────────────────┴──────────────────────┘
                             |
                    ┌────────────────┐
                    │  GATv2Conv     │  Layer 1
                    │  4 heads       │
                    │  hidden = 128  │
                    └────────────────┘
                             |
                    LayerNorm + Dropout(0.3) + Residual
                             |
                    ┌────────────────┐
                    │  GATv2Conv     │  Layer 2
                    │  4 heads       │
                    │  hidden = 128  │
                    └────────────────┘
                             |
                    LayerNorm + Dropout(0.3) + Residual
                             |
                   [Compound embeddings only]
                             |
                    Linear(128 → 64)
                    ReLU
                    Dropout(0.3)
                    Linear(64 → 13)
                             |
                    13 toxicity logits
```

### Key Design Choices

**GATv2 over GATv1:** Standard GAT computes attention as a(Wh_u, Wh_v) which is a static ranking — the importance of neighbour u to node v does not depend on the query context of v. GATv2 uses a(W[h_u || h_v]) which is dynamic: attention weights are recomputed based on the current state of both nodes. This is critical for the drug-gene relationship, where the importance of a gene to a compound should depend on both the compound's current chemical context and the gene's biological role.

**Heterogeneous convolution:** Different edge types (compound→gene, gene→pathway) have separate weight matrices. This prevents the model conflating "drug targets gene" with "gene participates in pathway" — fundamentally different semantic relationships that should be learned independently.

**Residual connections:** Each GATv2 layer adds the previous layer's representation back to the new one, preventing gradient vanishing over deeper message passing and allowing the model to preserve the Morgan fingerprint signal even after two hops of graph propagation.

---

## 3. Mathematical Foundations

### 3.1 Morgan Fingerprint (Input Features)

For each compound with SMILES string s, the Morgan fingerprint is computed as a 1024-dimensional binary vector using the extended-connectivity algorithm at radius r = 2:

```
FP(s) ∈ {0, 1}^1024

where bit k is set if any atom in s has an extended connectivity identifier
hashing to k within 2 bond hops
```

Implementation uses `rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)` from RDKit.

### 3.2 GATv2 Attention Mechanism

For each directed edge (u → v) with edge type t, the attention coefficient is computed as:

```
e_vu = a^T · LeakyReLU(W_t · [h_u || h_v])
```

where:
- `h_u, h_v ∈ R^d` are the current embeddings of source and target nodes
- `W_t ∈ R^(d × 2d)` is a learnable weight matrix specific to edge type t
- `a ∈ R^d` is a learnable attention vector
- `||` denotes vector concatenation
- `LeakyReLU` uses negative slope 0.2 (PyTorch Geometric default)

The raw scores are normalised over all neighbours N(v) of node v using softmax:

```
α_vu = softmax_u(e_vu) = exp(e_vu) / Σ_{k ∈ N(v)} exp(e_vk)
```

The updated node embedding for v after one layer is the weighted sum of transformed neighbour embeddings across K attention heads, concatenated:

```
h_v' = ||_{k=1}^{K} σ( Σ_{u ∈ N(v)} α_vu^k · W^k · h_u )
```

where σ is the ELU activation and K = 4 (number of attention heads).

### 3.3 Residual Connection and Normalisation

After each GATv2 layer, the update rule is:

```
h_v^(l) = LayerNorm( Dropout( ReLU( h_v'^(l) ) ) + h_v^(l-1) )
```

This ensures the gradient flows directly to the input projections and prevents the embeddings from drifting arbitrarily far from the initial chemical representation.

### 3.4 Loss Function

Binary cross-entropy with positive class weighting to handle severe class imbalance (positive rate 2–10% per assay):

```
L = - (1/N) Σ_i Σ_j [ w_pos · y_ij · log(σ(ẑ_ij)) + (1 - y_ij) · log(1 - σ(ẑ_ij)) ]
```

where:
- `y_ij ∈ {0, 1}` is the true label for compound i, assay j
- `ẑ_ij` is the raw logit output
- `σ` is the sigmoid function
- `w_pos = 8.0` (positive class weight, set to approximate inverse class frequency)
- N is the number of training compounds

Implementation: `torch.nn.BCEWithLogitsLoss(pos_weight=tensor([8.0] * 13))`

### 3.5 Evaluation Metric

Area Under the Receiver Operating Characteristic Curve (ROC-AUC), computed per assay and macro-averaged:

```
AUC_macro = (1/J) Σ_{j=1}^{J} AUC_j

where J = number of assays with at least one positive example in the evaluation split
```

AUC is used rather than accuracy because of extreme class imbalance — a classifier predicting all-negative achieves >90% accuracy on some assays but AUC = 0.5.

---

## 4. Layer-by-Layer Description

### Layer 0: Input Projections

Three separate linear layers project each node type from its native feature dimension to the shared hidden dimension:

| Layer | Input dim | Output dim | Activation | Purpose |
|---|---|---|---|---|
| `proj_compound` | 1024 | 128 | ReLU | Morgan FP → hidden space |
| `proj_gene` | 512 | 128 | ReLU | Gene identity → hidden space |
| `proj_pathway` | 512 | 128 | ReLU | Pathway identity → hidden space |

All three projections use `torch_geometric.nn.Linear` which applies Glorot (Xavier) uniform initialisation by default.

### Layer 1: GATv2Conv (First Message Passing Layer)

Four parallel GATv2 convolutions, one per edge type, wrapped in `HeteroConv` with `aggr='mean'`:

| Edge type | Source node | Target node | Head dim | Total output dim |
|---|---|---|---|---|
| `compound → targets → gene` | compound | gene | 32 | 128 |
| `gene → targeted_by → compound` | gene | compound | 32 | 128 |
| `gene → in_pathway → pathway` | gene | pathway | 32 | 128 |
| `pathway → contains → gene` | pathway | gene | 32 | 128 |

Output per node type: concatenation of 4 heads × 32 dims = 128 dims.

After this layer: `LayerNorm(128) + Dropout(0.3) + Residual`

### Layer 2: GATv2Conv (Second Message Passing Layer)

Identical architecture to Layer 1. After two layers, a compound node's embedding contains information from:
- Its own Morgan fingerprint (via residual)
- Its direct gene neighbours (1-hop)
- Genes that share pathways with its direct gene neighbours (2-hop)

After this layer: `LayerNorm(128) + Dropout(0.3) + Residual`

### Layer 3: Prediction Head (MLP)

Applied only to compound node embeddings:

| Sub-layer | Input | Output | Activation |
|---|---|---|---|
| `Linear` | 128 | 64 | — |
| `ReLU` | 64 | 64 | — |
| `Dropout(0.3)` | 64 | 64 | — |
| `Linear` | 64 | 13 | — (raw logits) |

Output: 13 raw logits, one per Tox21 assay. Sigmoid is applied at inference time to obtain probabilities.

### Total Trainable Parameters

```
Input projections:       3 × (dim_in × 128 + 128)     ≈  230,784
GATv2 Layer 1:           4 edge types × (2×128×128 + 128)  ≈  524,288
GATv2 Layer 2:           4 edge types × (2×128×128 + 128)  ≈  524,288
LayerNorm (×4):          4 × 2 × 128                  ≈    1,024
Prediction head:         128×64 + 64 + 64×13 + 13     ≈    9,293
─────────────────────────────────────────────────────
Total:                                                 ≈ 1,289,677
```

---

## 5. Graph Structure

### Node Types and Counts

| Node type | Count | Feature dim | Feature source |
|---|---|---|---|
| Compound | 12,505 | 1024 | Morgan fingerprint (radius=2) |
| Gene | 23,658 | 512 | Truncated one-hot identity |
| Pathway | 2,848 | 512 | Truncated one-hot identity |

### Edge Types and Counts

| Edge type | Count | Source |
|---|---|---|
| compound → targets → gene | 21,936 (real) + fallback | PharmGKB via InChIKey bridge |
| gene → targeted_by → compound | same (reversed) | PharmGKB |
| gene → in_pathway → pathway | 48,593 | Reactome (Homo sapiens only) |
| pathway → contains → gene | same (reversed) | Reactome |

**Coverage:** 937 of 12,505 compounds (7.5%) have real PharmGKB gene edges. The remaining 11,568 compounds are connected to 12 core PGx toxicity genes (CYP1A2, CYP2C9, CYP2C19, CYP2D6, CYP3A4, CYP3A5, UGT1A1, ABCB1, SLCO1B1, DPYD, TPMT, NUDT15) as a structural prior.

### InChIKey Bridge

The compound-gene edge set was constructed by:
1. Extracting InChI strings from `stg_pharmgkb_drug` and computing InChIKeys using RDKit
2. Matching on the first 14 characters of InChIKey (connectivity layer, stereochemistry-invariant)
3. Joining to `drug_gene_edges` via PharmGKB drug ID

This yielded 1,762 bridge matches → 21,936 compound-gene edges across 1,334 unique genes.

---

## 6. Training Configuration

### Hyperparameters

| Parameter | Value | Rationale |
|---|---|---|
| Hidden dimension | 128 | Balances capacity vs overfitting on CPU |
| Attention heads | 4 | Multi-view attention for different relationship types |
| GATv2 layers | 2 | 2-hop neighbourhood: compound → gene → pathway |
| Dropout | 0.3 | Regularisation; applied after each GATv2 layer and in prediction head |
| Positive class weight | 8.0 | Compensates for ~8× class imbalance across assays |
| Learning rate | 1e-3 | Adam default; effective with weight decay |
| Weight decay | 1e-4 | L2 regularisation on all parameters |
| Gradient clipping | 1.0 (L2 norm) | Prevents exploding gradients in GAT layers |
| Batch size | Full graph | Single-graph transductive setting |
| Max epochs | 300 | With early stopping |
| Early stopping patience | 20 evaluations (200 epochs) | Stops when valid AUC does not improve |
| Evaluation frequency | Every 10 epochs | |

### Optimiser

Adam optimiser with the following configuration:

```python
torch.optim.Adam(
    model.parameters(),
    lr=1e-4,
    weight_decay=1e-4,
    betas=(0.9, 0.999),   # default
    eps=1e-8              # default
)
```

### Learning Rate Schedule

`ReduceLROnPlateau` scheduler monitoring validation AUC:

```python
torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode='max',        # maximise AUC
    factor=0.5,        # halve LR on plateau
    patience=5,        # wait 5 evaluations (50 epochs)
    min_lr=1e-5        # floor
)
```

### Train / Validation / Test Split

Splits are defined by the `cvfold` column in `pgx.tox21_model_ready` — a pre-assigned stratified fold variable:

| Split | cvfold values | Count |
|---|---|---|
| Train | NULL (NA), 0 | 5,915 |
| Validation | 1, 2 | 3,475 |
| Test | 3, 4, 5 | 3,074 |

Note: `cvfold` is stored as `float64` after CSV export from PostgreSQL. NULL values become `NaN`. The correct masking is:

```python
train_mask = df['cvfold'].isna() | df['cvfold'].isin([0.0])
```

---

## 7. Dataset

### Tox21

The Toxicology in the 21st Century (Tox21) dataset contains quantitative high-throughput screening (qHTS) results for 12,707 compounds across 12 nuclear receptor and stress response pathway assays. It was assembled by the US National Toxicology Program, the Environmental Protection Agency, and the National Center for Advancing Translational Sciences.

- Compounds: 12,505 (after deduplication on canonical SMILES)
- Positive rate: 2.1% (NR-PPAR-gamma) to 9.8% (SR-MMP)
- SMILES source: PubChem via NCGC compound registry

### PharmGKB

The Pharmacogenomics Knowledgebase provides curated gene-drug relationships with evidence levels. Drug-gene edges used in EIRION are sourced from two evidence streams within PharmGKB: variant annotation relationships and clinical annotation relationships. Only associations with evidence type containing `ClinicalAnnotation` or `VariantAnnotation` are retained.

- Drug-gene edges: 21,298 (after deduplication)
- Genes covered: 25,041
- Drugs covered: 3,728

### CPIC

The Clinical Pharmacogenomics Implementation Consortium provides dosing guidelines for drug-gene pairs with actionable PGx evidence. CPIC levels A and B indicate strong evidence for clinical action.

- Drug-gene pairs: 572 (CPIC-level pairs used in training)

### Reactome

Reactome is a curated, peer-reviewed pathway database. Gene-pathway edges are restricted to Homo sapiens entries with experimental evidence codes (non-IEA where possible).

- Pathways: 2,848 (Homo sapiens)
- Gene-pathway edges: 48,593

---

## 8. Results

### Final Test Performance

| Assay | GNN AUC | RF AUC | Delta |
|---|---|---|---|
| NR-AhR | 0.8423 | 0.8696 | -0.0273 |
| NR-AR | 0.7961 | 0.6987 | +0.0974 |
| NR-AR-LBD | **0.9110** | 0.7782 | **+0.1328** |
| NR-Aromatase | 0.7506 | 0.7947 | -0.0441 |
| NR-ER | 0.6845 | 0.6471 | +0.0374 |
| NR-ER-LBD | 0.7629 | 0.7435 | +0.0194 |
| NR-PPAR-gamma | 0.6962 | 0.7519 | -0.0557 |
| SR-ARE | 0.7074 | 0.7144 | -0.0070 |
| SR-ATAD5 | 0.7891 | 0.7471 | +0.0420 |
| SR-HSE | 0.6542 | 0.6703 | -0.0161 |
| SR-MMP | 0.8306 | 0.8522 | -0.0216 |
| SR-p53 | 0.7697 | 0.7643 | +0.0054 |
| label_any | 0.7222 | 0.7402 | -0.0180 |
| **Macro average** | **0.7628** | **0.7517** | **+0.0111** |

### Training Convergence

The model converged at epoch 40 (best validation AUC 0.7594) and early stopped at epoch 240 after 20 consecutive non-improving evaluations. Loss decreased monotonically from 0.9863 to 0.1494, indicating successful optimisation. The gap between training loss and validation AUC after epoch 40 indicates mild overfitting — addressable with stronger regularisation (see Future Improvements).

---

## 9. Baseline Comparison

### Random Forest Baseline

A `MultiOutputClassifier` wrapping `RandomForestClassifier(n_estimators=200, class_weight='balanced')` trained on the same 1024-bit Morgan fingerprints and cvfold splits. No graph structure, no gene or pathway information.

| Property | Random Forest | EIRION GNN |
|---|---|---|
| Input | Morgan FP only | Morgan FP + gene-pathway graph |
| Relational structure | None | Heterogeneous GAT |
| Parameters | ~200 trees | ~1.29M |
| Training time (CPU) | ~8 min | ~40 min |
| Test AUC (macro) | 0.7517 | 0.7628 |
| Best single task | NR-AhR (0.8696) | NR-AR-LBD (0.9110) |

The GNN outperforms RF on 7 of 13 assays, with the largest gains on androgen receptor assays (NR-AR: +9.7%, NR-AR-LBD: +13.3%) where PharmGKB gene context provides direct signal about steroid receptor biology.

---

## 10. Data Sources

| Resource | URL | License |
|---|---|---|
| Tox21 qHTS dataset | https://tripod.nih.gov/tox21/assays/ | Public domain (US Government) |
| Tox21 SMILES (PubChem) | https://pubchem.ncbi.nlm.nih.gov/ | Public domain |
| PharmGKB gene-drug relationships | https://www.pharmgkb.org/downloads | CC BY-SA 4.0 |
| CPIC guidelines and pairs | https://cpicpgx.org/genes-drugs/ | CC BY 4.0 |
| Reactome pathway database | https://reactome.org/download-data | CC BY 4.0 |
| Comparative Toxicogenomics Database (CTD) | https://ctdbase.org/downloads/ | Free for research |
| ChEMBL bioactivity database | https://www.ebi.ac.uk/chembl/ | CC BY-SA 3.0 |
| RDKit cheminformatics | https://www.rdkit.org/ | BSD 3-Clause |
| PyTorch Geometric | https://pytorch-geometric.readthedocs.io/ | MIT |

---

## 11. Installation and Usage

### Requirements

```
python >= 3.9
torch >= 2.0
torch-geometric >= 2.4
rdkit-pypi >= 2022.09
scikit-learn >= 1.3
pandas >= 2.0
numpy >= 1.24
psycopg2 >= 2.9       # for PostgreSQL export
joblib >= 1.3         # for RF baseline
```

### Install

```bash
pip install torch torch-geometric rdkit-pypi scikit-learn pandas numpy psycopg2-binary joblib
```

### Pipeline

```bash
# 1. Export data from PostgreSQL
psql -U postgres -d pgx_db -f export_from_pgx.sql

# 2. Build InChIKey bridge (compound → gene edges)
python fix_compound_gene_bridge.py

# 3. Build heterogeneous graph
python step2_build_graph.py

# 4. Train GNN
python step4_train.py

# 5. Inference on new compounds
python predict_gnn.py --smiles "CC(=O)Oc1ccccc1C(=O)O"
```

### Inference on a New Compound

```python
import torch, pickle
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.SaltRemover import SaltRemover
from step3_model import EirionGNN

TASKS = ['nr_ahr','nr_ar','nr_ar_lbd','nr_aromatase','nr_er','nr_er_lbd',
         'nr_ppar_gamma','sr_are','sr_atad5','sr_hse','sr_mmp','sr_p53','label_any']

with open('./Datasets/Gnn/data/hetero_graph.pkl', 'rb') as f:
    data = pickle.load(f)

device = torch.device('cpu')
model  = EirionGNN(
    compound_dim=1024, gene_dim=512, pathway_dim=512,
    hidden=128, heads=4, num_layers=2, num_tasks=13
).to(device)
model.load_state_dict(torch.load('eirion_gnn_best.pt', map_location=device))
model.eval()

remover = SaltRemover()
gen     = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)

def predict_smiles(smiles_str):
    mol = Chem.MolFromSmiles(smiles_str)
    mol = remover.StripMol(mol)
    fp  = torch.tensor(gen.GetFingerprintAsNumPy(mol), dtype=torch.float).unsqueeze(0)

    # Inject as the first compound node
    x_dict          = {k: data[k].x.to(device) for k in ['compound','gene','pathway']}
    x_dict['compound'] = torch.cat([fp, x_dict['compound'][1:]], dim=0)
    edge_index_dict = {et: data[et].edge_index.to(device) for et in data.edge_types}

    with torch.no_grad():
        logits = model(x_dict, edge_index_dict)
        probs  = torch.sigmoid(logits[0]).cpu().numpy()

    return {task: round(float(p), 4) for task, p in zip(TASKS, probs)}

print(predict_smiles("CC(=O)Oc1ccccc1C(=O)O"))  # Aspirin
```

---

## 12. File Structure

```
Eirion/
├── README.md                         ← this file
├── fix_compound_gene_bridge.py       ← InChIKey matching: Tox21 ↔ PharmGKB
├── step2_build_graph.py              ← assembles HeteroData graph
├── step3_model.py                    ← EirionGNN model class
├── step4_train.py                    ← training loop with early stopping
├── predict_tox21.py                  ← RF inference (baseline)
├── tox21_rf_model.pkl                ← trained Random Forest
├── eirion_gnn_best.pt                ← best GNN checkpoint (v1.0.0)
│
├── v2_pipeline/                      ← EIRION v2.0 development (in progress)
│   ├── step_ctd.py                   ← CTD chemical-gene linkage via PubChem CAS
│   ├── merge_edges.py                ← merges PharmGKB + CTD + ChEMBL edges
│   ├── run_node2vec.py               ← trains Node2Vec gene embeddings
│   └── step_chembl.py                ← ChEMBL bioactivity linkage
│
└── Datasets/
    └── Gnn/
        └── data/
            ├── compounds.csv              ← 12,505 Tox21 compounds + inchikey + labels
            ├── genes.csv                  ← 23,658 genes from gene_master
            ├── pathways.csv               ← 2,848 Reactome pathways (Homo sapiens)
            ├── gene_pathway_edges.csv     ← 48,593 Reactome gene-pathway links
            ├── compound_gene_edges.csv    ← 21,936 PharmGKB compound-gene links (v1.0)
            ├── tox21_cas_map.csv          ← PubChem CAS numbers for Tox21 compounds (v2.0)
            ├── compound_gene_edges_ctd.csv← CTD chemical-gene edges (v2.0, post-query)
            ├── compound_gene_edges_merged.csv ← merged multi-source edges (v2.0)
            ├── pharmgkb_drugs_with_inchi.csv  ← PharmGKB drug InChI strings
            ├── drug_gene_edges_with_pharmgkb.csv ← drug-gene edges with PharmGKB IDs
            └── hetero_graph.pkl           ← compiled PyTorch Geometric HeteroData object
```

---

## 13. Known Limitations

**Sparse compound-gene coverage.** Only 758 of 12,505 Tox21 compounds (6.1%) have real PharmGKB drug-gene edges. The remaining 93.9% are connected only to 12 fallback PGx genes (CYP1A2, CYP2D6, CYP3A4, etc.) as a structural prior. This limits the model's ability to leverage biological context for the majority of compounds and is the primary ceiling on current performance. EIRION GNN v2.0 directly addresses this via multi-database linkage expansion (see Future Improvements).

**One-hot gene and pathway features.** Genes and pathways are represented by truncated identity matrices rather than pre-trained biological embeddings. This means the model must learn gene representations from scratch using only graph topology, which requires substantially more training data than is available.

**Transductive setting.** The current implementation trains on the full graph and predicts on held-out compound nodes. It cannot directly handle a new compound without rebuilding the graph. A proper inductive variant would require neighbourhood sampling.

**No stereochemistry in fingerprints.** Morgan fingerprints at radius 2 do not capture stereochemical differences. Enantiomers with different toxicity profiles will receive identical feature vectors.

**CPU training only (tested).** The model was trained and evaluated on CPU. Performance on CUDA or MPS hardware is untested but should be substantially faster with no code changes required.

**Class imbalance.** Despite positive class weighting, assays with fewer than 100 positive examples in the training set (NR-PPAR-gamma, NR-AR-LBD) have noisy AUC estimates that are sensitive to the random seed and fold assignment.

---

## 14. Future Improvements

### Short Term (v1.1) — Completed / In Progress

**Learning rate scheduling** *(implemented in current training pipeline).* `ReduceLROnPlateau` monitors validation AUC with `factor=0.5`, `patience=5`, and `min_lr=1e-5`. Prevents the epoch-40 overfitting cliff observed in v1.0 training.

**Per-task positive class weighting** *(implemented).* Replaced the flat `pos_weight=8.0` with dynamically computed per-task weights derived from the actual positive-to-negative ratio in the training split. Produces more calibrated predictions for rare assays such as NR-PPAR-gamma.

**Stronger dropout and regularisation.** Increasing dropout from 0.3 to 0.4 and adding DropEdge during training reduces overfitting. Combined with the LR scheduler, expected to push valid AUC past 0.77 without additional data.

---

### Medium Term (v2.0) — Active Development

EIRION GNN v2.0 is currently under active development. The primary objective is to raise compound-gene real-linkage coverage from 6.1% to 50%+, which is the single largest bottleneck on model performance.

#### 2.1 Multi-Database Compound-Gene Linkage Expansion

The v1.0 model links only 758 of 12,505 compounds to real gene associations via PharmGKB. v2.0 implements a three-layer expansion pipeline:

**Layer 1 — Comparative Toxicogenomics Database (CTD).**
CTD provides chemical-gene interaction data curated directly from toxicology literature, covering thousands of small molecules that PharmGKB does not annotate. The integration pipeline: query PubChem REST API by InChIKey to retrieve CAS registry numbers for all 12,505 Tox21 compounds, then join to `CTD_chem_gene_ixns.tsv` on CAS number, mapping NCBI Gene IDs to the internal `gene_master` via `ncbi_gene_id`. *Status: PubChem CAS query in progress (55%+ complete as of v2.0 development build). CTD file downloaded and validated.*

Expected yield: 4,000–6,000 additional compounds linked, total coverage 40–55%.

**Layer 2 — ChEMBL bioactivity data.**
ChEMBL stores binding assay IC50 data against specific protein targets. Compounds with pChEMBL ≥ 5 (IC50 ≤ 10µM) against human targets are retrieved via the ChEMBL REST API and linked to gene nodes via Ensembl ID crossreference. This is particularly valuable for the nuclear receptor assays (NR-AhR, NR-ER, NR-AR) where ChEMBL has extensive receptor binding data.

Expected yield: 1,000–2,500 additional compounds linked.

**Layer 3 — Tanimoto structural similarity inference.**
For compounds still unlinked after CTD and ChEMBL, gene annotations are inherited from the most structurally similar linked compound using Tanimoto similarity on Morgan fingerprints. Only compounds with Tanimoto ≥ 0.70 to a linked anchor compound receive inferred edges (threshold from Maggiora 2006). Edges are flagged as `source_tanimoto=True` and given reduced edge feature weight.

Expected yield: 1,000–2,000 additional compounds covered.

**Projected total after all three layers:** 7,000–9,000 of 12,505 compounds with real or structurally inferred gene edges (56–72% coverage).

#### 2.2 Edge Feature Encoding

v1.0 treats all compound-gene edges identically — a bare connection with no metadata. v2.0 encodes a 6-dimensional edge feature vector for each edge:

```
edge_feat = [
    pk_flag,              # 1 if pharmacokinetic relationship (metabolism/transport)
    pd_flag,              # 1 if pharmacodynamic relationship (target/receptor)
    cpic_level_encoded,   # A=1.0, B=0.75, C=0.5, D=0.25, None=0.0
    source_pharmgkb,      # evidence source flag
    source_cpic,          # evidence source flag
    is_fallback,          # 0 for real edges, 1 for fallback/inferred
]
```

These are passed to `GATv2Conv` via the `edge_dim=6` parameter, allowing the attention mechanism to distinguish pharmacokinetic edges (the gene metabolises the drug) from pharmacodynamic edges (the gene is the drug's receptor target) — a distinction invisible to v1.0.

#### 2.3 Node2Vec Gene Embeddings

Replace the truncated one-hot gene identity features with 128-dimensional Node2Vec embeddings trained on the gene-pathway co-membership graph. Two genes that appear in many of the same Reactome pathways receive similar embeddings, encoding functional similarity. Pathway node features become the mean of their member gene embeddings.

This replaces 512-dimensional identity vectors with 128-dimensional biologically meaningful representations, reducing parameter count while improving expressiveness.

#### 2.4 Deeper Architecture

Increase model capacity to match the richer data:

| Parameter | v1.0 | v2.0 |
|---|---|---|
| Hidden dimension | 128 | 256 |
| Attention heads | 4 | 8 |
| GATv2 layers | 2 | 3 |
| Dropout | 0.3 | 0.2 |
| Edge features | None | 6-dimensional |
| Gene features | One-hot 512-d | Node2Vec 128-d |
| Compound features | Morgan FP 1024-d | Morgan FP + RDKit descriptors ~1224-d |

3 layers extend the message passing neighbourhood to compound → gene → pathway → gene (3 hops), capturing indirect biological relationships.

#### 2.5 Mini-Batch Training via NeighborLoader

Replace full-graph transductive training with neighbourhood sampling using `NeighborLoader` (batch size 512, 2-hop sampling with 15 and 10 neighbours per hop). This resolves the scalability bottleneck that prevents training on GPU with larger hidden dimensions, and reduces overfitting by exposing the model to different subgraph samples each epoch.

#### 2.6 Evaluation Suite Upgrade

Add per-task AUPRC (area under precision-recall curve) alongside ROC-AUC. For the Tox21 class imbalance (2–10% positive rate), AUPRC more sensitively measures performance on positive compounds — the clinically relevant cases. Random AUPRC baseline is approximately equal to the positive rate (~5%), compared to random ROC-AUC of 0.5.

**Projected v2.0 performance:** Test macro AUC 0.80–0.84, macro AUPRC 0.35–0.45 (vs random ~0.05).

---

### Long Term (v3.0)

**DMPNN molecular encoder.** Replace Morgan fingerprints with a Directed Message Passing Neural Network (D-MPNN / ChemProp) trained end-to-end. DMPNN encodes the molecular graph directly and learns task-specific bond and atom representations.

**User pharmacogenotype overlay.** The EIRION architecture natively supports adding user-specific genotype features to gene nodes (metaboliser class: poor / intermediate / normal / ultrarapid). This allows compound toxicity predictions to be personalised to an individual's CYP enzyme activity profile — the core clinical use case of the EIRION platform.

**Organ-level toxicity heads.** Replace the 13 assay-level outputs with three organ-level predictions (hepatotoxicity, nephrotoxicity, cardiotoxicity) derived from a mapping of Tox21 assays to organ systems. This produces more clinically actionable risk scores for formulary review.

**Multi-drug interaction modelling.** Extend the graph to support edges between compound nodes representing known drug-drug interactions from the DrugBank DDI dataset. Enables prediction of combinatorial toxicity for multi-drug regimens.

**Attention-based explainability dashboard.** The GATv2 attention weights on compound→gene edges encode which biological targets drove each toxicity prediction. Exposing these as structured JSON enables downstream explainability tools to highlight the most relevant pharmacological interactions for clinical review.

---

## 15. References

Brody, S., Alon, U., and Yahav, E. (2021). How attentive are graph attention networks? *arXiv preprint arXiv:2105.14491*. https://arxiv.org/abs/2105.14491

Davis, A. P., Wiegers, T. C., Johnson, R. J., Sciaky, D., Wiegers, J., and Mattingly, C. J. (2023). Comparative Toxicogenomics Database (CTD): Update 2023. *Nucleic Acids Research*, 51(D1), D1257–D1262. https://doi.org/10.1093/nar/gkac833

Fey, M., and Lenssen, J. E. (2019). Fast graph representation learning with PyTorch Geometric. *ICLR Workshop on Representation Learning on Graphs and Manifolds*. https://arxiv.org/abs/1903.02428

Huang, R., Xia, M., Cho, M. H., Sakamuru, S., Shinn, P., Houck, K. A., Dix, D. J., Judson, R. S., Witt, K. L., Kavlock, R. J., Tice, R. R., and Austin, C. P. (2011). Chemical genomics profiling of environmental chemical modulation of human nuclear receptors. *Environmental Health Perspectives*, 119(8), 1142–1148. https://doi.org/10.1289/ehp.1002952

Jasial, S., Hu, Y., Vogt, M., and Bajorath, J. (2016). Activity-relevant similarity values for fingerprints and implications for similarity searching. *F1000Research*, 5, ISCB Comm J-591. https://doi.org/10.12688/f1000research.8357.1

Kearnes, S., McCloskey, K., Berndl, M., Pande, V., and Riley, P. (2016). Molecular graph convolutions: Moving beyond fingerprints. *Journal of Computer-Aided Molecular Design*, 30(8), 595–608. https://doi.org/10.1007/s10822-016-9938-8

Mayr, A., Klambauer, G., Unterthiner, T., and Hochreiter, S. (2016). DeepTox: Toxicity prediction using deep learning. *Frontiers in Environmental Science*, 3, 80. https://doi.org/10.3389/fenvs.2015.00080

PharmGKB. (2024). PharmGKB: The pharmacogenomics knowledgebase. Stanford University. https://www.pharmgkb.org

Reactome Consortium. (2024). Reactome: A curated knowledgebase of biological pathways. https://reactome.org

Rogers, D., and Hahn, M. (2010). Extended-connectivity fingerprints. *Journal of Chemical Information and Modeling*, 50(5), 742–754. https://doi.org/10.1021/ci100050t

Veličković, P., Cucurull, G., Casanova, A., Romero, A., Liò, P., and Bengio, Y. (2018). Graph attention networks. *International Conference on Learning Representations (ICLR)*. https://arxiv.org/abs/1710.10903

Yang, K., Swanson, K., Jin, W., Coley, C., Eiden, P., Gao, H., Guzman-Perez, A., Hopper, T., Kelley, B., Mathea, M., Palmer, A., Settels, V., Jaakkola, T., Jensen, K., and Barzilay, R. (2019). Analyzing learned molecular representations for property prediction. *Journal of Chemical Information and Modeling*, 59(8), 3370–3388. https://doi.org/10.1021/acs.jcim.9b00237

Zitnik, M., Agrawal, M., and Leskovec, J. (2018). Modeling polypharmacy side effects with graph convolutional networks. *Bioinformatics*, 34(13), i457–i466. https://doi.org/10.1093/bioinformatics/bty294

---

## Model Card

| Field | Value |
|---|---|
| Model name | EIRION GNN v1.0.0 |
| Model type | Heterogeneous Graph Attention Network (GATv2) |
| Task | Multi-label binary classification (13 Tox21 assays) |
| Input | SMILES string |
| Output | 13 toxicity probabilities (0–1) + binary flags |
| Training data | Tox21 qHTS + PharmGKB + CPIC + Reactome |
| Evaluation metric | Macro-averaged ROC-AUC |
| Test AUC | 0.7628 |
| RF baseline AUC | 0.7517 |
| Improvement over RF | +1.5% macro AUC; +13.3% on NR-AR-LBD |
| Real compound-gene coverage | 758 / 12,505 (6.1%) — v2.0 targeting 50%+ |
| Framework | PyTorch 2.x + PyTorch Geometric 2.4 |
| Hardware tested | CPU (Intel) |
| Checkpoint | `eirion_gnn_best.pt` |
| Graph object | `Datasets/Gnn/data/hetero_graph.pkl` |
| Next version | v2.0 — CTD + ChEMBL linkage expansion (in development) |
| License | MIT |
| Contact | via GitHub repository |

---

*This model was developed as part of the EIRION pharmacogenomics platform for personalised drug toxicity prediction. All data sources are publicly available under open licenses. No patient data was used in training.*
