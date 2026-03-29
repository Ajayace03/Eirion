"""
Temporal Fusion Transformer (TFT) — Organ Function Forecasting
---------------------------------------------------------------
Replaces the exponential decay model in projector.py with a proper
sequence model that ingests quarterly lab + lifestyle observations.

Architecture (Lim et al. 2021, NeurIPS):
    - Variable Selection Networks (VSN) for static + dynamic inputs
    - Gated Residual Networks (GRN)
    - Multi-head temporal self-attention
    - Quantile regression: P10 (pessimistic) / P50 (median) / P90 (optimistic)

This module exposes two interfaces:
    1. TFTOrganForecaster — the full PyTorch model (GPU/CPU)
    2. forecast_organs()  — high-level function pluggable into projector.py

Usage:
    from engine.planned.tft_forecasting import TFTOrganForecaster, load_tft, forecast_organs
    model = load_tft("weights/tft_organs.pt")
    projections = forecast_organs(model, request, current_organ_scores)
    # → dict mapping organ → {"p10": [...], "p50": [...], "p90": [...]}
"""

import logging
import math
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Dependency guard ──────────────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _TORCH = True
except ImportError:
    _TORCH = False
    logger.warning("[TFT] PyTorch not available — TFT forecaster disabled.")

# ── Dimensions ────────────────────────────────────────────────────────────────
ORGANS = ["liver", "kidney", "cardiovascular", "metabolic"]
HORIZONS_MONTHS = [12, 24, 60, 120]   # 1yr, 2yr, 5yr, 10yr
QUANTILES = [0.1, 0.5, 0.9]           # P10, P50, P90
N_ORGANS = len(ORGANS)

# Feature dims
STATIC_DIM  = 12   # age, sex, BMI, n_conditions, 8 genetic flags
DYNAMIC_DIM = 16   # quarterly labs + lifestyle snapshot
HIDDEN_DIM  = 64
N_HEADS     = 4
DROPOUT     = 0.1
N_ENCODER   = 4    # lookback quarters
N_DECODER   = 4    # max forecast quarters (10 yr / 4 per yr)


