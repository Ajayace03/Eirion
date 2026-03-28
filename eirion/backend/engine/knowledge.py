"""
EIRION Knowledge Tables — Phase 0
All hard-coded data for the rules-based liver toxicity engine.
Sources: PharmGKB, CPIC Guidelines, ToxCast, internal curation.
"""

from typing import Dict, Any, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Compound Liver Load Table — 15 curated compounds
# base: base liver load score (negative = protective)
# dose_normal: reference daily dose in mg
# protective: True if hepatoprotective (offsets load)
# tags: risk tags used by gene-drug rule matching
# display_name: human-readable name
# ─────────────────────────────────────────────────────────────────────────────
LIVER_LOAD_TABLE: Dict[str, Dict[str, Any]] = {
    "ashwagandha": {
        "base": 2,
        "dose_normal": 300,
        "protective": False,
        "tags": ["CYP2D6_substrate", "herb_hepatotoxic_reports"],
        "display_name": "Ashwagandha",
    },
    "metformin": {
        "base": 2,
        "dose_normal": 500,
        "protective": False,
        "tags": [],
        "display_name": "Metformin",
    },
    "omega3": {
        "base": -1,
        "dose_normal": 2000,
        "protective": True,
        "tags": ["anti_inflammatory"],
        "display_name": "Omega-3 Fish Oil",
    },
    "vitamin_d": {
        "base": 1,
        "dose_normal": 2000,
        "protective": False,
        "tags": ["fat_soluble"],
        "display_name": "Vitamin D3",
    },
    "nac": {
        "base": -3,
        "dose_normal": 600,
        "protective": True,
        "tags": ["antioxidant"],
        "display_name": "NAC (N-Acetyl Cysteine)",
    },
    "magnesium": {
        "base": 1,
        "dose_normal": 400,
        "protective": False,
        "tags": [],
        "display_name": "Magnesium Glycinate",
    },
    "zinc": {
        "base": 2,
        "dose_normal": 15,
        "protective": False,
        "tags": ["high_dose_hepatotoxic"],
        "display_name": "Zinc",
    },
    "quercetin": {
        "base": 2,
        "dose_normal": 500,
        "protective": False,
        "tags": ["CYP3A4_inhibitor"],
        "display_name": "Quercetin",
    },
    "berberine": {
        "base": 2,
        "dose_normal": 500,
        "protective": False,
        "tags": ["CYP2D6_substrate"],
        "display_name": "Berberine",
    },
    "curcumin": {
        "base": 1,
        "dose_normal": 500,
        "protective": False,
        "tags": ["anti_inflammatory"],
        "display_name": "Curcumin / Turmeric",
    },
    "coq10": {
        "base": 1,
        "dose_normal": 200,
        "protective": False,
        "tags": [],
        "display_name": "CoQ10 (Ubiquinol)",
    },
    "atorvastatin": {
        "base": 4,
        "dose_normal": 10,
        "protective": False,
        "tags": ["CYP2C9_substrate", "CYP3A4_substrate", "myopathy_risk"],
        "display_name": "Atorvastatin (Lipitor)",
    },
    "rosuvastatin": {
        "base": 4,
        "dose_normal": 10,
        "protective": False,
        "tags": ["CYP2C9_substrate", "myopathy_risk"],
        "display_name": "Rosuvastatin (Crestor)",
    },
    "sertraline": {
        "base": 3,
        "dose_normal": 50,
        "protective": False,
        "tags": ["CYP2D6_substrate", "CYP2C19_substrate"],
        "display_name": "Sertraline (Zoloft)",
    },
    "escitalopram": {
        "base": 3,
        "dose_normal": 10,
        "protective": False,
        "tags": ["CYP2D6_substrate", "CYP2C19_substrate"],
        "display_name": "Escitalopram (Lexapro)",
    },
}

# Default load for unknown compounds (conservative)
DEFAULT_LOAD = 2

# ─────────────────────────────────────────────────────────────────────────────
# Gene-Drug Rules (CPIC-Inspired)
# (gene, metabolizer_status, compound_tag, multiplier)
# ─────────────────────────────────────────────────────────────────────────────
GENE_DRUG_RULES: List[Tuple[str, str, str, float]] = [
    ("cyp2d6", "poor",         "CYP2D6_substrate",  1.5),   # CPIC: +50% load
    ("cyp2d6", "intermediate", "CYP2D6_substrate",  1.2),   # CPIC: +20% load
    ("cyp2d6", "ultra_rapid",  "CYP2D6_substrate",  0.8),   # Faster clearance
    ("cyp2c19", "poor",        "CYP2C19_substrate", 1.3),   # CPIC: +30% load
    ("cyp2c19", "ultra_rapid", "CYP2C19_substrate", 0.85),  # Higher clearance
]

# ─────────────────────────────────────────────────────────────────────────────
# Lifestyle Penalty Rules
# Thresholds are upper bounds; penalty applied for values exceeding threshold
# Format: list of (threshold, penalty) sorted ascending
# ─────────────────────────────────────────────────────────────────────────────
SUGAR_PENALTIES = [
    (60,   0),    # < 60 g/day: healthy range
    (120,  2),    # 60-120 g/day: moderately elevated fructose load
    (160,  5),    # 120-160 g/day: high NAFLD risk (Priya: 140)
    (float("inf"), 10),  # > 160 g/day: severe load
]

ALCOHOL_PENALTIES = [
    (7, 0),               # ≤ 7 units/week: within limit
    (14, 4),              # 7-14 units/week: moderate load
    (float("inf"), 8),    # > 14 units/week: hepatotoxic threshold
]

