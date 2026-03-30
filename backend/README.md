# EIRION Backend — FastAPI + GNN + Gemini AI

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.11-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

*The backend API server powering EIRION's pharmacogenomics analysis engine*

</div>

---

## Overview

The EIRION backend is a **FastAPI application** that serves as the intelligence layer of the precision longevity platform. It runs a multi-stage inference pipeline combining:

1. **Deterministic pharmacokinetic scoring** — CYP450-adjusted organ load calculations
2. **GATv2 Graph Neural Network** — 1.29M parameter heterogeneous GNN for toxicity prediction
3. **Google Gemini 2.5 Flash** — Patient-contextualised clinical recommendation generation
4. **ReportLab PDF engine** — 9-page clinical handout generation

---

## Table of Contents

- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Engine Pipeline](#engine-pipeline)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Database Schema](#database-schema)
- [GNN Model](#gnn-model)
- [Configuration](#configuration)
- [Docker](#docker)
- [Testing](#testing)
- [Dependencies](#dependencies)

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │     FastAPI Application      │
                    │   (main.py — 11 routers)     │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
    ┌─────┴─────┐    ┌────────┴────────┐   ┌───────┴──────┐
    │  Routers   │    │   Engine Layer  │   │   Database   │
    │ (11 files) │    │  (10 modules)   │   │ (Prisma/SQL) │
    └─────┬─────┘    └────────┬────────┘   └───────┬──────┘
          │                    │                     │
          │        ┌───────────┼───────────┐         │
          │        │           │           │         │
          │   ┌────┴───┐ ┌────┴───┐ ┌─────┴────┐    │
          │   │Scorer  │ │  GNN   │ │ Gemini   │    │
          │   │(887 ln)│ │(1.29M) │ │ 2.5 Flash│    │
          │   └────────┘ └────────┘ └──────────┘    │
          │                    │                     │
          │              ┌─────┴─────┐               │
          │              │    PDF    │               │
          │              │ Generator │               │
          │              │ (47K)     │               │
          │              └───────────┘               │
          └──────────────────┴───────────────────────┘
```

---

## Directory Structure

```
backend/
├── main.py                    # App bootstrap, lifespan, CORS, scheduler, router mounting
├── database.py                # Prisma async connection manager (connect_db / disconnect_db)
├── auth.py                    # JWT token creation/verification + bcrypt password hashing
├── schema.prisma              # SQLite schema — User, UserAttributes, TrajectoryHistory
├── requirements.txt           # Pinned Python dependencies (44 packages)
├── Dockerfile                 # Production container (Python 3.11-slim + torch CPU)
├── dev.db                     # SQLite development database
├── .env.example               # Environment variable template
│
├── engine/                    # ═══ THE BRAIN — Core inference pipeline ═══
│   ├── __init__.py            # Engine package init
│   ├── scorer.py              # 🏆 PRIMARY: Multi-organ scoring engine (887 lines)
│   │                          #   - validate_and_normalize()
│   │                          #   - compute_compound_load() — per-compound with CYP multipliers
│   │                          #   - compute_lifestyle_penalties() — sleep, stress, alcohol, etc.
│   │                          #   - compute_food_penalty() — diet type, processed food, fiber
│   │                          #   - aggregate_liver_index() — clamp(100 - loads, 40, 100)
│   │                          #   - assign_risk_band() — green/amber/red classification
│   │                          #   - compute_trajectory() — 6-point yearly projection
│   │                          #   - generate_recommendations() — rule-based + fallback
│   │                          #   - compute_recommendation_delta() — hypothetical re-run
│   │                          #   - compute_multi_organ_data() — knowledge graph → 4-organ scores
│   │                          #   - run_liver_analysis() — master orchestrator
│   │
│   ├── gnn_model.py           # EirionGNN model class (GATv2 HeteroConv)
│   │                          #   - 1.29M parameters
│   │                          #   - 2-layer GATv2 with 4 attention heads
│   │                          #   - Hidden dim 128, residual + LayerNorm + Dropout(0.3)
│   │                          #   - 13-output MLP classifier (Tox21 bioassays)
│   │
│   ├── inference.py           # GNN predictor singleton
│   │                          #   - Loads eirion_gnn_best.pt on startup
│   │                          #   - predict_toxicity(smiles) → float (0-1 probability)
│   │                          #   - SMILES → Morgan FP → GNN forward → sigmoid
│   │
│   ├── knowledge.py           # Static knowledge tables (19K)
│   │                          #   - LIVER_LOAD_TABLE: ~50 compounds with base scores, tags, SMILES
│   │                          #   - GENE_DRUG_RULES: CYP metabolizer × tag → multiplier
│   │                          #   - Lifestyle penalty thresholds (sleep, alcohol, sugar, etc.)
│   │                          #   - RECOMMENDATION_RULES: trigger functions + clinical advice
│   │                          #   - FOOD_RECOMMENDATION_RULES: diet-specific triggers
│   │
│   ├── knowledge_graph.py     # Compound→Gene→Pathway knowledge graph (28K)
│   │                          #   - PATHWAY_GRAPH: pathway_id → organs + severity
│   │                          #   - COMPOUND_INTERACTIONS: compound → gene interactions + pathways
│   │                          #   - build_pathway_chain(): compound → gene → pathway → organ
│   │                          #   - detect_ddis(): pairwise DDI detection
│   │                          #   - get_gene_multiplier(): CYP phenotype → multiplier
│   │
│   ├── graph_builder.py       # PatientGraph builder (12K)
│   │                          #   - Constructs patient-specific graph from AnalysisRequest
│   │                          #   - Resolves compound data, condition data, genetics dict
│   │
│   ├── projector.py           # Multi-organ trajectory projector (11K)
│   │                          #   - compute_multi_organ_projection()
│   │                          #   - Per-organ timeframe projections (6m, 1yr, 2yr, 5yr)
│   │                          #   - Confidence bands widening over time
│   │                          #   - Guideline-grounded recommendations per organ
│   │
│   ├── gemini_recs.py         # Gemini 2.5 Flash enrichment (14K)
│   │                          #   - _build_system_prompt(): clinical AI persona
│   │                          #   - _build_patient_context(): full CYP panel + labs + regimen
│   │                          #   - _build_full_analysis_prompt(): batch all recs in one call
│   │                          #   - enrich_recommendations_with_gemini(): main entry point
│   │
│   ├── pdf_generator.py       # 9-page ReportLab PDF generator (47K)
│   │                          #   - Demographics page
│   │                          #   - Lab values (LFT + KFT + Metabolic/Cardiac)
│   │                          #   - Pharmacogenomics profile
│   │                          #   - Multi-organ scorecard
│   │                          #   - Trajectory charts
│   │                          #   - DDI flags
│   │                          #   - Recommendations
│   │                          #   - Clinical disclaimer
│   │
│   ├── weights/               # Trained model checkpoints
│   │   └── eirion_gnn_best.pt # GATv2 GNN checkpoint (2.17 MB)
│   │                          # Best valid AUC: 0.7594, saved at epoch 40
│   │
│   └── planned/               # Phase 2/3 modules (designed, not yet live)
│       ├── __init__.py
│       ├── bio_age_tracker.py           # Advanced biological age tracking (14K)
│       ├── dmpnn_toxicity.py            # D-MPNN molecular toxicity encoder (12K)
│       ├── gatv2_drug_gene_organ.py     # Extended GATv2 drug→gene→organ (10K)
│       ├── multi_organ_expansion.py     # Expanded organ system support (2K)
│       ├── rl_regimen_optimizer.py      # RL (SAC/PPO) regimen optimizer (13K)
│       ├── tft_forecasting.py           # Temporal Fusion Transformer forecasting (16K)
│       └── wearable_fhir_integration.py # FHIR R4 + Oura/Apple Health sync (22K)
│
├── models/                    # ═══ Pydantic v2 Data Models ═══
│   ├── __init__.py
│   ├── request.py             # AnalysisRequest (200 lines)
│   │                          #   - Patient (age, sex, weight, height, ethnicity)
│   │                          #   - Condition (condition_id, severity, diagnosed)
│   │                          #   - ExtendedGenetics (7 CYP enzymes + MTHFR + diplotypes)
│   │                          #   - LifestyleIntake (15 parameters)
│   │                          #   - Food (calories, processed %, red meat, fiber, diet type)
│   │                          #   - RegimenItem (compound, dose, frequency, timing, Rx flag)
│   │                          #   - Labs (16 lab markers across LFT/KFT/metabolic/cardiac)
│   │                          #   - AnalysisRequest (root — combines all above)
│   │
│   └── response.py            # AnalysisResponse (143 lines)
│                              #   - OrganScore (organ, score, risk_level, primary_driver)
│                              #   - CompoundGeneChain (compound → genes → pathways → organs)
│                              #   - DDIFlag (compound_a, compound_b, mechanism, recommendation)
│                              #   - RiskSummary, TrajectoryPoint, Contribution
│                              #   - Recommendation (action_type, details, expected_improvement)
│                              #   - MultiOrganProjection (4-organ, multi-timeframe)
│                              #   - AnalysisResponse (root — combines all above)
│
├── routers/                   # ═══ API Endpoints — 11 routers ═══
│   ├── __init__.py
│   ├── analysis.py            # POST /analysis/run — main inference endpoint
│   │                          # POST /analysis/extract-genetics — Gemini PDF extraction
│   ├── users.py               # POST /register, /login | GET/PATCH /me | POST /change-password
│   ├── export.py              # GET /export/clinical-pdf — authenticated PDF download
│   ├── extraction.py          # POST /extraction/parse-labs — Gemini Vision lab OCR
│   ├── notifications.py       # GET /notifications | PATCH /notifications/{id}/read
│   ├── history.py             # GET /history — trajectory history
│   ├── chat.py                # POST /chat/message — Gemini conversational AI
│   ├── labs.py                # GET /labs — stored lab values
│   ├── billing.py             # GET /billing/status — subscription management
│   ├── wearables.py           # GET /wearables/sync — Oura wearable sync
│   └── health.py              # GET /health — health check
│
├── data/                      # ═══ Static Reference Data ═══
│   ├── snp_pgx_map.json       # rsID → star-allele → metabolizer phenotype (CPIC-sourced)
│   └── mock_response.json     # Fallback response for dev/demo mode
│
└── tests/                     # ═══ Test Suite ═══
    ├── __init__.py
    └── test_engine.py          # Scoring engine unit tests (17K, ~400 lines)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- [Gemini API Key](https://aistudio.google.com/) (for AI recommendations + lab OCR)

### Installation

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate
# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Generate Prisma client
prisma generate --schema=schema.prisma

# Create/migrate database
prisma db push --schema=schema.prisma
```

### Running

```bash
# Development (with hot reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

> ⚡ **API:** `http://localhost:8000`  
> 📖 **Swagger Docs:** `http://localhost:8000/docs`  
> 📖 **ReDoc:** `http://localhost:8000/redoc`

---

## Engine Pipeline

The main analysis endpoint (`POST /analysis/run`) orchestrates a multi-stage pipeline:

```
AnalysisRequest
       │
       ▼
┌─ Step 1: validate_and_normalize() ──────────────────┐
│  Pydantic v2 validation + domain normalization      │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 2: compute_compound_load() ───────────────────┐
│  For each regimen compound:                          │
│  • Look up base hepatic load from LIVER_LOAD_TABLE   │
│  • Apply dose factor: clamp(dose / dose_normal, 0.5-2.0) │
│  • Apply CYP genetic multiplier (GENE_DRUG_RULES)   │
│  • [ML] GNN toxicity prediction modulates base ±50% │
│  • Identify protective compounds (negative load)     │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 3: compute_lifestyle_penalties() ─────────────┐
│  Quantify organ stress from:                         │
│  • Sugar intake, alcohol, sleep quality              │
│  • Exercise level, stress, environmental toxins      │
│  • Processed food percentage, diet type              │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 4: aggregate_liver_index() ───────────────────┐
│  liver_index = clamp(100 - sum_of_loads, 40, 100)   │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 5: assign_risk_band() + compute_trajectory() ─┐
│  Green (≥75) / Amber (≥55) / Red (<55)              │
│  6-point yearly trajectory [year 0 → year 5]        │
│  Lab elevation bumps decline fraction               │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 6: generate_recommendations() ────────────────┐
│  Rule-based recommendations from RECOMMENDATION_RULES│
│  + Food recommendations from FOOD_RECOMMENDATION_RULES│
│  + Fallback: reduce top harmful compound             │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 7: compute_recommendation_delta() ────────────┐
│  For each recommendation:                            │
│  • Deep-copy the request                             │
│  • Apply the hypothetical change                     │
│  • Re-run full pipeline                              │
│  • Compute delta in liver index (now + year 5)       │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 8: compute_multi_organ_data() ────────────────┐
│  Knowledge graph → per-organ scores:                 │
│  • Condition penalties per organ                     │
│  • Compound → gene → pathway → organ impacts        │
│  • Lifestyle modifiers (alcohol, stress, sleep)      │
│  • Lab adjustments (eGFR, LDL, HbA1c, hsCRP)       │
│  • Load → health index conversion (0-100)            │
│  • DDI detection via pairwise compound analysis      │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 9: compute_multi_organ_projection() ──────────┐
│  Multi-timeframe forecasting per organ:              │
│  • 6-month, 1-year, 2-year, 5-year horizons         │
│  • Baseline vs. optimized trajectories               │
│  • Confidence bands widening over time               │
│  • Guideline-grounded recommendations                │
│  • Organ-years-gained metric                         │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌─ Step 10: enrich_recommendations_with_gemini() ─────┐
│  Single Gemini 2.5 Flash API call:                   │
│  • Full patient context (CYP panel, labs, regimen)   │
│  • Batch personalise top 5 recommendations           │
│  • Mechanistically specific, CYP-grounded advice     │
│  • Falls back to static text if no API key           │
└──────────────────────────────────────────────────────┘
       │
       ▼
AnalysisResponse (JSON)
```

---

## API Endpoints

### Authentication (`/users`)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/users/register` | ❌ | Create account (email, full_name, password → bcrypt) |
| `POST` | `/users/login` | ❌ | Login → JWT token + user profile |
| `GET` | `/users/me` | ✅ | Current user profile + UserAttributes |
| `PATCH` | `/users/me` | ✅ | Update profile (full_name) |
| `POST` | `/users/change-password` | ✅ | Change password (requires current password) |

### Core Analysis (`/analysis`)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/analysis/run` | ✅ | **Main inference** — runs full multi-organ scoring pipeline |
| `POST` | `/analysis/extract-genetics` | ✅ | Gemini Vision — extract CYP phenotypes from uploaded PGx PDF |

### Export (`/export`)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `GET` | `/export/clinical-pdf` | ✅ | Download 9-page clinical PDF report |

### Lab Extraction (`/extraction`)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/extraction/parse-labs` | ✅ | Gemini Vision OCR — upload lab report image → structured values |

### Supporting Features

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `GET` | `/notifications` | ✅ | Get notification list |
| `PATCH` | `/notifications/{id}/read` | ✅ | Mark notification as read |
| `GET` | `/history` | ✅ | Trajectory history (past analyses) |
| `POST` | `/chat/message` | ✅ | Gemini conversational AI |
| `GET` | `/labs` | ✅ | Stored lab values |
| `GET` | `/wearables/sync` | ✅ | Trigger wearable data sync |
| `GET` | `/billing/status` | ✅ | Subscription status |
| `GET` | `/health` | ❌ | Health check |

---

## Data Models

### Request Models (`models/request.py`)

```python
AnalysisRequest
├── patient: Patient
│   ├── age: int (1-120)
│   ├── sex: "male" | "female" | "other"
│   ├── weight_kg: float
│   ├── height_cm: float?
│   └── ethnicity: str?
├── conditions: List[Condition]
│   ├── condition_id: str (e.g. "prediabetes", "nafld")
│   ├── severity: "mild" | "moderate" | "severe"
│   └── diagnosed: bool
├── genetics: ExtendedGenetics
│   ├── cyp2d6_metabolizer: Phenotype
│   ├── cyp2c19_metabolizer: Phenotype
│   ├── cyp3a4_metabolizer: Phenotype
│   ├── cyp2c9_metabolizer: Phenotype
│   ├── cyp1a2_metabolizer: Phenotype
│   ├── slco1b1_function: "normal" | "reduced" | "poor"
│   ├── mthfr_c677t: "normal" | "heterozygous" | "homozygous"
│   ├── diplotypes: Dict[str, str]  # e.g. {"CYP2D6": "*4/*4"}
│   └── source: "manual" | "23andme_upload" | "pgx_report"
├── lifestyle: LifestyleIntake (15 parameters)
├── regimen: List[RegimenItem]
│   ├── compound_id: str
│   ├── dose_mg: float
│   ├── frequency_per_day: float
│   ├── is_rx: bool
│   └── timing, prescribed_by, start_date, brand_name...
├── labs: Labs? (16 lab markers)
└── food: Food? (calories, processed %, fiber, diet type)
```

### Response Models (`models/response.py`)

```python
AnalysisResponse
├── risk_summary: RiskSummary
│   ├── risk_level: "green" | "amber" | "red"
│   ├── liver_index_now: float (0-100)
│   ├── projected_drop_percent: float
│   └── headline: str
├── trajectory: List[TrajectoryPoint] (6 points, year 0→5)
├── contributions: List[Contribution] (per-compound + lifestyle loads)
├── recommendations: List[Recommendation] (Gemini-enriched)
├── biological_age: float
├── polypharmacy_score: int
├── organ_scores: List[OrganScore] (liver, kidney, CVD, metabolic)
├── compound_gene_chains: List[CompoundGeneChain]
├── ddi_flags: List[DDIFlag]
├── active_pathways: List[str]
├── gnn_version: str
└── multi_organ_projection: MultiOrganProjection?
    ├── liver/kidney/cardiovascular/metabolic: OrganTrajectory
    ├── organ_years_gained: float?
    └── max_gain_organ: str?
```

---

## Database Schema

**SQLite** via **Prisma Python** (asyncio):

| Model | Fields | Purpose |
|-------|--------|---------|
| `User` | id, email (unique), full_name, hashed_password, onboarding_complete, is_pro, oura_token, created_at | User accounts |
| `UserAttributes` | id, user_id (unique FK), age, sex, weight_kg, height_cm, ethnicity, cyp2d6_metabolizer, cyp2c19_metabolizer | Demographics + PGx profile |
| `TrajectoryHistory` | id, user_id (FK), score, snapshot (JSON), created_at | Past analysis snapshots |

---

## GNN Model

The `EirionGNN` is a **Heterogeneous Graph Attention Network** (GATv2):

- **1.29M trainable parameters**
- **Knowledge graph:** 12,505 compounds × 23,658 genes × 2,848 pathways
- **Input:** SMILES string → 1024-bit Morgan fingerprint
- **Output:** 13 Tox21 bioassay toxicity probabilities
- **Test AUC:** 0.7628 macro-averaged (vs 0.7517 Random Forest)
- **Checkpoint:** `engine/weights/eirion_gnn_best.pt` (2.17 MB)

> 📖 Full GNN documentation: [`docs/GNN_README.md`](../docs/GNN_README.md)

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key |
| `DATABASE_URL` | ❌ | `file:./dev.db` | SQLite database path |
| `JWT_SECRET` | ❌ | `change_me_in_production` | JWT signing secret |
| `ALLOWED_ORIGINS` | ❌ | `http://localhost:5173` | Comma-separated CORS origins |

### Startup Behaviour

On startup (`lifespan`), the app:
1. Connects to the Prisma database
2. Eagerly loads the GNN model into memory (~250 MB)
3. Starts the APScheduler cron job for wearable sync (daily 08:00 UTC)

---

## Docker

```dockerfile
# Build
docker build -t eirion-backend .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e JWT_SECRET=your_secret \
  -v ./dev.db:/app/dev.db \
  eirion-backend
```

The Dockerfile uses:
- `python:3.11-slim` base
- **CPU-only PyTorch** (keeps image ~2 GB instead of ~6 GB for CUDA)
- Auto-runs `prisma db push` on container start

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=engine --cov-report=term-missing
```

The test suite (`test_engine.py`, 17K) covers:
- Compound load calculations with various CYP metabolizer statuses
- Lifestyle penalty computations
- Food/diet penalty scoring
- Liver index aggregation
- Risk band assignment
- Trajectory projection
- Recommendation generation and delta computation
- Multi-organ scoring pipeline

---

## Dependencies

<details>
<summary><b>Full dependency list (click to expand)</b></summary>

| Package | Version | Purpose |
|---------|---------|---------|
| **fastapi** | 0.135.2 | Web framework |
| **uvicorn** | 0.42.0 | ASGI server |
| **python-multipart** | 0.0.22 | File upload support |
| **python-dotenv** | 1.2.2 | Environment variable loading |
| **PyJWT** | 2.12.1 | JWT token handling |
| **bcrypt** | 5.0.0 | Password hashing |
| **prisma** | 0.15.0 | Database ORM (asyncio) |
| **pydantic** | 2.12.5 | Data validation (v2) |
| **google-genai** | 1.69.0 | Google Gemini AI SDK |
| **torch** | 2.11.0 | PyTorch (ML framework) |
| **torch-geometric** | 2.7.0 | PyTorch Geometric (GNN) |
| **scikit-learn** | 1.7.2 | ML utilities |
| **numpy** | 2.2.6 | Numerical computing |
| **scipy** | 1.15.3 | Scientific computing |
| **rdkit** | 2025.9.6 | Cheminformatics (SMILES, Morgan FP) |
| **reportlab** | 4.4.10 | PDF generation |
| **pillow** | 12.1.1 | Image processing (for PDFs) |
| **APScheduler** | 3.11.2 | Background job scheduling |
| **httpx** | 0.28.1 | Async HTTP client |
| **pandas** | 2.3.3 | Data manipulation |
| **joblib** | 1.5.3 | Serialization utilities |

</details>

---

<div align="center">

*Part of the [EIRION Precision Longevity Platform](../README.md)*

</div>
