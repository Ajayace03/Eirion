from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ─── Organ Scorecard ─────────────────────────────────────────────────────────

class OrganScore(BaseModel):
    organ: Literal["liver", "kidney", "cardiovascular", "metabolic"]
    score: float = Field(description="Current health index 0=very poor → 100=optimal")
    risk_level: Literal["green", "amber", "red"]
    primary_driver: str = Field(description="Top compound or condition driving this score")
    active_pathways: List[str] = Field(default_factory=list)
    projected_5yr: Optional[float] = None


# ─── Compound→Gene Chain ──────────────────────────────────────────────────────

class GeneInteractionDetail(BaseModel):
    gene: str
    phenotype: str
    multiplier: float
    evidence: str = ""


class CompoundGeneChain(BaseModel):
    compound_id: str
    display_name: str
    gene_interactions: List[GeneInteractionDetail] = Field(default_factory=list)
    pathway_chain: List[str] = Field(default_factory=list)
    organ_impacts: Dict[str, float] = Field(default_factory=dict)


# ─── Drug-Drug Interaction Flag ───────────────────────────────────────────────

class DDIFlag(BaseModel):
    compound_a: str
    compound_b: str
    risk_level: Literal["low", "moderate", "high"]
    mechanism: str
    recommendation: str
    evidence: str = ""


# ─── Core Response Building Blocks ───────────────────────────────────────────

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


# ─── Phase 3: Multi-Timeframe Projections ─────────────────────────────────────

class TimeframePoint(BaseModel):
    """Single data point in a multi-timeframe projection."""
    month: int                  # months from now
    label: str                  # human display label e.g. "6m", "1yr"
    score: float                # current-path organ score
    optimized_score: float      # score if all recs adopted
    confidence_band: float      # ±σ band (widens over time)


class OrganTrajectory(BaseModel):
    """Full multi-timeframe trajectory for a single organ."""
    organ: Literal["liver", "kidney", "cardiovascular", "metabolic"]
    current_score: float
    optimized_now: float
    risk_level: Literal["green", "amber", "red"]
    # Full monthly/quarterly/annual point series keyed by timeframe label
    timeframes: Dict[str, List[TimeframePoint]] = Field(default_factory=dict)
    # Summary scalars — score at end of each horizon
    scores_at: Dict[str, float] = Field(default_factory=dict)
    optimized_at: Dict[str, float] = Field(default_factory=dict)
    # Improvement delta (current minus optimized) at each horizon
    improvement_at: Dict[str, float] = Field(default_factory=dict)
    # Guideline-grounded recommendation
    guideline_rec: Optional[str] = None
    guideline_source: Optional[str] = None


class MultiOrganProjection(BaseModel):
    """Phase 3 core output — full multi-timeframe multi-organ projections."""
    liver:          OrganTrajectory
    kidney:         OrganTrajectory
    cardiovascular: OrganTrajectory
    metabolic:      OrganTrajectory
    # Cross-organ summary
    organ_years_gained: Optional[float] = None   # total healthy organ-years gained if recs adopted
    max_gain_organ:     Optional[str] = None
    max_gain_pct:       Optional[float] = None


# ─── Full Analysis Response ──────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    # Core (backwards compatible)
    risk_summary: RiskSummary
    trajectory: List[TrajectoryPoint]
    contributions: List[Contribution]
    recommendations: List[Recommendation]
    biological_age: float
    polypharmacy_score: int

    # Phase 2 — Multi-organ
    organ_scores: List[OrganScore] = Field(default_factory=list)
    compound_gene_chains: List[CompoundGeneChain] = Field(default_factory=list)
    ddi_flags: List[DDIFlag] = Field(default_factory=list)
    active_pathways: List[str] = Field(default_factory=list)
    gnn_version: str = Field(default="rules_v1")

    # Phase 3 — Multi-timeframe projections
    multi_organ_projection: Optional[MultiOrganProjection] = None
