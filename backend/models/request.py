from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Shared type aliases
# ─────────────────────────────────────────────────────────────────────────────

Phenotype = Literal["poor", "intermediate", "normal", "ultra_rapid", "unknown"]
RiskLevel = Literal["green", "amber", "red"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Patient
# ─────────────────────────────────────────────────────────────────────────────

class Patient(BaseModel):
    age: int = Field(..., ge=1, le=120)
    sex: Literal["male", "female", "other"]
    weight_kg: float = Field(..., gt=0)
    height_cm: Optional[float] = None
    ethnicity: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Conditions / Diseases
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_CONDITIONS = [
    "prediabetes", "type2_diabetes", "nafld", "fatty_liver",
    "metabolic_syndrome", "hypertension", "cardiovascular_risk",
    "hyperlipidemia", "hypothyroidism", "hyperthyroidism",
    "anxiety", "depression", "burnout", "sleep_disorder",
    "autoimmune", "inflammatory", "pcos", "hormonal_imbalance",
    "kidney_disease", "cancer_history", "osteoporosis", "gout",
]

class Condition(BaseModel):
    condition_id: str = Field(..., description="e.g. 'prediabetes', 'nafld', 'anxiety'")
    severity: Literal["mild", "moderate", "severe"] = "mild"
    diagnosed: bool = Field(default=False, description="Formally diagnosed vs self-reported")
    onset_year: Optional[int] = None
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Extended Genetics
# ─────────────────────────────────────────────────────────────────────────────

class ExtendedGenetics(BaseModel):
    """Full pharmacogenomics profile — extended from the original 2-gene model."""
    # CYP450 Phase I metabolizers
    cyp2d6_metabolizer: Phenotype = "unknown"
    cyp2c19_metabolizer: Phenotype = "unknown"
    cyp3a4_metabolizer: Phenotype = "unknown"
    cyp2c9_metabolizer: Phenotype = "unknown"
    cyp1a2_metabolizer: Phenotype = "unknown"
    # Transporter variants
    slco1b1_function: Literal["normal", "reduced", "poor", "unknown"] = "unknown"
    ugt1a1_function: Phenotype = "unknown"
    # Folate cycle
    mthfr_c677t: Literal["normal", "heterozygous", "homozygous", "unknown"] = "unknown"
    mthfr_a1298c: Literal["normal", "heterozygous", "homozygous", "unknown"] = "unknown"
    # Raw star-allele diplotypes for display / audit trail
    diplotypes: Dict[str, str] = Field(
        default_factory=dict,
        description="e.g. {'CYP2D6': '*4/*4', 'CYP2C19': '*1/*2'}"
    )
    # Source of genetic data
    source: Literal["manual", "23andme_upload", "pgx_report", "unknown"] = "manual"

# Backwards-compat alias so existing code still works
class Genetics(BaseModel):
    cyp2d6_metabolizer: Phenotype = "unknown"
    cyp2c19_metabolizer: Phenotype = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Lifestyle
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 4. Lifestyle Intake
# ─────────────────────────────────────────────────────────────────────────────

class LifestyleIntake(BaseModel):
    # Sleep & Stress
    sleep_hours_avg: float = Field(default=7.0, ge=0, le=24)
    sleep_quality: int = Field(default=5, ge=1, le=10)
    stress_level: int = Field(default=5, ge=1, le=10)
    cognitive_load: int = Field(default=5, ge=1, le=10)
    
    # Diet & Hydration
    diet_type: Literal["omnivore", "mediterranean", "vegan", "keto", "standard_american"] = "omnivore"
    processed_food_frequency: int = Field(default=5, ge=1, le=10)
    hydration_oz_per_day: int = Field(default=64, ge=0)
    sugar_g_per_day: float = Field(default=50, ge=0)
    
    # Activity
    exercise_mins_per_week: int = Field(default=150, ge=0)
    resistance_training_days: int = Field(default=0, ge=0, le=7)
    
    # Substances
    alcohol_drinks_per_week: int = Field(default=0, ge=0)
    smoking_status: Literal["never", "former", "current"] = "never"
    
    # Environment
    environmental_toxin_exposure: int = Field(default=5, ge=1, le=10)
    sunlight_mins_per_day: int = Field(default=20, ge=0, le=500)
    screen_time_hours: float = Field(default=6.0, ge=0, le=24)



# ─────────────────────────────────────────────────────────────────────────────
# 5. Food / Diet
# ─────────────────────────────────────────────────────────────────────────────

class Food(BaseModel):
    calories_per_day: Optional[float] = Field(default=None, ge=0, le=10000)
    processed_food_pct: Optional[float] = Field(default=None, ge=0, le=100)
    red_meat_g_per_week: Optional[float] = Field(default=None, ge=0)
    fiber_g_per_day: Optional[float] = Field(default=None, ge=0)
    diet_type: Optional[Literal["omnivore", "vegetarian", "vegan", "keto", "mediterranean"]] = None


# ─────────────────────────────────────────────────────────────────────────────
# 6. Detailed Regimen Item
# ─────────────────────────────────────────────────────────────────────────────

class RegimenItem(BaseModel):
    """Detailed supplement/medication entry — includes why, when, how long."""
    compound_id: str = Field(..., description="Must match a key in LIVER_LOAD_TABLE")
    dose_mg: float = Field(..., gt=0)
    frequency_per_day: float = Field(default=1, gt=0)
    duration_months: Optional[float] = None

    # Enhanced fields (Phase 1)
    timing: List[Literal["morning", "afternoon", "evening", "with_food", "before_sleep"]] = Field(
        default_factory=list,
        description="When in the day this is taken"
    )
    prescribed_by: Literal["self", "gp", "specialist", "online"] = "self"
    is_rx: bool = Field(default=False, description="Prescription drug (Rx) vs OTC supplement")
    reason_condition_ids: List[str] = Field(
        default_factory=list,
        description="Which conditions this compound is taken for"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="When they started taking this — 'YYYY-MM' format"
    )
    brand_name: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 7. Extended Labs
# ─────────────────────────────────────────────────────────────────────────────

class Labs(BaseModel):
    """Extended lab panel — LFT + KFT + Metabolic/Cardiac markers."""
    # Liver Function Tests (LFT) — originally just 3
    ast_u_per_l: Optional[float] = None
    alt_u_per_l: Optional[float] = None
    ggt_u_per_l: Optional[float] = None
    alp_u_per_l: Optional[float] = None
    albumin_g_per_dl: Optional[float] = None
    bilirubin_mg_per_dl: Optional[float] = None

    # Kidney Function Tests (KFT)
    creatinine_mg_per_dl: Optional[float] = None
    egfr_ml_per_min: Optional[float] = None
    bun_mg_per_dl: Optional[float] = None
    uric_acid_mg_per_dl: Optional[float] = None

    # Metabolic / Cardiac panel
    hba1c_pct: Optional[float] = None
    glucose_mg_per_dl: Optional[float] = None
    ldl_mg_per_dl: Optional[float] = None
    hdl_mg_per_dl: Optional[float] = None
    triglycerides_mg_per_dl: Optional[float] = None
    hscrp_mg_per_l: Optional[float] = None

    # Metadata
    lab_report_date: Optional[str] = None   # "YYYY-MM-DD"
    lab_name: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 8. Root Request
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    patient: Patient
    conditions: List[Condition] = Field(default_factory=list)
    lifestyle: LifestyleIntake
    genetics: ExtendedGenetics = Field(default_factory=ExtendedGenetics)
    regimen: List[RegimenItem] = Field(..., min_length=1)
    labs: Optional[Labs] = None
    food: Optional[Food] = None

