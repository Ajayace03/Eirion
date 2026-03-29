"""
EIRION Scoring Engine — Phase 0
Deterministic rules-based liver toxicity analysis pipeline.

Flow:
  validate_and_normalize → compute_compound_load (per item)
  → aggregate_liver_index → assign_risk_band
  → compute_trajectory → generate_recommendations
  → compute_recommendation_delta → assemble AnalysisResponse
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

from ..models.request import AnalysisRequest, Genetics, Lifestyle  # type: ignore
from ..models.response import (  # type: ignore
    AnalysisResponse,
    Contribution,
    ExpectedImprovement,
    Recommendation,
    RiskSummary,
    TrajectoryPoint,
)
from .knowledge import (  # type: ignore
    ALT_THRESHOLD,
    AST_THRESHOLD,
    ACTIVITY_PENALTIES,
    ALCOHOL_PENALTIES,
    DEFAULT_LOAD,
    GENE_DRUG_RULES,
    HIGH_RISK_TAGS,
    LAB_ELEVATION_BUMP,
    LAB_ELEVATION_MAX,
    LIVER_LOAD_TABLE,
    POLYPHARMACY_BASE_PER_COMPOUND,
    POLYPHARMACY_HIGH_TAG_BONUS,
    RECOMMENDATION_RULES,
    RISK_THRESHOLDS,
    SLEEP_PENALTIES,
    STRESS_PENALTY,
    STRESS_THRESHOLD,
    SUGAR_PENALTIES,
    TRAJECTORY_PARAMS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _apply_threshold_penalties(value: float, thresholds: list) -> int:
    """Walk ascending threshold list and return penalty for the bracket value falls in."""
    for threshold, penalty in thresholds:
        if value <= threshold:
            return penalty
    return thresholds[-1][1]


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Validate & Normalize
# ─────────────────────────────────────────────────────────────────────────────

def validate_and_normalize(request: AnalysisRequest) -> AnalysisRequest:
    """
    Ensures all regimen items have a valid compound entry and doses are clamped.
    Unknown genetics fields default to 'unknown' via Pydantic defaults.
    """
    # Pydantic already validates types; this step does domain-level normalization.
    # We don't mutate — just return as-is (future: normalize dose units, etc.)
    return request


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Per-Compound Load
# ─────────────────────────────────────────────────────────────────────────────

def compute_compound_load(
    compound_id: str, dose_mg: float, genetics: Genetics
) -> Tuple[float, str, bool]:
    """
    Returns (load_score, explanation_reason, is_protective).
    load_score may be negative for protective compounds.
    """
    compound = LIVER_LOAD_TABLE.get(compound_id)

    if compound is None:
        # Unknown compound: conservative default
        return (
            DEFAULT_LOAD * 1.0,
            f"{compound_id} (unknown compound — conservative estimate applied)",
            False,
        )

    dose_factor = _clamp(dose_mg / compound["dose_normal"], 0.5, 2.0)
    genetic_multiplier = 1.0
    genetic_note = ""

    # Apply gene-drug rules
    cyp_status = {
        "cyp2d6": genetics.cyp2d6_metabolizer,
        "cyp2c19": genetics.cyp2c19_metabolizer,
    }

    for gene, status, tag, multiplier in GENE_DRUG_RULES:
        if cyp_status.get(gene) == status and tag in compound["tags"]:
            genetic_multiplier = multiplier
            direction = "slower" if multiplier > 1 else "faster"
            pct = abs(int((multiplier - 1) * 100))
            genetic_note = (
                f" Your {gene.upper()} {status} metabolizer status causes "
                f"~{pct}% {direction} clearance."
            )
            break  # Apply first matching rule only

    # [ML GNN INJECTION]
    from .inference import predictor  # type: ignore
    
    if "smiles" in compound:
        prob = predictor.predict_toxicity(compound["smiles"])
        ml_base = float(f"{prob * 10:.2f}")
    else:
        prob = 0.0
        ml_base = float(compound["base"])

    if compound["protective"]:
        base_score = float(compound["base"]) # Negative domain
        ml_note = ""
    else:
        base_score = ml_base
        ml_note = f"[ML Tox {prob*100:.0f}%] Base {base_score:.1f}. " if "smiles" in compound else ""

    raw_load = base_score * dose_factor * genetic_multiplier

    # Build explanation
    display_name = compound["display_name"]
    if compound["protective"]:
        reason = f"{display_name}: hepatoprotective agent — offsets {abs(raw_load):.1f} load points.{genetic_note}"
    else:
        reason = (
            f"{display_name}: {ml_note}"
            f"dose {dose_factor:.1f}×, "
            f"genes {genetic_multiplier:.1f}× → {raw_load:.1f} load pts.{genetic_note}"
        )

    return raw_load, reason, compound["protective"]


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Lifestyle Penalties
# ─────────────────────────────────────────────────────────────────────────────

def compute_lifestyle_penalties(lifestyle: Lifestyle) -> Tuple[float, Dict[str, float]]:
    """Returns (total_penalty, breakdown_dict). All penalties are negative numbers."""
    breakdown: Dict[str, float] = {}

    sugar_pen = _apply_threshold_penalties(lifestyle.sugar_g_per_day, SUGAR_PENALTIES)
    breakdown["High Sugar Diet"] = float(sugar_pen)

    alcohol_pen = _apply_threshold_penalties(lifestyle.alcohol_units_per_week, ALCOHOL_PENALTIES)
    breakdown["Alcohol Intake"] = alcohol_pen

    sleep_pen = _apply_threshold_penalties(lifestyle.sleep_hours_per_night, SLEEP_PENALTIES)
    breakdown["Poor Sleep"] = sleep_pen

    activity_pen = ACTIVITY_PENALTIES.get(lifestyle.activity_level, 0)
    breakdown["Sedentary Activity"] = activity_pen

    stress_pen = STRESS_PENALTY if lifestyle.stress_level >= STRESS_THRESHOLD else 0
    breakdown["High Stress"] = stress_pen

    total = sum(breakdown.values())
    # Remove zero-penalty entries for cleanliness
    breakdown = {k: v for k, v in breakdown.items() if v != 0}

    return total, breakdown


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Aggregate Liver Index
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_liver_index(
    contributions: List[Contribution], lifestyle_penalty: float
) -> float:
    """
    liver_index = clamp(100 − sum_of_loads, 40, 100)
    """
    compound_load_sum = sum(c.load for c in contributions)
    liver_index = _clamp(100 - compound_load_sum, 40, 100)
    return float(f"{liver_index:.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Risk Band & Trajectory
# ─────────────────────────────────────────────────────────────────────────────

def assign_risk_band(liver_index: float) -> Tuple[str, float]:
    """Returns (risk_level, decline_fraction)."""
    if liver_index >= RISK_THRESHOLDS["green"]:
        risk = "green"
    elif liver_index >= RISK_THRESHOLDS["amber"]:
        risk = "amber"
    else:
        risk = "red"
    return risk, TRAJECTORY_PARAMS[risk]


def compute_trajectory(
    liver_index_now: float,
    decline_fraction: float,
    labs: Optional[Any],
) -> List[TrajectoryPoint]:
    """
    Produces a 6-point yearly trajectory [year 0 → year 5].
    Bumps decline if labs already show elevated markers.
    """
    df = decline_fraction

    if labs is not None:
        if (labs.ast_u_per_l and labs.ast_u_per_l > AST_THRESHOLD) or \
           (labs.alt_u_per_l and labs.alt_u_per_l > ALT_THRESHOLD):
            df = min(df + LAB_ELEVATION_BUMP, LAB_ELEVATION_MAX)

    index_year5 = liver_index_now - (100 * df)

    points = []
    for y in range(6):
        fraction = y / 5
        val = float(liver_index_now + (index_year5 - liver_index_now) * fraction)
        points.append(TrajectoryPoint(year=y, liver_index=float(f"{val:.2f}")))

    return points


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — Recommendations
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendations(
    request: AnalysisRequest,
    contributions: List[Contribution],
) -> List[Recommendation]:
    """
    Applies the ordered recommendation rule set and returns matching recs.
    """
    regimen_ids = {item.compound_id for item in request.regimen}
    recs: List[Recommendation] = []

    for rule in RECOMMENDATION_RULES:
        try:
            triggered = rule["trigger"](regimen_ids, request.genetics, request.lifestyle)
        except Exception:
            triggered = False

        if triggered:
            details = rule["details"]
            # Interpolate sugar value if present
            if "{sugar_g}" in details:
                details = details.format(sugar_g=int(request.lifestyle.sugar_g_per_day))

            recs.append(
                Recommendation(
                    id=rule["id"],
                    action_type=rule["action_type"],
                    title=rule["title"],
                    details=details,
                    expected_improvement=ExpectedImprovement(
                        delta_index_now=0.0,  # Computed in next step
                        delta_index_year5=0.0,
                    ),
                    confidence=rule["confidence"],
                    evidence_refs=rule["evidence_refs"],
                )
            )

    # Fallback: if no recs and there are high-load compounds, suggest reducing the top one
    if not recs and contributions:
        harmful = sorted(
            [c for c in contributions if not c.is_protective and c.load > 0],
            key=lambda c: c.load,
            reverse=True,
        )
        if harmful:
            top = harmful[0]
            recs.append(
                Recommendation(
                    id=f"reduce_{top.compound_id}",
                    action_type="reduce",
                    title=f"Consider Reducing {top.name} Dose",
                    details=(
                        f"{top.name} is your highest hepatic load contributor at "
                        f"{top.load:.1f} load points. Halving the dose could recover "
                        f"~{top.load * 0.3:.1f} index points."
                    ),
                    expected_improvement=ExpectedImprovement(
                        delta_index_now=0.0,
                        delta_index_year5=0.0,
                    ),
                    confidence=0.72,
                    evidence_refs=[],
                )
            )

    return recs


# ─────────────────────────────────────────────────────────────────────────────
# Step 7 — Recommendation Deltas
# ─────────────────────────────────────────────────────────────────────────────

def compute_recommendation_delta(
    request: AnalysisRequest,
    rec: Recommendation,
    original_index: float,
    original_trajectory: List[TrajectoryPoint],
) -> ExpectedImprovement:
    """
    Hypothetically applies the recommendation, re-runs the pipeline,
    and computes the delta in liver index (now and at year 5).
    """
    modified = copy.deepcopy(request)

    if rec.id == "swap_ashwagandha_rhodiola":
        modified.regimen = [r for r in modified.regimen if r.compound_id != "ashwagandha"]

    elif rec.id == "reduce_sugar":
        modified.lifestyle.sugar_g_per_day = 90.0

    elif rec.id == "add_nac":
        from ..models.request import RegimenItem  # type: ignore
        modified.regimen.append(RegimenItem(compound_id="nac", dose_mg=600))

    elif rec.id.startswith("reduce_"):
        cid = rec.id.replace("reduce_", "")
        for item in modified.regimen:
            if item.compound_id == cid:
                item.dose_mg = item.dose_mg * 0.5
                break

    # Re-run analysis on the modified request
    mod_contributions, mod_penalty, _ = _build_contributions(modified)
    mod_index = aggregate_liver_index(mod_contributions, mod_penalty)
    mod_risk, mod_decline = assign_risk_band(mod_index)
    mod_trajectory = compute_trajectory(mod_index, mod_decline, modified.labs)

    delta_now = float(f"{(mod_index - original_index):.2f}")
    delta_y5 = float(f"{(mod_trajectory[5].liver_index - original_trajectory[5].liver_index):.2f}")

    return ExpectedImprovement(delta_index_now=delta_now, delta_index_year5=delta_y5)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helper — builds contributions list
# ─────────────────────────────────────────────────────────────────────────────

def _build_contributions(
    request: AnalysisRequest,
) -> Tuple[List[Contribution], float, Dict[str, float]]:
    contributions: List[Contribution] = []

    for item in request.regimen:
        load, reason, is_protective = compute_compound_load(
            item.compound_id, item.dose_mg, request.genetics
        )
        compound = LIVER_LOAD_TABLE.get(item.compound_id)
        display_name = compound["display_name"] if compound else item.compound_id.title()

        contributions.append(
            Contribution(
                compound_id=item.compound_id,
                name=display_name,
                load=float(f"{load:.3f}"),
                reason=reason,
                is_protective=is_protective,
            )
        )

    lifestyle_penalty, lifestyle_breakdown = compute_lifestyle_penalties(request.lifestyle)

    # Add lifestyle contributions as synthetic entries
    for factor, penalty in lifestyle_breakdown.items():
        contributions.append(
            Contribution(
                compound_id=f"lifestyle_{factor.lower().replace(' ', '_')}",
                name=factor,
                load=float(f"{penalty:.1f}"),
                reason=_lifestyle_reason(factor, request.lifestyle),
                is_protective=False,
            )
        )

    return contributions, lifestyle_penalty, lifestyle_breakdown


def _lifestyle_reason(factor: str, lifestyle: Lifestyle) -> str:
    reasons = {
        "High Sugar Diet": f"At {lifestyle.sugar_g_per_day:.0f}g/day — chronically elevated fructose increases NAFLD risk.",
        "Alcohol Intake": f"At {lifestyle.alcohol_units_per_week} units/week — exceeds hepatotoxic threshold.",
        "Poor Sleep": f"At {lifestyle.sleep_hours_per_night}h/night — impairs hepatic regeneration and clearance.",
        "Sedentary Activity": "Sedentary lifestyle reduces metabolic clearance of hepatic substrates.",
        "High Stress": f"Stress level {lifestyle.stress_level}/10 — elevated cortisol increases liver inflammation markers.",
    }
    return reasons.get(factor, factor)


# ─────────────────────────────────────────────────────────────────────────────
# Main Orchestrator — run_liver_analysis
# ─────────────────────────────────────────────────────────────────────────────

def run_liver_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Master orchestrator. Runs all pipeline steps in order and returns
    a fully populated AnalysisResponse.
    """
    # Step 1: Validate
    request = validate_and_normalize(request)

    # Step 2 + 3: Build contributions (compounds + lifestyle)
    contributions, lifestyle_penalty, _ = _build_contributions(request)

    # Step 4: Aggregate liver index
    liver_index_now = aggregate_liver_index(contributions, lifestyle_penalty)

    # Step 5: Risk band + trajectory
    risk_level, decline_fraction = assign_risk_band(liver_index_now)
    trajectory = compute_trajectory(liver_index_now, decline_fraction, request.labs)

    # Projected drop %
    val = (liver_index_now - trajectory[5].liver_index) / liver_index_now * 100
    drop_pct = float(f"{val:.1f}")

    # Headline text
    if risk_level == "green":
        headline = f"Your liver is in good shape — index {liver_index_now:.0f}/100. Maintain your current routine."
    elif risk_level == "amber":
        headline = (
            f"Moderate liver stress detected — index {liver_index_now:.0f}/100. "
            f"Projected to decline ~{drop_pct:.0f}% by year 5 without changes."
        )
    else:
        headline = (
            f"Elevated liver risk — index {liver_index_now:.0f}/100. "
            f"Significant decline projected. Changes are strongly recommended."
        )

    risk_summary = RiskSummary(
        risk_level=risk_level,
        liver_index_now=liver_index_now,
        projected_drop_percent=drop_pct,
        headline=headline,
    )

    # Step 6: Recommendations
    recommendations = generate_recommendations(request, contributions)

    # Step 7: Recommendation deltas
    for rec in recommendations:
        rec.expected_improvement = compute_recommendation_delta(
            request, rec, liver_index_now, trajectory
        )

    # Compute optimized trajectory (all recs applied cumulatively)
    optimized_trajectory = _build_optimized_trajectory(request, trajectory, recommendations)
    for i, pt in enumerate(trajectory):
        pt.optimized_liver_index = optimized_trajectory[i].liver_index

    # Biological age
    val = request.patient.age + (100 - liver_index_now) * 0.3
    biological_age = float(f"{val:.1f}")
    biological_age = max(request.patient.age - 10, biological_age)  # safety floor

    # Polypharmacy score
    high_risk_count = sum(
        1
        for item in request.regimen
        for tag in (LIVER_LOAD_TABLE.get(item.compound_id, {}).get("tags", []))
        if tag in HIGH_RISK_TAGS
    )
    polypharmacy_score = min(
        100,
        len(request.regimen) * POLYPHARMACY_BASE_PER_COMPOUND
        + high_risk_count * POLYPHARMACY_HIGH_TAG_BONUS,
    )

    # Sort contributions: highest load first, protective items last
    contributions.sort(key=lambda c: (c.is_protective, -c.load))

    return AnalysisResponse(
        risk_summary=risk_summary,
        trajectory=trajectory,
        contributions=contributions,
        recommendations=recommendations,
        biological_age=biological_age,
        polypharmacy_score=polypharmacy_score,
    )


