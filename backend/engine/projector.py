"""
Multi-Timeframe Projection Engine (Phase 3)
===========================================
Generates month-resolution per-organ trajectories across 5 horizons:
  1yr · 2yr · 5yr · 10yr · lifetime

Decline model:
  score(t) = score₀ × exp(-λ × t)  — exponential decay with organ-specific λ
  λ = base_rate × condition_mult × lifestyle_mult × polypharmacy_mult

Optimized path: same λ but with a one-time score_boost at t=0 and reduced λ
from lifestyle improvements (sleep, sugar, stress).

Guidelines grounded in:
  AHA/ACC 2023 Cardiovascular Guidelines
  KDIGO 2022 CKD Guidelines
  EASL 2023 Liver Guidelines
  ADA 2024 Metabolic / Diabetes Guidelines
"""

import math
from typing import Dict, List, Optional, Tuple

from models.response import (
    MultiOrganProjection,
    OrganTrajectory,
    TimeframePoint,
)

# ────────────────────────────────────────────────────────────────────────────
# Organ-specific parameters
# ────────────────────────────────────────────────────────────────────────────

ORGAN_PARAMS = {
    "liver": {
        # Base annual decline λ per risk tier
        "lambda_green":  0.005,   # healthy: ~0.5%/yr
        "lambda_amber":  0.018,   # caution: ~1.8%/yr
        "lambda_red":    0.040,   # risk:    ~4%/yr
        # Lifestyle multipliers on λ
        "sleep_mult_per_h_below7": 0.008,
        "sugar_mult_per_50g":      0.010,
        "alcohol_mult_per_unit":   0.006,
        "smoking_boost":           0.015,
        # Polypharmacy: each high-risk compound adds to λ
        "polypharmacy_mult":       0.004,
        # Optimized: how much λ drops and score boosts
        "opt_lambda_reduction":    0.40,  # 40% lower decline rate
        "opt_score_boost":         5.0,   # +5 pts at t=0
        # Confidence band widens 0.15 pts per month
        "confidence_growth_rate":  0.15,
        # Guideline
        "guideline_rec": (
            "Maintain ALT < 40 U/L and GGT < 45 U/L. EASL 2023 recommends "
            "abstaining from alcohol entirely if liver index < 65, and beginning "
            "supervised NAFLD management if steatohepatitis markers persist."
        ),
        "guideline_source": "EASL Clinical Practice Guidelines 2023",
    },
    "kidney": {
        "lambda_green":  0.003,
        "lambda_amber":  0.012,
        "lambda_red":    0.030,
        "sleep_mult_per_h_below7": 0.004,
        "sugar_mult_per_50g":      0.006,
        "alcohol_mult_per_unit":   0.002,
        "smoking_boost":           0.010,
        "polypharmacy_mult":       0.003,
        "opt_lambda_reduction":    0.35,
        "opt_score_boost":         4.0,
        "confidence_growth_rate":  0.10,
        "guideline_rec": (
            "Target eGFR decline < 2 mL/min/1.73m²/yr. KDIGO 2022 recommends "
            "ACE inhibitor or ARB therapy if urinary ACR > 30 mg/g, and protein "
            "restriction to 0.8 g/kg/day in CKD Stage 3+."
        ),
        "guideline_source": "KDIGO CKD Guidelines 2022",
    },
    "cardiovascular": {
        "lambda_green":  0.004,
        "lambda_amber":  0.016,
        "lambda_red":    0.035,
        "sleep_mult_per_h_below7": 0.005,
        "sugar_mult_per_50g":      0.008,
        "alcohol_mult_per_unit":   0.004,
        "smoking_boost":           0.025,
        "polypharmacy_mult":       0.002,
        "opt_lambda_reduction":    0.45,
        "opt_score_boost":         6.0,
        "confidence_growth_rate":  0.12,
        "guideline_rec": (
            "Target LDL-C < 100 mg/dL (< 70 mg/dL if 10-yr ASCVD risk ≥ 10%). "
            "AHA/ACC 2023: high-intensity statin for primary prevention if LDL > 190 "
            "or age 40-75 with diabetes. hsCRP > 2 mg/L indicates residual inflammatory risk."
        ),
        "guideline_source": "AHA/ACC Cardiovascular Guidelines 2023",
    },
    "metabolic": {
        "lambda_green":  0.006,
        "lambda_amber":  0.020,
        "lambda_red":    0.042,
        "sleep_mult_per_h_below7": 0.010,
        "sugar_mult_per_50g":      0.014,
        "alcohol_mult_per_unit":   0.003,
        "smoking_boost":           0.008,
        "polypharmacy_mult":       0.003,
        "opt_lambda_reduction":    0.50,
        "opt_score_boost":         7.0,
        "confidence_growth_rate":  0.18,
        "guideline_rec": (
            "Target HbA1c < 5.7% (prediabetes reversal goal). ADA 2024 recommends "
            "structured lifestyle intervention achieving ≥ 7% body weight loss, "
            "150 min/week moderate exercise, and < 25g added sugar/day to delay T2DM onset."
        ),
        "guideline_source": "ADA Standards of Care in Diabetes 2024",
    },
}

# Timeframe definitions: (label, total_months, point_step_months)
TIMEFRAME_DEFS: List[Tuple[str, int, int]] = [
    ("1yr",      12,  1),
    ("2yr",      24,  2),
    ("5yr",      60,  6),
    ("10yr",    120, 12),
    ("lifetime", 480, 24),  # ~40 years
]


def _risk_level(score: float) -> str:
    if score >= 75: return "green"
    if score >= 55: return "amber"
    return "red"


