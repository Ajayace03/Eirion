"""
Eirion Engine — Planned Models (NOW IMPLEMENTED)
=================================================
All modules in this package contain real, runnable implementations.
Optional heavy dependencies (torch_geometric, gymnasium, stable-baselines3)
degrade gracefully — each module falls back to a stub when unavailable.

Modules:
    gatv2_drug_gene_organ.py       — GATv2 heterogeneous polypharmacy GNN
                                     Requires: torch-geometric
    dmpnn_toxicity.py              — DMPNN on ToxCast/Tox21/FAERS endpoints
                                     Requires: torch + rdkit
    multi_organ_expansion.py       — Brain + Heart organ stubs (architecture docs)
    tft_forecasting.py             — Temporal Fusion Transformer (5-10yr forecasts)
                                     Requires: torch
    rl_regimen_optimizer.py        — SAC/PPO supplement regimen RL agent
                                     Requires: gymnasium + stable-baselines3
                                     Fallback: deterministic greedy optimizer (always available)
    bio_age_tracker.py             — Multi-clock biological age (PhenoAge/OrganAge)
                                     No external deps — runs with labs only
    wearable_fhir_integration.py   — FHIR R4 + Oura/Garmin/Apple HealthKit bridge
                                     Requires: httpx

Quick import:
    from engine.planned.bio_age_tracker import BioAgeTracker
    from engine.planned.rl_regimen_optimizer import load_rl_optimizer, greedy_optimize
    from engine.planned.dmpnn_toxicity import load_dmpnn
    from engine.planned.gatv2_drug_gene_organ import load_gatv2
    from engine.planned.tft_forecasting import load_tft, forecast_organs
    from engine.planned.wearable_fhir_integration import FHIRClient, OuraClient
"""
