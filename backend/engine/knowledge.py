"""
EIRION Knowledge Tables — Phase 0
All hard-coded data for the rules-based liver toxicity engine.
Sources: PharmGKB, CPIC Guidelines, ToxCast, internal curation.
"""

from typing import Dict, Any, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Compound Liver Load Table — 15 curated compounds
# base: base liver load score (negative = protective) — values match spec §8.1
# dose_normal: reference daily dose in mg
# protective: True if hepatoprotective (offsets load)
# tags: risk tags used by gene-drug rule matching
# display_name: human-readable name
# ─────────────────────────────────────────────────────────────────────────────
LIVER_LOAD_TABLE: Dict[str, Dict[str, Any]] = {
    "ashwagandha": {
        "smiles": "CC1=C(C(=O)OC1C2C(CC3(C2(CC(C4C3(CCC(C4(C)C)O)C)O)C)O)C)C",
        "base": 7,  # Spec §8.1: withanolide accumulation + CYP2D6 substrate
        "dose_normal": 300,
        "protective": False,
        "tags": ["CYP2D6_substrate", "herb_hepatotoxic_reports"],
        "display_name": "Ashwagandha",
    },
    "metformin": {
        "smiles": "CN(C)C(=N)N=C(N)N",
        "base": 3,  # Spec §8.1
        "dose_normal": 500,
        "protective": False,
        "tags": [],
        "display_name": "Metformin",
    },
    "omega3": {
        "smiles": "CCC=CCC=CCC=CCC=CCC=CCCCC(=O)O",
        "base": -1,  # Spec §8.1: hepatoprotective (anti_inflammatory)
        "dose_normal": 2000,
        "protective": True,
        "tags": ["anti_inflammatory"],
        "display_name": "Omega-3 Fish Oil",
    },
    "vitamin_d": {
        "smiles": "CC(C)CCCC(C)C1CCC2C1(CCCC2=CC=C3CC(CCC3=C)O)C",
        "base": 2,  # Spec §8.1: fat_soluble — note: high-dose (5000IU) above normal
        "dose_normal": 2000,
        "protective": False,
        "tags": ["fat_soluble"],
        "display_name": "Vitamin D3",
    },
    "nac": {
        "smiles": "CC(=O)NC(CS)C(=O)O",
        "base": -3,  # Spec §8.1: PROTECTIVE (antioxidant)
        "dose_normal": 600,
        "protective": True,
        "tags": ["antioxidant"],
        "display_name": "NAC (N-Acetyl Cysteine)",
    },
    "magnesium": {
        "smiles": "C(C(=O)O)N.C(C(=O)O)N.[Mg]",
        "base": 1,  # Spec §8.1
        "dose_normal": 400,
        "protective": False,
        "tags": [],
        "display_name": "Magnesium Glycinate",
    },
    "zinc": {
        "smiles": "[Zn]",
        "base": 2,  # Spec §8.1
        "dose_normal": 15,
        "protective": False,
        "tags": ["high_dose_hepatotoxic"],
        "display_name": "Zinc",
    },
    "quercetin": {
        "smiles": "C1=CC(=C(C=C1C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O)O",
        "base": 2,  # Spec §8.1
        "dose_normal": 500,
        "protective": False,
        "tags": ["CYP3A4_inhibitor"],
        "display_name": "Quercetin",
    },
    "berberine": {
        "smiles": "COC1=C(C2=C(C=C1)C3=C(CC[N+]4=C3C=C5C(=C4)C=C(C(=C5)O)O)C=C2)OC",
        "base": 4,  # Spec §8.1
        "dose_normal": 500,
        "protective": False,
        "tags": ["CYP2D6_substrate"],
        "display_name": "Berberine",
    },
    "curcumin": {
        "smiles": "COC1=C(C=CC(=C1)C=CC(=O)CC(=O)C=CC2=CC(=C(C=C2)O)OC)O",
        "base": 1,  # Spec §8.1
        "dose_normal": 500,
        "protective": False,
        "tags": ["anti_inflammatory"],
        "display_name": "Curcumin / Turmeric",
    },
    "coq10": {
        "smiles": "CC1=C(C(=O)C(=C(C1=O)OC)OC)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)C",
        "base": 1,  # Spec §8.1
        "dose_normal": 200,
        "protective": False,
        "tags": [],
        "display_name": "CoQ10 (Ubiquinol)",
    },
    "atorvastatin": {
        "smiles": "CC(C)C1=C(C(=C(N1CC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",
        "base": 5,  # Spec §8.1: CYP2C9 + CYP3A4 substrate, myopathy risk
        "dose_normal": 10,
        "protective": False,
        "tags": ["CYP2C9_substrate", "CYP3A4_substrate", "myopathy_risk"],
        "display_name": "Atorvastatin (Lipitor)",
    },
    "rosuvastatin": {
        "smiles": "CC(C)C1=NC(=NC(=C1C=CC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)N(C)S(=O)(=O)C",
        "base": 5,  # Spec §8.1
        "dose_normal": 10,
        "protective": False,
        "tags": ["CYP2C9_substrate", "myopathy_risk"],
        "display_name": "Rosuvastatin (Crestor)",
    },
    "sertraline": {
        "smiles": "CN[C@H]1CC[C@@H](C2=CC=CC=C12)C3=CC=C(C=C3Cl)Cl",
        "base": 4,  # Spec §8.1: CYP2D6 + CYP2C19 substrate
        "dose_normal": 50,
        "protective": False,
        "tags": ["CYP2D6_substrate", "CYP2C19_substrate"],
        "display_name": "Sertraline (Zoloft)",
    },
    "escitalopram": {
        "smiles": "CN(C)CCCC1(C2=C(CO1)C=C(C=C2)C#N)C3=CC=C(C=C3)F",
        "base": 4,  # Spec §8.1: CYP2D6 + CYP2C19 substrate
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
# ─────────────────────────────────────────────────────────────────────────────
SUGAR_PENALTIES = [
    (60,   0),    # <60 g/day: healthy range
    (120,  5),    # 60-120 g/day: moderately elevated fructose load (spec: -5 pts)
    (float("inf"), 10),  # >120 g/day: high NAFLD risk (spec: -10 pts, Priya: 140)
]

ALCOHOL_PENALTIES = [
    (7, 0),               # ≤7 units/week: within limit
    (14, 5),              # 7-14 units/week: hepatotoxic threshold (spec: -5 pts)
    (float("inf"), 8),    # >14 units/week: severe load
]

SLEEP_PENALTIES = [
    (5, 4),               # ≤5h: severely impairs hepatic regeneration
    (6, 3),               # 5-6h: impairs hepatic regeneration (spec: -3 pts)
    (float("inf"), 0),    # >6h: no penalty
]

ACTIVITY_PENALTIES = {
    "sedentary": 2,  # Reduced metabolic clearance (spec: -2 pts)
    "light": 0,
    "moderate": 0,
    "intense": 0,
}

# Stress penalty: triggered at ≥8/10 (spec: -2 pts)
STRESS_THRESHOLD = 8
STRESS_PENALTY = 2  # Chronic cortisol elevates liver inflammation markers

# ─────────────────────────────────────────────────────────────────────────────
# Food / Diet Penalty Rules
# Sources: NAFLD meta-analyses, Mediterranean diet RCTs, dietary fiber research
# ─────────────────────────────────────────────────────────────────────────────
CALORIE_PENALTIES = [
    (1800,  0),           # ≤1800 kcal/day: lean/optimal
    (2500,  0),           # 1800-2500 kcal/day: normal range, no penalty
    (3000,  3),           # 2500-3000 kcal/day: elevated caloric load
    (float("inf"), 8),    # >3000 kcal/day: severe hepatic caloric stress
]

PROCESSED_FOOD_PENALTIES = [
    (20,  0),             # ≤20% processed: optimal (whole-food diet)
    (40,  2),             # 20-40%: lightly processed
    (70,  5),             # 40-70%: moderate ultra-processed load
    (float("inf"), 10),   # >70%: high ultra-processed food intake (NAFLD risk)
]

RED_MEAT_PENALTIES = [
    (200,  0),            # ≤200g/week: acceptable
    (500,  3),            # 200-500g/week: elevated heme iron + nitrites
    (float("inf"), 6),    # >500g/week: high red/processed meat hepatic load
]

FIBER_PENALTIES = [
    (15,  3),             # <15g/day: severe deficiency (gut microbiome → liver axis)
    (25,  0),             # 15-25g/day: below target but functional
    (float("inf"), -2),   # ≥25g/day: protective (high fiber diet)
]

# Diet type modifiers — net liver index adjustment (positive = protective)
DIET_TYPE_MODIFIERS: Dict[str, float] = {
    "mediterranean": 3.0,   # Strong evidence: reduces NAFLD, anti-inflammatory
    "vegetarian": 1.5,      # Generally lower saturated fat, higher fiber
    "vegan": 1.0,           # Lower heme iron but may lack B12/omega-3
    "omnivore": 0.0,        # Baseline — no modifier
    "keto": -2.0,           # Elevated saturated fat hepatic processing load
}

DIET_TYPE_REASONS: Dict[str, str] = {
    "mediterranean": "Mediterranean diet provides strong hepatoprotection (olive oil, fish, legumes, high fiber) — reduces NAFLD risk by ~39%.",
    "vegetarian": "Vegetarian diet typically reduces saturated fat intake and hepatic lipid accumulation.",
    "vegan": "Vegan diet lowers heme iron and saturated fat; ensure adequate B12 and omega-3 to avoid nutrient gaps.",
    "omnivore": "Mixed omnivore diet — hepatic load depends on food quality and portion sizes.",
    "keto": "Ketogenic diet increases saturated fat processing through hepatic beta-oxidation and may worsen NAFLD in susceptible individuals.",
}

# Food recommendation triggers and details
FOOD_RECOMMENDATION_RULES: List[Dict] = [
    {
        "id": "reduce_processed_food",
        "trigger": lambda food: food is not None and food.processed_food_pct > 40,
        "action_type": "behavior_change",
        "title": "Reduce Ultra-Processed Food Intake",
        "details": (
            "Ultra-processed foods (>40% of diet) drive hepatic inflammation through advanced glycation "
            "end-products, refined oils, and additive loads. Replacing with whole foods can reduce liver "
            "enzyme elevation (ALT/AST) by 15–30% within 8 weeks."
        ),
        "confidence": 0.88,
        "evidence_refs": ["PMID:33974869", "ToxCast:ultra_processed_NAFLD"],
    },
    {
        "id": "adopt_mediterranean_diet",
        "trigger": lambda food: food is not None and food.diet_type in ("omnivore", "keto") and food.processed_food_pct > 30,
        "action_type": "behavior_change",
        "title": "Shift Toward Mediterranean Diet Pattern",
        "details": (
            "The Mediterranean diet is the most evidence-backed dietary pattern for liver health, "
            "reducing NAFLD prevalence by 39% in meta-analyses. Key shifts: extra-virgin olive oil, "
            "fatty fish 3×/week, legumes, nuts, and vegetables at every meal."
        ),
        "confidence": 0.92,
        "evidence_refs": ["PMID:28723783", "PMID:34543726"],
    },
    {
        "id": "increase_fiber",
        "trigger": lambda food: food is not None and food.fiber_g_per_day < 20,
        "action_type": "behavior_change",
        "title": "Increase Dietary Fiber to ≥25g/day",
        "details": (
            f"Low fiber intake impairs the gut-liver axis by reducing short-chain fatty acid production "
            "and increasing intestinal permeability. Target 25-35g/day (legumes, oats, vegetables) "
            "to reduce hepatic inflammation and improve insulin sensitivity."
        ),
        "confidence": 0.85,
        "evidence_refs": ["PMID:30728226", "PMID:31174214"],
    },
    {
        "id": "reduce_red_meat",
        "trigger": lambda food: food is not None and food.red_meat_g_per_week > 500,
        "action_type": "behavior_change",
        "title": "Reduce Red & Processed Meat to <300g/week",
        "details": (
            "High red meat consumption (>500g/week) increases hepatic heme iron load and generates "
            "nitrosamines during digestion, both of which accelerate hepatocyte stress. "
            "Replacing with fish, poultry, and legumes reduces these risks significantly."
        ),
        "confidence": 0.82,
        "evidence_refs": ["PMID:30064941", "WHO:red_meat_classification"],
    },
]

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
# Recommendation Templates (compound / lifestyle triggers)
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