def _organ_lambda(organ: str, score: float, request) -> float:
    """Compute the monthly decay constant λ for an organ given current load."""
    p = ORGAN_PARAMS[organ]
    risk = _risk_level(score)

    # Base annual λ
    base_λ = {
        "green": p["lambda_green"],
        "amber": p["lambda_amber"],
        "red":   p["lambda_red"],
    }[risk]

    ls = request.lifestyle
    # Lifestyle modifiers (additive on λ)
    sleep_deficit = max(0.0, 7.0 - ls.sleep_hours_avg)
    sugar_50g = max(0.0, (ls.sugar_g_per_day - 50) / 50)
    base_λ += p["sleep_mult_per_h_below7"] * sleep_deficit
    base_λ += p["sugar_mult_per_50g"] * sugar_50g
    base_λ += p["alcohol_mult_per_unit"] * max(0.0, ls.alcohol_drinks_per_week - 2)
    if ls.smoking_status == "current":
        base_λ += p["smoking_boost"]

    # Polypharmacy load
    n_rx = sum(1 for item in request.regimen if getattr(item, "is_rx", False))
    base_λ += p["polypharmacy_mult"] * n_rx

    # Convert annual → monthly
    return base_λ / 12.0


def _project_series(
    score0: float,
    lam: float,
    opt_lam: float,
    opt_boost: float,
    total_months: int,
    step: int,
    confidence_rate: float,
) -> List[TimeframePoint]:
    """
    Generate a list of TimeframePoints for a given organ trajectory.
    Uses exponential decay: score(t) = score₀ × exp(-λ × t)
    Optimized path: score(t) = (score₀ + boost) × exp(-λ_opt × t)
    Confidence band: ±(confidence_rate × sqrt(t))
    """
    points = []
    months = list(range(0, total_months + 1, step))
    if months[-1] != total_months:
        months.append(total_months)

    for m in months:
        # Exponential decay — clamp to [10, 98]
        raw = score0 * math.exp(-lam * m)
        score = max(10.0, min(98.0, round(raw, 1)))

        opt_raw = (score0 + opt_boost) * math.exp(-opt_lam * m)
        opt_score = max(10.0, min(98.0, round(opt_raw, 1)))

        # Confidence band ±σ growing with sqrt(t)
        band = round(confidence_rate * math.sqrt(max(m, 1)), 1)

        # Human label
        if m < 12:
            label = f"{m}m" if m > 0 else "Now"
        elif m % 12 == 0:
            yrs = m // 12
            label = f"{yrs}yr" if yrs <= 10 else f"{yrs}yrs"
        else:
            label = f"{m}m"

        points.append(TimeframePoint(
            month=m,
            label=label,
            score=score,
            optimized_score=opt_score,
            confidence_band=band,
        ))

    return points


def build_organ_trajectory(
    organ: str,
    current_score: float,
    request,
) -> OrganTrajectory:
    """Build full multi-timeframe trajectory for one organ."""
    p = ORGAN_PARAMS[organ]
    risk = _risk_level(current_score)

    lam = _organ_lambda(organ, current_score, request)
    opt_lam = lam * (1.0 - p["opt_lambda_reduction"])
    opt_boost = p["opt_score_boost"]
    conf_rate = p["confidence_growth_rate"]

    # Optimized score at t=0 (immediate lifestyle adoption)
    optimized_now = min(98.0, current_score + opt_boost)

    timeframes: Dict = {}
    scores_at: Dict = {}
    optimized_at: Dict = {}
    improvement_at: Dict = {}

    for label, total_months, step in TIMEFRAME_DEFS:
        series = _project_series(
            score0=current_score,
            lam=lam,
            opt_lam=opt_lam,
            opt_boost=opt_boost,
            total_months=total_months,
            step=step,
            confidence_rate=conf_rate,
        )
        timeframes[label] = series

        last = series[-1]
        scores_at[label]      = last.score
        optimized_at[label]   = last.optimized_score
        improvement_at[label] = round(last.optimized_score - last.score, 1)

    return OrganTrajectory(
        organ=organ,
        current_score=round(current_score, 1),
        optimized_now=round(optimized_now, 1),
        risk_level=risk,
        timeframes=timeframes,
        scores_at=scores_at,
        optimized_at=optimized_at,
        improvement_at=improvement_at,
        guideline_rec=p["guideline_rec"],
        guideline_source=p["guideline_source"],
    )


def compute_multi_organ_projection(
    organ_scores: list,
    request,
) -> MultiOrganProjection:
    """
    Entry point: given already-computed OrganScore list, build full
    multi-timeframe projections for all 4 organs.
    """
    score_map: Dict[str, float] = {organ_s.organ: organ_s.score for organ_s in organ_scores}

    trajectories = {}
    for organ in ("liver", "kidney", "cardiovascular", "metabolic"):
        score = score_map.get(organ, 70.0)
        trajectories[organ] = build_organ_trajectory(organ, score, request)

    # Cross-organ summary — organ-years gained at 10yr horizon
    organ_years = sum(
        trajectories[o].improvement_at.get("10yr", 0.0) / 100.0 * 10
        for o in trajectories
    )

    max_gain_organ = max(
        trajectories.keys(),
        key=lambda o: trajectories[o].improvement_at.get("10yr", 0.0)
    )
    max_gain_pct = trajectories[max_gain_organ].improvement_at.get("10yr", 0.0)

    return MultiOrganProjection(
        liver=trajectories["liver"],
        kidney=trajectories["kidney"],
        cardiovascular=trajectories["cardiovascular"],
        metabolic=trajectories["metabolic"],
        organ_years_gained=round(organ_years, 1),
        max_gain_organ=max_gain_organ,
        max_gain_pct=round(max_gain_pct, 1),
    )
