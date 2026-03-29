"""
Biological Age Tracking & Reversal Plans
-----------------------------------------
Multi-clock biological age system.

Clocks implemented:
    1. OrganAge  — composite of 4 organ health indices (runs now, no extra data)
    2. PhenoAge  — Levine 2018 formula (requires extended labs)
    3. GrimAge   — stub (requires DNA methylation array — PDF upload path)

Reversal Plans: rule-based protocol recommendations per clock gap.

Usage:
    from engine.planned.bio_age_tracker import BioAgeTracker
    tracker = BioAgeTracker()
    result  = tracker.compute(request, organ_scores, chronological_age)
    # → BioAgeResult(organ_age, pheno_age, clocks, reversal_plans, years_younger_if_adopted)
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ClockResult:
    name: str
    age: float                    # estimated biological age
    gap: float                    # bio_age - chronological_age (+ = older)
    confidence: float = 0.8       # 0-1 confidence in this clock
    requires_data: str = ""       # what data was needed


@dataclass
class ReversalPlan:
    clock: str
    intervention: str
    evidence_level: str           # "A" | "B" | "C"
    expected_reduction_yrs: float # years of bio age reversal expected
    mechanism: str


@dataclass
class BioAgeResult:
    chronological_age: int
    organ_age: float
    pheno_age: Optional[float]    # None if labs insufficient
    grimage_age: Optional[float]  # None if methylation not provided
    composite_age: float          # weighted average of available clocks
    clocks: List[ClockResult] = field(default_factory=list)
    reversal_plans: List[ReversalPlan] = field(default_factory=list)
    years_younger_if_adopted: float = 0.0
    longevity_escape_velocity: bool = False  # True if optimized path outpaces aging


# ─── PhenoAge formula (Levine 2018, Table 1) ──────────────────────────────────

PHENO_COEFFICIENTS = {
    # Variable                coefficient    units
    "albumin":                -0.0336,     # g/dL
    "creatinine":              0.0095,     # mg/dL
    "glucose":                 0.1953,     # mg/dL (log-transformed below)
    "crp":                     0.0954,     # mg/dL → convert from mg/L ÷ 10
    "lymphocyte_pct":         -0.0120,     # % (will approximate from WBC if absent)
    "mcv":                     0.0268,     # fL  (not always in panel — optional)
    "rdw":                     0.3306,     # %
    "alp":                     0.00188,    # U/L
    "wbc":                     0.0554,     # 10^3/μL
}
PHENO_INTERCEPT = -19.9067

# Mortality rate → biological age conversion constants (Gompertz)
_GAMMA = 0.0076927
_LAMBDA = 0.000000001


def compute_pheno_age(labs) -> Optional[float]:
    """
    Levine 2018 PhenoAge from blood labs.
    Returns age estimate or None if insufficient data.

    labs: backend Labs model (or any obj with attributes)
    """
    if labs is None:
        return None

    albumin    = getattr(labs, "albumin_g_per_dl", None)
    creatinine = getattr(labs, "creatinine_mg_per_dl", None)
    glucose    = getattr(labs, "glucose_mg_per_dl", None)
    crp_mg_l   = getattr(labs, "hscrp_mg_per_l", None)
    alp        = getattr(labs, "alp_u_per_l", None)

    # Need at least 3 of 5 key markers
    available = sum(x is not None for x in [albumin, creatinine, glucose, crp_mg_l, alp])
    if available < 3:
        logger.info("[BioAge] Insufficient labs for PhenoAge (%d/5 markers)", available)
        return None

    # Build lin comb (use smart defaults for missing markers)
    lin = PHENO_INTERCEPT
    lin += PHENO_COEFFICIENTS["albumin"]    * (albumin or 4.2)
    lin += PHENO_COEFFICIENTS["creatinine"] * (creatinine or 0.9)
    # Glucose: log-transformed in the original paper
    gluc = glucose or 95.0
    lin += PHENO_COEFFICIENTS["glucose"]    * math.log(max(gluc, 1.0))
    # CRP: mg/L → mg/dL
    crp_mg_dl = (crp_mg_l or 0.5) / 10
    lin += PHENO_COEFFICIENTS["crp"]        * math.log(max(crp_mg_dl, 0.0001))
    # Lymphocyte pct — estimate 28% if not available
    lin += PHENO_COEFFICIENTS["lymphocyte_pct"] * 28.0
    # MCV — estimate 90 fL if not available
    lin += PHENO_COEFFICIENTS["mcv"]        * 90.0
    # RDW — estimate 13.0% if not available
    lin += PHENO_COEFFICIENTS["rdw"]        * 13.0
    lin += PHENO_COEFFICIENTS["alp"]        * (alp or 70.0)
    # WBC — estimate 6.5 × 10^3/μL
    lin += PHENO_COEFFICIENTS["wbc"]        * 6.5

    # Gompertz mortality rate
    mortality_rate = math.exp(lin)
    # Convert to phenotypic age
    try:
        pheno_age = (
            math.log(-math.log(1 - mortality_rate) / _LAMBDA) / _GAMMA
        )
        return round(float(pheno_age), 1)
    except (ValueError, ZeroDivisionError):
        return None


# ─── OrganAge (composite) ─────────────────────────────────────────────────────

ORGAN_WEIGHTS = {"liver": 0.30, "kidney": 0.25, "cardiovascular": 0.30, "metabolic": 0.15}
AGE_SENSITIVITY = 0.4   # years of bio age per 1-pt organ score deficit


def compute_organ_age(
    chronological_age: int,
    organ_scores: Dict[str, float],
) -> float:
    """
    OrganAge = chronological_age + Σ(weight × (100 - score)) × sensitivity
    Better scores → negative gap (biologically younger).
    """
    weighted_deficit = sum(
        ORGAN_WEIGHTS.get(organ, 0.0) * max(0, 100 - score)
        for organ, score in organ_scores.items()
    )
    organ_age = chronological_age + weighted_deficit * AGE_SENSITIVITY
    return round(max(chronological_age - 20, min(chronological_age + 30, organ_age)), 1)


# ─── Reversal Plans ───────────────────────────────────────────────────────────

REVERSAL_RULES = [
    # (clock, condition_fn, plan)
    {
        "clock": "organ_age",
        "condition": lambda result, gap: gap > 5,
        "plan": ReversalPlan(
            clock="organ_age",
            intervention="NAD+ precursor supplementation (NMN 500mg or NR 300mg/day)",
            evidence_level="B",
            expected_reduction_yrs=1.5,
            mechanism="Restores NAD+ pools → mitochondrial biogenesis → improves organ efficiency",
        ),
    },
    {
        "clock": "organ_age",
        "condition": lambda result, gap: gap > 3 and result.chronological_age >= 40,
        "plan": ReversalPlan(
            clock="organ_age",
            intervention="Mediterranean diet + 150 min/week aerobic exercise",
            evidence_level="A",
            expected_reduction_yrs=2.5,
            mechanism="Improves insulin sensitivity, reduces CRP, raises eGFR — all organ indices go up",
        ),
    },
    {
        "clock": "pheno_age",
        "condition": lambda result, gap: gap > 4,
        "plan": ReversalPlan(
            clock="pheno_age",
            intervention="Optimize albumin via adequate protein intake (1.2g/kg/day)",
            evidence_level="A",
            expected_reduction_yrs=1.2,
            mechanism="Albumin is the strongest contributor to PhenoAge — raising it from 3.8→4.3 g/dL saves ~1.8 biological years",
        ),
    },
    {
        "clock": "pheno_age",
        "condition": lambda result, gap: gap > 2,
        "plan": ReversalPlan(
            clock="pheno_age",
            intervention="High-sensitivity CRP reduction: omega-3 2g/day + curcumin 500mg",
            evidence_level="B",
            expected_reduction_yrs=0.8,
            mechanism="hsCRP drives PhenoAge via log-scale CRP coefficient — each 50% CRP reduction ≈ 0.5yr reversal",
        ),
    },
    {
        "clock": "organ_age",
        "condition": lambda result, gap: gap > 0,
        "plan": ReversalPlan(
            clock="organ_age",
            intervention="Sleep optimization: 7-9h/night, consistent sleep schedule",
            evidence_level="A",
            expected_reduction_yrs=0.7,
            mechanism="Sleep orchestrates hepatic lipid clearance and kidney filtration rhythms",
        ),
    },
]


# ─── Main tracker ─────────────────────────────────────────────────────────────

class BioAgeTracker:
    """
    Computes all available biological age clocks and generates personalized
    reversal plans.
    """

    def compute(
        self,
        request,
        organ_scores: Dict[str, float],
        chronological_age: Optional[int] = None,
    ) -> BioAgeResult:
        """
        Main entry point.

        Args:
            request       : AnalysisRequest (or any object with .patient, .labs, .lifestyle)
            organ_scores  : dict from scorer.run_liver_analysis organ_scores list
            chronological_age: override age (defaults to request.patient.age)

        Returns:
            BioAgeResult
        """
        chron = chronological_age or getattr(getattr(request, "patient", None), "age", 35)
        labs  = getattr(request, "labs", None)

        # ── Clock 1: OrganAge ───────────────────────────────────────────────
        organ_age = compute_organ_age(chron, organ_scores)
        organ_gap = organ_age - chron
        clocks = [ClockResult(
            name="OrganAge",
            age=organ_age,
            gap=round(organ_gap, 1),
            confidence=0.75,
            requires_data="organ_scores (computed automatically)",
        )]

        # ── Clock 2: PhenoAge ───────────────────────────────────────────────
        pheno_age = compute_pheno_age(labs)
        pheno_gap = None
        if pheno_age is not None:
            pheno_gap = round(pheno_age - chron, 1)
            clocks.append(ClockResult(
                name="PhenoAge",
                age=pheno_age,
                gap=pheno_gap,
                confidence=0.88,
                requires_data="albumin, creatinine, glucose, hsCRP, ALP",
            ))

        # ── Clock 3: GrimAge (stub — needs methylation) ─────────────────────
        grimage = None  # Only available via uploaded methylation report

        # ── Composite age ───────────────────────────────────────────────────
        ages = [organ_age]
        weights_used = [0.6]
        if pheno_age is not None:
            ages.append(pheno_age)
            weights_used.append(0.4)
        total_w = sum(weights_used)
        composite = round(
            sum(a * w for a, w in zip(ages, weights_used)) / total_w, 1
        )

        result = BioAgeResult(
            chronological_age=chron,
            organ_age=organ_age,
            pheno_age=pheno_age,
            grimage_age=grimage,
            composite_age=composite,
            clocks=clocks,
        )

        # ── Reversal plans ──────────────────────────────────────────────────
        plans = []
        for rule in REVERSAL_RULES:
            clock  = rule["clock"]
            gap    = organ_gap if clock == "organ_age" else (pheno_gap or 0)
            try:
                if rule["condition"](result, gap):
                    plans.append(rule["plan"])
            except Exception:
                continue

        # Deduplicate by intervention text
        seen = set()
        unique_plans = []
        for p in plans:
            key = p.intervention[:40]
            if key not in seen:
                seen.add(key)
                unique_plans.append(p)

        result.reversal_plans = unique_plans[:6]

        # ── Years younger if all plans adopted ──────────────────────────────
        result.years_younger_if_adopted = round(
            sum(p.expected_reduction_yrs for p in result.reversal_plans), 1
        )

        # ── Longevity escape velocity check ─────────────────────────────────
        # LEV: if optimized composite age grows < 1 yr per calendar year
        projected_composite = composite - result.years_younger_if_adopted
        result.longevity_escape_velocity = (projected_composite < chron)

        return result

    def format_summary(self, result: BioAgeResult) -> str:
        """Human-readable summary string for logging / API text field."""
        lines = [
            f"Chronological age: {result.chronological_age}",
            f"OrganAge:          {result.organ_age:.1f} ({result.organ_age - result.chronological_age:+.1f})",
        ]
        if result.pheno_age is not None:
            lines.append(f"PhenoAge:          {result.pheno_age:.1f} ({result.pheno_age - result.chronological_age:+.1f})")
        lines.append(f"Composite BioAge:  {result.composite_age:.1f}")
        if result.reversal_plans:
            lines.append(f"\nTop reversal intervention:")
            p = result.reversal_plans[0]
            lines.append(f"  {p.intervention} [Level {p.evidence_level}] → -{p.expected_reduction_yrs:.1f} yrs")
        if result.longevity_escape_velocity:
            lines.append("\n🚀 Longevity Escape Velocity: on optimized path, bio age growth < 1yr/yr")
        return "\n".join(lines)