SLEEP_PENALTIES = [
    (5, 4),               # ≤ 5 h: impairs hepatic regeneration
    (6, 2),               # 5-6 h: moderate impairment
    (float("inf"), 0),    # > 6 h: no penalty
]

ACTIVITY_PENALTIES = {
    "sedentary": 2,  # Reduced metabolic clearance
    "light": 0,
    "moderate": 0,
    "intense": 0,
}

# Stress penalty: triggered at ≥ 8/10
STRESS_THRESHOLD = 8
STRESS_PENALTY = 2  # Chronic cortisol elevates liver inflammation markers

# ─────────────────────────────────────────────────────────────────────────────
# Trajectory Decline Parameters — by risk band
# ─────────────────────────────────────────────────────────────────────────────
TRAJECTORY_PARAMS = {
    "green": 0.05,   # ≥85 index: 5% 5-year decline
    "amber": 0.15,   # 70-84 index: 15% 5-year decline (Priya's scenario)
    "red":   0.30,   # <70 index: 30% 5-year decline
}

# Lab elevation adds extra decline risk
LAB_ELEVATION_BUMP = 0.05
LAB_ELEVATION_MAX = 0.35
AST_THRESHOLD = 40
ALT_THRESHOLD = 40

# ─────────────────────────────────────────────────────────────────────────────
# Risk Band Thresholds
# ─────────────────────────────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "green": 85,
    "amber": 70,
}

# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Templates
# ─────────────────────────────────────────────────────────────────────────────
RECOMMENDATION_RULES = [
    {
        "id": "swap_ashwagandha_rhodiola",
        "trigger": lambda req_ids, genetics, _: (
            "ashwagandha" in req_ids and genetics.cyp2d6_metabolizer == "poor"
        ),
        "action_type": "swap",
        "title": "Switch Ashwagandha → Rhodiola Rosea",
        "details": (
            "Ashwagandha is metabolized via CYP2D6. As a poor metabolizer, you clear it "
            "~50% slower than average, leading to withanolide accumulation and elevated "
            "hepatic load over months. Rhodiola Rosea provides similar adaptogenic benefits "
            "with a significantly lower hepatotoxicity profile and no CYP2D6 dependency."
        ),
        "confidence": 0.88,
        "evidence_refs": ["PharmGKB:PA166182476", "CPIC:CYP2D6"],
    },
    {
        "id": "reduce_sugar",
        "trigger": lambda req_ids, _, lifestyle: lifestyle.sugar_g_per_day > 120,
        "action_type": "behavior_change",
        "title": "Reduce Sugar Intake to ≤90 g/day",
        "details": (
            "At {sugar_g}g/day, chronic dietary fructose is a primary independent driver of "
            "non-alcoholic fatty liver disease (NAFLD). Reducing below 90g/day significantly "
            "lowers hepatic de novo lipogenesis and reduces cumulative oxidative stress."
        ),
        "confidence": 0.92,
        "evidence_refs": ["ToxCast:NAFLD_fructose", "PMID:31465498"],
    },
    {
        "id": "add_nac",
        "trigger": lambda req_ids, _, __: "nac" not in req_ids,
        "action_type": "add",
        "title": "Add NAC (N-Acetyl Cysteine) 600 mg/day",
        "details": (
            "NAC is a precursor to glutathione — the liver's primary antioxidant defense. "
            "It directly offsets oxidative stress from CYP450 metabolism of multiple "
            "compounds in your stack. Well-tolerated at 600 mg/day with strong safety profile."
        ),
        "confidence": 0.85,
        "evidence_refs": ["ToxCast:NAC_hepatoprotective", "PMID:16323102"],
    },
    {
        "id": "consult_statin_cyp2d6",
        "trigger": lambda req_ids, genetics, _: (
            any(s in req_ids for s in ["atorvastatin", "rosuvastatin"])
            and genetics.cyp2d6_metabolizer == "poor"
        ),
        "action_type": "consult",
        "title": "Discuss Statin Dose with Your Physician",
        "details": (
            "Your CYP2D6 poor metabolizer status may reduce clearance of statins, increasing "
            "plasma exposure and myopathy/hepatotoxicity risk. A pharmacogenomics-guided dose "
            "review with your prescribing physician is recommended."
        ),
        "confidence": 0.82,
        "evidence_refs": ["CPIC:statins_CYP2D6", "PharmGKB:PA166104940"],
    },
    {
        "id": "consult_ssri_cyp2d6",
        "trigger": lambda req_ids, genetics, _: (
            any(s in req_ids for s in ["sertraline", "escitalopram"])
            and genetics.cyp2d6_metabolizer == "poor"
        ),
        "action_type": "consult",
        "title": "Discuss SSRI Dose with Your Physician",
        "details": (
            "SSRIs like sertraline and escitalopram are CYP2D6 substrates. Poor metabolizers "
            "may accumulate higher plasma levels, increasing both efficacy and adverse effect "
            "risk. A dose review is clinically recommended."
        ),
        "confidence": 0.82,
        "evidence_refs": ["CPIC:SSRIs_CYP2D6", "PharmGKB:PA166182804"],
    },
]

# Polypharmacy score weights
POLYPHARMACY_BASE_PER_COMPOUND = 8
POLYPHARMACY_HIGH_TAG_BONUS = 5
HIGH_RISK_TAGS = {"CYP2D6_substrate", "CYP2C19_substrate", "herb_hepatotoxic_reports", "high_dose_hepatotoxic"}