def _build_optimized_trajectory(
    request: AnalysisRequest,
    original_trajectory: List[TrajectoryPoint],
    recommendations: List[Recommendation],
) -> List[TrajectoryPoint]:
    """
    Builds a trajectory assuming all recommendations are adopted.
    Used to render the dashed 'optimized' line on the chart.
    """
    modified = copy.deepcopy(request)

    for rec in recommendations:
        if rec.id == "swap_ashwagandha_rhodiola":
            modified.regimen = [r for r in modified.regimen if r.compound_id != "ashwagandha"]
        elif rec.id == "reduce_sugar":
            modified.lifestyle.sugar_g_per_day = 90.0
        elif rec.id == "add_nac":
            from ..models.request import RegimenItem  # type: ignore
            if not any(r.compound_id == "nac" for r in modified.regimen):
                modified.regimen.append(RegimenItem(compound_id="nac", dose_mg=600))
        elif rec.id.startswith("reduce_"):
            cid = rec.id.replace("reduce_", "")
            for item in modified.regimen:
                if item.compound_id == cid:
                    item.dose_mg *= 0.5
                    break

    contribs, penalty, _ = _build_contributions(modified)
    opt_index = aggregate_liver_index(contribs, penalty)
    _, opt_decline = assign_risk_band(opt_index)
    return compute_trajectory(opt_index, opt_decline, modified.labs)
