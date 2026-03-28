from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    risk_level: Literal["green", "amber", "red"]
    liver_index_now: float
    projected_drop_percent: float
    headline: str


class TrajectoryPoint(BaseModel):
    year: int
    liver_index: float
    optimized_liver_index: Optional[float] = None


class Contribution(BaseModel):
    compound_id: str
    name: str
    load: float
    reason: str
    is_protective: bool = False


class ExpectedImprovement(BaseModel):
    delta_index_now: float
    delta_index_year5: float


class Recommendation(BaseModel):
    id: str
    action_type: Literal["swap", "reduce", "add", "behavior_change", "consult"]
    title: str
    details: str
    expected_improvement: ExpectedImprovement
    confidence: float = Field(default=0.85)
    evidence_refs: List[str] = []


class AnalysisResponse(BaseModel):
    risk_summary: RiskSummary
    trajectory: List[TrajectoryPoint]
    contributions: List[Contribution]
    recommendations: List[Recommendation]
    biological_age: float
    polypharmacy_score: int