if _TORCH:

    # ── Helper building blocks ────────────────────────────────────────────────

    class GRN(nn.Module):
        """Gated Residual Network as used in TFT."""

        def __init__(self, input_dim: int, hidden_dim: int, output_dim: int,
                     dropout: float = DROPOUT):
            super().__init__()
            self.fc1  = nn.Linear(input_dim, hidden_dim)
            self.fc2  = nn.Linear(hidden_dim, output_dim)
            self.gate = nn.Sequential(nn.Linear(input_dim, output_dim), nn.Sigmoid())
            self.norm = nn.LayerNorm(output_dim)
            self.skip = nn.Linear(input_dim, output_dim) if input_dim != output_dim else nn.Identity()
            self.drop = nn.Dropout(dropout)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            h  = F.elu(self.fc1(x))
            h  = self.drop(self.fc2(h))
            gate = self.gate(x)
            return self.norm(gate * h + (1 - gate) * self.skip(x))


    class VariableSelectionNetwork(nn.Module):
        """VSN: learns soft variable selection weights per time step."""

        def __init__(self, n_vars: int, var_dim: int, hidden: int,
                     dropout: float = DROPOUT):
            super().__init__()
            self.var_grns  = nn.ModuleList([GRN(var_dim, hidden, hidden, dropout)
                                            for _ in range(n_vars)])
            self.select_grn = GRN(n_vars * var_dim, hidden, n_vars, dropout)
            self.softmax    = nn.Softmax(dim=-1)

        def forward(self, x_list: List["torch.Tensor"]) -> "torch.Tensor":
            processed = torch.stack([grn(xi) for grn, xi in zip(self.var_grns, x_list)], dim=-2)
            flat = torch.cat(x_list, dim=-1)
            weights = self.softmax(self.select_grn(flat))   # (..., n_vars)
            return (weights.unsqueeze(-1) * processed).sum(dim=-2)


    class TFTOrganForecaster(nn.Module):
        """
        Temporal Fusion Transformer for 4-organ index forecasting.

        Input:
            static_feats  : (B, STATIC_DIM)  — patient demographics + genetics
            dynamic_feats : (B, T, DYNAMIC_DIM) — quarterly lab/lifestyle snapshots
            organ_scores  : (B, N_ORGANS)    — current organ indices

        Output:
            (B, N_ORGANS, len(QUANTILES), max_horizon_steps)
        """

        def __init__(
            self,
            static_dim:  int = STATIC_DIM,
            dynamic_dim: int = DYNAMIC_DIM,
            n_organs:    int = N_ORGANS,
            hidden:      int = HIDDEN_DIM,
            n_heads:     int = N_HEADS,
            dropout:     float = DROPOUT,
        ):
            super().__init__()
            self.n_organs  = n_organs
            self.hidden    = hidden

            # Static covariate encoder
            self.static_encoder = GRN(static_dim, hidden, hidden, dropout)

            # Variable selection for dynamic inputs
            # Each dynamic variable gets its own embedding
            self.dynamic_vsn = VariableSelectionNetwork(
                n_vars=dynamic_dim, var_dim=1, hidden=hidden, dropout=dropout
            )

            # Positional encoding (learnable)
            self.pos_embed = nn.Embedding(32, hidden)

            # LSTM encoder (past observations)
            self.encoder_lstm = nn.LSTM(hidden, hidden, batch_first=True, dropout=dropout)

            # LSTM decoder (future horizon)
            self.decoder_lstm = nn.LSTM(hidden, hidden, batch_first=True, dropout=dropout)

            # Temporal self-attention
            self.temporal_attn = nn.MultiheadAttention(hidden, n_heads, dropout=dropout, batch_first=True)
            self.attn_gate = GRN(hidden, hidden, hidden, dropout)

            # Static enrichment
            self.static_enrich = GRN(hidden * 2, hidden, hidden, dropout)

            # Per-organ, per-quantile output heads
            self.output_heads = nn.ModuleDict({
                f"{organ}_q{int(q*100)}": nn.Sequential(
                    GRN(hidden, hidden, hidden // 2, dropout),
                    nn.Linear(hidden // 2, 1),
                )
                for organ in ORGANS
                for q in QUANTILES
            })

        def forward(
            self,
            static_feats:  "torch.Tensor",
            dynamic_feats: "torch.Tensor",
            n_future_steps: int = 4,
        ) -> Dict[str, "torch.Tensor"]:
            B, T, D = dynamic_feats.shape

            # Static context
            static_ctx = self.static_encoder(static_feats)   # (B, H)

            # Dynamic: VSN expects list of single features
            dyn_list = [dynamic_feats[:, :, i:i+1].squeeze(-1) for i in range(D)]
            # Apply VSN per time step
            dyn_encoded = self.dynamic_vsn(
                [d.reshape(B * T, 1) for d in dyn_list]
            ).reshape(B, T, self.hidden)

            # Positional encoding
            pos = self.pos_embed(torch.arange(T, device=dynamic_feats.device))
            dyn_encoded = dyn_encoded + pos.unsqueeze(0)

            # LSTM encoder over past T steps
            enc_out, (h_n, c_n) = self.encoder_lstm(dyn_encoded)   # (B, T, H)

            # LSTM decoder for future steps
            dec_inp = enc_out[:, -1:, :].expand(B, n_future_steps, self.hidden)
            dec_out, _ = self.decoder_lstm(dec_inp, (h_n, c_n))    # (B, F, H)

            # Temporal attention over encoder output
            full_seq  = torch.cat([enc_out, dec_out], dim=1)        # (B, T+F, H)
            attn_out, _ = self.temporal_attn(full_seq, full_seq, full_seq)
            attn_out  = self.attn_gate(attn_out)
            future_h  = attn_out[:, T:, :]                          # (B, F, H)

            # Static enrichment
            sc_exp = static_ctx.unsqueeze(1).expand(B, n_future_steps, self.hidden)
            enriched = self.static_enrich(torch.cat([future_h, sc_exp], dim=-1))  # (B, F, H)

            # Output: per organ per quantile
            results = {}
            for organ in ORGANS:
                for q in QUANTILES:
                    key = f"{organ}_q{int(q*100)}"
                    pred = self.output_heads[key](enriched).squeeze(-1)  # (B, F)
                    results[f"{organ}_q{int(q*100)}"] = pred

            return results

        def predict(
            self,
            static_feats: "torch.Tensor",
            dynamic_feats: "torch.Tensor",
            n_future_steps: int = 4,
        ) -> Dict[str, List[float]]:
            """Eval mode prediction → plain Python dicts of floats."""
            self.eval()
            with torch.no_grad():
                raw = self.forward(static_feats, dynamic_feats, n_future_steps)
                return {k: v[0].tolist() for k, v in raw.items()}


    def load_tft(weights_path: str = "") -> "TFTOrganForecaster":
        """Load TFT model; random init if weights absent."""
        model = TFTOrganForecaster()
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location="cpu", weights_only=True)
                if "state_dict" in state:
                    state = state["state_dict"]
                model.load_state_dict(state, strict=False)
                logger.info("[TFT] Loaded weights: %s", weights_path)
            except Exception as e:
                logger.warning("[TFT] Could not load weights: %s", e)
        else:
            logger.info("[TFT] No weights at '%s' — using random init. "
                        "Train on UK Biobank/NHANES for calibrated forecasts.", weights_path)
        model.eval()
        return model


    def _build_static_features(request) -> "torch.Tensor":
        """Build (1, STATIC_DIM) static feature tensor from an AnalysisRequest."""
        p  = request.patient
        ls = request.lifestyle
        gen = request.genetics
        age_n = (getattr(p, "age", 35) - 18) / 82
        bmi   = getattr(p, "weight_kg", 70) / ((max(getattr(p, "height_cm", 170), 1) / 100) ** 2)
        sex_n = 1.0 if getattr(p, "sex", "male") == "male" else 0.0
        n_cond = min(len(getattr(request, "conditions", []) or []) / 5, 1.0)
        n_drugs = min(len(request.regimen) / 10, 1.0)
        stress_n = getattr(ls, "stress_level", 5) / 10
        sleep_n  = getattr(ls, "sleep_hours_avg", 7) / 12
        smk = 1.0 if getattr(ls, "smoking_status", "never") == "current" else 0.0
        cyp2d6_n = {"poor": 0.0, "intermediate": 0.33, "normal": 0.67, "ultra_rapid": 1.0,
                    "unknown": 0.5}.get(getattr(gen, "cyp2d6_metabolizer", "unknown"), 0.5)
        cyp2c19_n = {"poor": 0.0, "intermediate": 0.33, "normal": 0.67, "ultra_rapid": 1.0,
                     "unknown": 0.5}.get(getattr(gen, "cyp2c19_metabolizer", "unknown"), 0.5)
        mthfr_n = {"normal": 0.0, "heterozygous": 0.5, "homozygous": 1.0,
                   "unknown": 0.25}.get(getattr(gen, "mthfr_c677t", "unknown"), 0.25)
        feats = [age_n, sex_n, min(bmi/40, 1.0), n_cond, n_drugs,
                 stress_n, sleep_n, smk, cyp2d6_n, cyp2c19_n, mthfr_n, 0.0]
        feats = feats[:STATIC_DIM]
        return torch.tensor([feats], dtype=torch.float)


    def _build_dynamic_features(request, organ_scores: Dict[str, float]) -> "torch.Tensor":
        """Build (1, 4, DYNAMIC_DIM) dynamic tensor — simulates 4 past quarters."""
        labs = request.labs
        feats_now = [
            organ_scores.get("liver", 70) / 100,
            organ_scores.get("kidney", 75) / 100,
            organ_scores.get("cardiovascular", 72) / 100,
            organ_scores.get("metabolic", 70) / 100,
            min((getattr(labs, "alt_u_per_l", None) or 25) / 80, 1.0) if labs else 0.3,
            min((getattr(labs, "egfr_ml_per_min", None) or 90) / 120, 1.0) if labs else 0.75,
            min((getattr(labs, "ldl_mg_per_dl", None) or 100) / 200, 1.0) if labs else 0.5,
            min((getattr(labs, "hba1c_pct", None) or 5.0) / 9, 1.0) if labs else 0.55,
            min((getattr(labs, "hscrp_mg_per_l", None) or 0.5) / 5, 1.0) if labs else 0.1,
            getattr(request.lifestyle, "stress_level", 5) / 10,
            getattr(request.lifestyle, "sleep_hours_avg", 7) / 12,
            min(getattr(request.lifestyle, "exercise_mins_per_week", 150) / 300, 1.0),
            getattr(request.lifestyle, "alcohol_drinks_per_week", 0) / 20,
            min(getattr(request.lifestyle, "sugar_g_per_day", 50) / 200, 1.0),
            len(request.regimen) / 10,
            0.0,  # padding
        ]
        feats_now = feats_now[:DYNAMIC_DIM]
        # Simulate 4 quarters of past data (add small noise for realism)
        rng = np.random.default_rng(42)
        quarters = []
        for q in range(N_ENCODER):
            noise = rng.normal(0, 0.02, len(feats_now))
            quarters.append([max(0, min(1, f + n)) for f, n in zip(feats_now, noise)])
        return torch.tensor([quarters], dtype=torch.float)   # (1, T, D)


    def forecast_organs(
        model: "TFTOrganForecaster",
        request,
        organ_scores: Dict[str, float],
        horizons: List[int] = HORIZONS_MONTHS,
    ) -> Dict[str, Dict[str, List[float]]]:
        """
        High-level entry — builds features, runs TFT, returns per-organ P10/P50/P90
        at each requested horizon in months.

        Returns:
            {
              "liver": {"p10": [s1, s2, ...], "p50": [...], "p90": [...]},
              ...
            }
        """
        try:
            static  = _build_static_features(request)
            dynamic = _build_dynamic_features(request, organ_scores)
            n_steps = max(horizons) // 12   # coarse: one step per year
            preds   = model.predict(static, dynamic, n_future_steps=max(1, n_steps))

            out = {}
            for organ in ORGANS:
                p10 = preds.get(f"{organ}_q10", [organ_scores.get(organ, 70.0)] * n_steps)
                p50 = preds.get(f"{organ}_q50", [organ_scores.get(organ, 70.0)] * n_steps)
                p90 = preds.get(f"{organ}_q90", [organ_scores.get(organ, 70.0)] * n_steps)
                # Clamp to valid range
                out[organ] = {
                    "p10": [max(10.0, min(98.0, round(v * 100, 1))) for v in p10],
                    "p50": [max(10.0, min(98.0, round(v * 100, 1))) for v in p50],
                    "p90": [max(10.0, min(98.0, round(v * 100, 1))) for v in p90],
                }
            return out
        except Exception as e:
            logger.error("[TFT] forecast_organs failed: %s", e)
            return {o: {"p10": [], "p50": [], "p90": []} for o in ORGANS}

else:
    # Stub when PyTorch unavailable
    class TFTOrganForecaster:  # type: ignore[no-redef]
        def predict(self, *a, **kw): return {}

    def load_tft(weights_path: str = "") -> TFTOrganForecaster:
        return TFTOrganForecaster()

    def forecast_organs(model, request, organ_scores, horizons=HORIZONS_MONTHS):
        return {o: {"p10": [], "p50": [], "p90": []} for o in ORGANS}
