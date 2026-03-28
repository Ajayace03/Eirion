from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Patient(BaseModel):
    age: int = Field(..., ge=1, le=120, description="Age in years")
    sex: Literal["male", "female", "other"]
    weight_kg: float = Field(..., gt=0)
    height_cm: Optional[float] = None
    ethnicity: Optional[str] = None


class Lifestyle(BaseModel):
    sugar_g_per_day: float = Field(..., ge=0)
    alcohol_units_per_week: float = Field(default=0, ge=0)
    sleep_hours_per_night: float = Field(default=7, ge=0, le=24)
    activity_level: Literal["sedentary", "light", "moderate", "intense"] = "moderate"
    stress_level: float = Field(default=5, ge=1, le=10)


class Genetics(BaseModel):
    cyp2d6_metabolizer: Literal[
        "poor", "intermediate", "normal", "ultra_rapid", "unknown"
    ] = "unknown"
    cyp2c19_metabolizer: Literal[
        "poor", "intermediate", "normal", "ultra_rapid", "unknown"
    ] = "unknown"


class RegimenItem(BaseModel):
    compound_id: str = Field(..., description="Must match a key in LIVER_LOAD_TABLE")
    dose_mg: float = Field(..., gt=0)
    frequency_per_day: float = Field(default=1, gt=0)
    duration_months: Optional[float] = None


class Labs(BaseModel):
    ast_u_per_l: Optional[float] = None
    alt_u_per_l: Optional[float] = None
    bilirubin_mg_per_dl: Optional[float] = None


class AnalysisRequest(BaseModel):
    patient: Patient
    lifestyle: Lifestyle
    genetics: Genetics
    regimen: List[RegimenItem] = Field(..., min_length=1)
    labs: Optional[Labs] = None
