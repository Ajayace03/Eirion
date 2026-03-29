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

from models.request import AnalysisRequest, Food, Genetics, LifestyleIntake
from models.response import (
    AnalysisResponse,
    Contribution,
    CompoundGeneChain,
    DDIFlag,
    ExpectedImprovement,
    GeneInteractionDetail,
    OrganScore,
    Recommendation,
    RiskSummary,
    TrajectoryPoint,
)
from .knowledge import (  # type: ignore
    ALT_THRESHOLD,
    AST_THRESHOLD,
    ACTIVITY_PENALTIES,
    ALCOHOL_PENALTIES,
    CALORIE_PENALTIES,
    DEFAULT_LOAD,
    DIET_TYPE_MODIFIERS,
    DIET_TYPE_REASONS,
    FIBER_PENALTIES,
    FOOD_RECOMMENDATION_RULES,
    GENE_DRUG_RULES,
    HIGH_RISK_TAGS,
    LAB_ELEVATION_BUMP,
    LAB_ELEVATION_MAX,
    LIVER_LOAD_TABLE,
    POLYPHARMACY_BASE_PER_COMPOUND,
    POLYPHARMACY_HIGH_TAG_BONUS,
    PROCESSED_FOOD_PENALTIES,
    RECOMMENDATION_RULES,
    RED_MEAT_PENALTIES,
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
    from .inference import predictor, ML_READY

    if "smiles" in compound and ML_READY and predictor.rf_model is not None:
        prob = predictor.predict_toxicity(compound["smiles"])
        # Phase 0: ML tunes the curated base by at most ±50%.
        # Tox21 is a broad molecular toxicity model (not liver-specific); using
        # prob*10 directly produces wildly inflated scores vs the clinically
        # calibrated base values. This formula preserves clinical calibration
        # while still encoding the ML signal. Full recalibration is Phase 1.
        # prob=0 → 0.5× base  |  prob=0.5 → 1.0× base  |  prob=1 → 1.5× base
        ml_base = float(f"{compound['base'] * (0.5 + prob):.2f}")
    else:
        # Stub / no ML weights: use manually curated base score from knowledge table
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

def compute_lifestyle_penalties(lifestyle: LifestyleIntake) -> Tuple[float, Dict[str, float]]:
    """Returns (total_penalty, breakdown_dict). All penalties are negative numbers."""
    breakdown: Dict[str, float] = {}

    sugar_pen = _apply_threshold_penalties(lifestyle.sugar_g_per_day, SUGAR_PENALTIES)
    breakdown["High Sugar Diet"] = float(sugar_pen)

    alcohol_pen = _apply_threshold_penalties(lifestyle.alcohol_drinks_per_week, ALCOHOL_PENALTIES)
    breakdown["Alcohol Intake"] = alcohol_pen

    sleep_pen = _apply_threshold_penalties(lifestyle.sleep_hours_avg, SLEEP_PENALTIES)
    breakdown["Poor Sleep"] = sleep_pen

    # Activity: sedentary (<60 min/wk) = +2 penalty; very active (>=150) = -2 credit;
    # moderate (60-149) = no change
    if lifestyle.exercise_mins_per_week >= 150:
        activity_pen = -2.0  # protective credit
    elif lifestyle.exercise_mins_per_week < 60:
        activity_pen = 2.0   # sedentary penalty
    else:
        activity_pen = 0.0   # moderate — neutral
    breakdown["Activity Level"] = activity_pen

    stress_pen = STRESS_PENALTY if lifestyle.stress_level >= STRESS_THRESHOLD else 0
    breakdown["High Stress"] = stress_pen

    env_pen = 2.0 if lifestyle.environmental_toxin_exposure >= 8 else 0.0
    if env_pen > 0:
        breakdown["High Toxin Exposure"] = env_pen
    
    processed_pen = 3.0 if lifestyle.processed_food_frequency >= 8 else 0.0
    if processed_pen > 0:
        breakdown["Ultra-Processed Diet"] = processed_pen

    total = sum(breakdown.values())
    # Remove zero-penalty entries for cleanliness
    breakdown = {k: v for k, v in breakdown.items() if v != 0}

    return total, breakdown


# ───────────────────────────────────────────────────────────────────────────────
# Step 3b — Food / Diet Penalties
# ───────────────────────────────────────────────────────────────────────────────

def compute_food_penalty(food: Optional["Food"]) -> Tuple[float, Dict[str, float]]:
    """
    Returns (total_penalty, breakdown_dict) for food/diet inputs.
    Positive penalty values subtract from liver_index.
    Negative penalty values (e.g. Mediterranean, high fiber) are protective credits.
    """
    if food is None:
        return 0.0, {}

    breakdown: Dict[str, float] = {}

    if food.calories_per_day is not None:
        cal_pen = _apply_threshold_penalties(food.calories_per_day, CALORIE_PENALTIES)
        if cal_pen:
            breakdown["Excess Caloric Intake"] = float(cal_pen)

    if food.processed_food_pct is not None:
        proc_pen = _apply_threshold_penalties(food.processed_food_pct, PROCESSED_FOOD_PENALTIES)
        if proc_pen:
            breakdown["Ultra-Processed Food Diet"] = float(proc_pen)

    if food.red_meat_g_per_week is not None:
        meat_pen = _apply_threshold_penalties(food.red_meat_g_per_week, RED_MEAT_PENALTIES)
        if meat_pen:
            breakdown["High Red Meat Intake"] = float(meat_pen)

    if food.fiber_g_per_day is not None:
        # Fiber table returns negative penalty for high fiber (protective)
        fiber_pen = _apply_threshold_penalties(food.fiber_g_per_day, FIBER_PENALTIES)
        if fiber_pen < 0:
            breakdown["High Fiber Diet"] = float(fiber_pen)  # protective
        elif fiber_pen > 0:
            breakdown["Low Fiber Intake"] = float(fiber_pen)

    if food.diet_type is not None:
        diet_mod = DIET_TYPE_MODIFIERS.get(food.diet_type, 0.0)
        # diet_mod > 0 means bad diet (more load) → positive penalty
        # diet_mod < 0 means good diet (protective) → negative value (credit)
        if diet_mod > 0:
            breakdown[f"Diet Pattern ({food.diet_type.title()})"] = diet_mod   # harmful
        elif diet_mod < 0:
            breakdown[f"Diet Pattern ({food.diet_type.title()})"] = diet_mod   # protective

    total = sum(breakdown.values())
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

        if triggered and not any(r.id == rule["id"] for r in recs):
            details = rule["details"]
            if "{sugar_g}" in details:
                details = details.format(sugar_g=int(request.lifestyle.sugar_g_per_day))
            recs.append(
                Recommendation(
                    id=rule["id"],
                    action_type=rule["action_type"],
                    title=rule["title"],
                    details=details,
                    expected_improvement=ExpectedImprovement(delta_index_now=0.0, delta_index_year5=0.0),
                    confidence=rule["confidence"],
                    evidence_refs=rule["evidence_refs"],
                )
            )

    # Food recommendations
    for rule in FOOD_RECOMMENDATION_RULES:
        try:
            triggered = rule["trigger"](request.food)
        except Exception:
            triggered = False

        if triggered and not any(r.id == rule["id"] for r in recs):
            recs.append(
                Recommendation(
                    id=rule["id"],
                    action_type=rule["action_type"],
                    title=rule["title"],
                    details=rule["details"],
                    expected_improvement=ExpectedImprovement(delta_index_now=0.0, delta_index_year5=0.0),
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
        from models.request import RegimenItem
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
                is_protective=(penalty < 0),
            )
        )

    # Food / diet contributions
    food_penalty, food_breakdown = compute_food_penalty(request.food)
    for factor, penalty in food_breakdown.items():
        is_food_protective = penalty < 0
        contributions.append(
            Contribution(
                compound_id=f"food_{factor.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                name=factor,
                load=float(f"{penalty:.1f}"),
                reason=_food_reason(factor, request.food),
                is_protective=is_food_protective,
            )
        )

    total_non_food_penalty = lifestyle_penalty
    return contributions, total_non_food_penalty + food_penalty, lifestyle_breakdown


def _lifestyle_reason(factor: str, lifestyle: LifestyleIntake) -> str:
    reasons = {
        "High Sugar Diet": f"At {lifestyle.sugar_g_per_day:.0f}g/day — chronically elevated fructose increases NAFLD risk.",
        "Alcohol Intake": f"At {lifestyle.alcohol_drinks_per_week} drinks/week — exceeds hepatotoxic threshold.",
        "Poor Sleep": f"At {lifestyle.sleep_hours_avg}h/night — impairs hepatic regeneration and clearance.",
        "Activity Level": f"At {lifestyle.exercise_mins_per_week} mins/week of exercise.",
        "High Stress": f"Stress level {lifestyle.stress_level}/10 — elevated cortisol increases liver inflammation markers.",
        "High Toxin Exposure": f"Reported high environmental toxin exposure (level {lifestyle.environmental_toxin_exposure}) adds direct load to detox pathways.",
        "Ultra-Processed Diet": f"Highly processed diet patterns (frequency {lifestyle.processed_food_frequency}/10) increase oxidative stress.",
    }
    return reasons.get(factor, factor)


def _food_reason(factor: str, food: Optional["Food"]) -> str:
    if food is None:
        return factor
    if "Diet Pattern" in factor and food.diet_type:
        return DIET_TYPE_REASONS.get(food.diet_type, factor)
    reasons = {
        "Excess Caloric Intake": f"At {food.calories_per_day:.0f} kcal/day — excess calories increase hepatic de novo lipogenesis.",
        "Ultra-Processed Food Diet": f"At {food.processed_food_pct:.0f}% ultra-processed — AGEs and additives drive hepatic inflammation.",
        "High Red Meat Intake": f"At {food.red_meat_g_per_week:.0f}g/week — elevated heme iron and nitrosamines stress hepatocytes.",
        "Low Fiber Intake": f"At {food.fiber_g_per_day:.0f}g/day fiber — impairs gut-liver axis and SCFA production.",
        "High Fiber Diet": f"At {food.fiber_g_per_day:.0f}g/day fiber — protects gut-liver axis and reduces hepatic inflammation.",
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

    # Projected drop % — clamp to 0 so we never show a negative "drop"
    raw_drop = (liver_index_now - trajectory[5].liver_index) / liver_index_now * 100
    drop_pct = float(f"{max(0.0, raw_drop):.1f}")

    # Headline text
    if risk_level == "green":
        headline = f"Your liver is in good shape — index {liver_index_now:.0f}/100. Maintain your current routine."
    elif risk_level == "amber":
        if drop_pct > 0:
            headline = (
                f"Moderate liver stress detected — index {liver_index_now:.0f}/100. "
                f"Projected to decline ~{drop_pct:.0f}% by year 5 without changes."
            )
        else:
            headline = (
                f"Moderate liver stress detected — index {liver_index_now:.0f}/100. "
                f"On current trajectory. Consider the recommendations below."
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

    # ── Phase 2: Multi-organ scoring ─────────────────────────────────────────
    organ_scores, compound_gene_chains, ddi_flags, active_pathways = compute_multi_organ_data(
        request, liver_index_now
    )

    # ── Phase 3: Multi-timeframe projections ─────────────────────────────────
    from engine.projector import compute_multi_organ_projection
    multi_organ_projection = compute_multi_organ_projection(organ_scores, request)

    return AnalysisResponse(
        risk_summary=risk_summary,
        trajectory=trajectory,
        contributions=contributions,
        recommendations=recommendations,
        biological_age=biological_age,
        polypharmacy_score=polypharmacy_score,
        organ_scores=organ_scores,
        compound_gene_chains=compound_gene_chains,
        ddi_flags=ddi_flags,
        active_pathways=active_pathways,
        gnn_version="rules_v1",
        multi_organ_projection=multi_organ_projection,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Multi-Organ Scoring (Phase 2 — Knowledge Graph Rules)
# ─────────────────────────────────────────────────────────────────────────────

def compute_multi_organ_data(request: AnalysisRequest, liver_index_now: float):
    """
    Uses the knowledge graph to produce per-organ scores, compound→gene chains,
    and DDI flags.

    Returns:
        organ_scores: List[OrganScore]
        compound_gene_chains: List[CompoundGeneChain]
        ddi_flags: List[DDIFlag]
        active_pathways: List[str]
    """
    from engine.graph_builder import PatientGraph
    from engine.knowledge_graph import PATHWAY_GRAPH, COMPOUND_INTERACTIONS, build_pathway_chain, detect_ddis, get_gene_multiplier

    pg = PatientGraph(request)
    genetics_dict = pg.genetics_dict

    # ── 1. Baseline organ scores (healthy person = 80/100) ─────────────────
    organ_loads: dict = {"liver": 0.0, "kidney": 0.0, "cardiovascular": 0.0, "metabolic": 0.0}
    organ_pathway_map: dict = {o: [] for o in organ_loads}

    # ── 2. Condition-based organ penalties ────────────────────────────────
    for cd in pg.condition_data:
        for organ, penalty in cd["organs"].items():
            if organ in organ_loads:
                organ_loads[organ] += penalty
        for pathway_id in cd["pathway_activations"]:
            for organ in PATHWAY_GRAPH.get(pathway_id, {}).get("organs", []):
                if organ in organ_pathway_map and pathway_id not in organ_pathway_map[organ]:
                    organ_pathway_map[organ].append(pathway_id)

    # ── 3. Compound pathway activations → organ impact ───────────────────
    compound_gene_chains = []
    for cd in pg.compound_data:
        comp_id = cd["compound_id"]
        comp_kg = COMPOUND_INTERACTIONS.get(comp_id, {})

        # Gene interaction details
        gene_details = []
        for gi in comp_kg.get("gene_interactions", []):
            gene = gi["gene"]
            field_map = {
                "CYP2D6": "cyp2d6_metabolizer", "CYP2C19": "cyp2c19_metabolizer",
                "CYP3A4": "cyp3a4_metabolizer", "CYP2C9": "cyp2c9_metabolizer",
                "CYP1A2": "cyp1a2_metabolizer", "SLCO1B1": "slco1b1_function",
                "UGT1A1": "ugt1a1_function",
            }
            phenotype = genetics_dict.get(field_map.get(gene, ""), "unknown")
            mult = get_gene_multiplier(gi, genetics_dict)
            gene_details.append(GeneInteractionDetail(
                gene=gene,
                phenotype=phenotype,
                multiplier=mult,
                evidence=gi.get("evidence", ""),
            ))

        # Pathway chain explanation
        pathway_chain = build_pathway_chain(comp_id, genetics_dict) or []

        # Per-organ load contribution from pathway activations
        organ_impacts: dict = {}
        for pa in comp_kg.get("pathway_activations", []):
            pdata = PATHWAY_GRAPH.get(pa["pathway"], {})
            delta = pa["delta"]
            severity = pdata.get("severity_weight", 1.0)
            gene_mult = cd["gene_multiplier"]

            for organ in pdata.get("organs", []):
                if organ in organ_loads:
                    contribution = delta * severity * gene_mult
                    organ_loads[organ] += contribution
                    organ_impacts[organ] = organ_impacts.get(organ, 0.0) + contribution
                    if delta > 0 and pa["pathway"] not in organ_pathway_map.get(organ, []):
                        organ_pathway_map[organ].append(pa["pathway"])

        compound_gene_chains.append(CompoundGeneChain(
            compound_id=comp_id,
            display_name=cd["display_name"],
            gene_interactions=gene_details,
            pathway_chain=pathway_chain,
            organ_impacts={o: round(v, 2) for o, v in organ_impacts.items()},
        ))

    # ── 4. Lifestyle modifiers ─────────────────────────────────────────────
    ls = request.lifestyle
    if ls.alcohol_drinks_per_week > 7:
        organ_loads["liver"] += (ls.alcohol_drinks_per_week - 7) * 0.5
    if ls.stress_level >= 7:
        organ_loads["metabolic"] += (ls.stress_level - 6) * 1.5
        organ_loads["cardiovascular"] += (ls.stress_level - 6) * 1.0
    if ls.sleep_hours_avg < 6:
        organ_loads["metabolic"] += (6 - ls.sleep_hours_avg) * 2.0
    if ls.smoking_status == "current":
        organ_loads["cardiovascular"] += 10.0
        organ_loads["liver"] += 3.0

    # ── 5. Lab adjustments ───────────────────────────────────────────────
    labs = request.labs
    if labs:
        if labs.egfr_ml_per_min is not None and labs.egfr_ml_per_min < 60:
            organ_loads["kidney"] += (60 - labs.egfr_ml_per_min) * 0.3
        if labs.ldl_mg_per_dl is not None and labs.ldl_mg_per_dl > 130:
            organ_loads["cardiovascular"] += (labs.ldl_mg_per_dl - 130) * 0.08
        if labs.hba1c_pct is not None and labs.hba1c_pct > 5.7:
            organ_loads["metabolic"] += (labs.hba1c_pct - 5.7) * 8.0
        if labs.hscrp_mg_per_l is not None and labs.hscrp_mg_per_l > 1.0:
            organ_loads["cardiovascular"] += labs.hscrp_mg_per_l * 2.0
            organ_loads["liver"] += labs.hscrp_mg_per_l * 1.0

    # ── 6. Convert loads → 0-100 health index (100 = optimal) ────────────
    def load_to_index(organ: str, load: float) -> float:
        # Baseline load representing a moderate lifestyle with no conditions
        baseline_loads = {"liver": 20.0, "kidney": 15.0, "cardiovascular": 18.0, "metabolic": 16.0}
        total = baseline_loads.get(organ, 18.0) + max(load, 0)
        raw = max(0, 100 - total * 1.5)
        return round(_clamp(raw, 10.0, 95.0), 1)

    def risk_for(index: float) -> str:
        if index >= 75: return "green"
        if index >= 55: return "amber"
        return "red"

    def top_driver(organ: str) -> str:
        # Find compound with highest impact on this organ
        top = ("", 0.0)
        for cgc in compound_gene_chains:
            impact = cgc.organ_impacts.get(organ, 0.0)
            if abs(impact) > abs(top[1]):
                top = (cgc.display_name, impact)
        if top[0]:
            return top[0]
        # Fall back to condition
        for cd in pg.condition_data:
            if organ in cd["organs"] and cd["organs"][organ] > 0:
                return cd["condition_id"].replace("_", " ").title()
        return "Lifestyle"

    # Use our existing liver_index_now for liver (already calibrated)
    organ_scores_list = [
        OrganScore(
            organ="liver",
            score=liver_index_now,
            risk_level=risk_for(liver_index_now),
            primary_driver=top_driver("liver"),
            active_pathways=organ_pathway_map.get("liver", [])[:4],
            projected_5yr=max(10, liver_index_now - abs(organ_loads["liver"]) * 0.5),
        ),
        OrganScore(
            organ="kidney",
            score=load_to_index("kidney", organ_loads["kidney"]),
            risk_level=risk_for(load_to_index("kidney", organ_loads["kidney"])),
            primary_driver=top_driver("kidney"),
            active_pathways=organ_pathway_map.get("kidney", [])[:4],
            projected_5yr=load_to_index("kidney", organ_loads["kidney"] * 1.2),
        ),
        OrganScore(
            organ="cardiovascular",
            score=load_to_index("cardiovascular", organ_loads["cardiovascular"]),
            risk_level=risk_for(load_to_index("cardiovascular", organ_loads["cardiovascular"])),
            primary_driver=top_driver("cardiovascular"),
            active_pathways=organ_pathway_map.get("cardiovascular", [])[:4],
            projected_5yr=load_to_index("cardiovascular", organ_loads["cardiovascular"] * 1.15),
        ),
        OrganScore(
            organ="metabolic",
            score=load_to_index("metabolic", organ_loads["metabolic"]),
            risk_level=risk_for(load_to_index("metabolic", organ_loads["metabolic"])),
            primary_driver=top_driver("metabolic"),
            active_pathways=organ_pathway_map.get("metabolic", [])[:4],
            projected_5yr=load_to_index("metabolic", organ_loads["metabolic"] * 1.1),
        ),
    ]

    # ── 7. DDI Flags ──────────────────────────────────────────────────────
    raw_ddis = detect_ddis([{"compound_id": item.compound_id} for item in request.regimen])
    ddi_flags_list = [
        DDIFlag(
            compound_a=d["compound_a"],
            compound_b=d["compound_b"],
            risk_level=d["risk_level"],
            mechanism=d["mechanism"],
            recommendation=d["recommendation"],
            evidence=d.get("evidence", ""),
        )
        for d in raw_ddis
    ]

    # ── 8. Active pathway dedup ───────────────────────────────────────────
    all_pathways = []
    for pathways in organ_pathway_map.values():
        for p in pathways:
            if p not in all_pathways:
                all_pathways.append(p)

    return organ_scores_list, compound_gene_chains, ddi_flags_list, all_pathways


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
            from models.request import RegimenItem
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
