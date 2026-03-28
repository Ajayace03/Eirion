// Shared interfaces mirroring the backend Pydantic models

export interface Patient {
  age: number;
  sex: "male" | "female" | "other";
  weight_kg: number;
  height_cm?: number;
  ethnicity?: string;
}

export interface Lifestyle {
  sugar_g_per_day: number;
  alcohol_units_per_week: number;
  sleep_hours_per_night: number;
  activity_level: "sedentary" | "light" | "moderate" | "intense";
  stress_level: number;
}

export interface Genetics {
  cyp2d6_metabolizer: "poor" | "intermediate" | "normal" | "ultra_rapid" | "unknown";
  cyp2c19_metabolizer: "poor" | "intermediate" | "normal" | "ultra_rapid" | "unknown";
}

export interface RegimenItem {
  compound_id: string;
  dose_mg: number;
  frequency_per_day: number;
  duration_months?: number;
}

export interface Labs {
  ast_u_per_l?: number;
  alt_u_per_l?: number;
  bilirubin_mg_per_dl?: number;
}

export interface AnalysisRequest {
  patient: Patient;
  lifestyle: Lifestyle;
  genetics: Genetics;
  regimen: RegimenItem[];
  labs?: Labs;
}

// -------------------------------------------------------------
// Response Models

export interface RiskSummary {
  risk_level: "green" | "amber" | "red";
  liver_index_now: number;
  projected_drop_percent: number;
  headline: string;
}

export interface TrajectoryPoint {
  year: number;
  liver_index: number;
  optimized_liver_index: number | null;
}

export interface Contribution {
  compound_id: string;
  name: string;
  load: number;
  reason: string;
  is_protective: boolean;
}

export interface ExpectedImprovement {
  delta_index_now: number;
  delta_index_year5: number;
}

export interface Recommendation {
  id: string;
  action_type: "swap" | "reduce" | "add" | "behavior_change" | "consult";
  title: string;
  details: string;
  expected_improvement: ExpectedImprovement;
  confidence: number;
  evidence_refs: string[];
}

export interface AnalysisResponse {
  risk_summary: RiskSummary;
  trajectory: TrajectoryPoint[];
  contributions: Contribution[];
  recommendations: Recommendation[];
  biological_age: number;
  polypharmacy_score: number;
}
