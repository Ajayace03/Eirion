// Shared interfaces mirroring the backend Pydantic models

export type Phenotype = "poor" | "intermediate" | "normal" | "ultra_rapid" | "unknown";
export type FunctionLevel = "normal" | "reduced" | "poor" | "unknown";
export type MthfrStatus = "normal" | "heterozygous" | "homozygous" | "unknown";

// ─── Patient ─────────────────────────────────────────────────────────────────
export interface Patient {
  age: number;
  sex: "male" | "female" | "other";
  weight_kg: number;
  height_cm?: number;
  ethnicity?: string;
}

// ─── Condition ───────────────────────────────────────────────────────────────
export interface Condition {
  condition_id: string;
  severity: "mild" | "moderate" | "severe";
  diagnosed: boolean;
  onset_year?: number;
  notes?: string;
}

// ─── Lifestyle ───────────────────────────────────────────────────────────────
export interface LifestyleIntake {
  // Sleep & Stress
  sleep_hours_avg: number;
  sleep_quality: number;
  stress_level: number;
  cognitive_load: number;
  
  // Diet & Hydration
  diet_type: "omnivore" | "mediterranean" | "vegan" | "keto" | "standard_american";
  processed_food_frequency: number;
  hydration_oz_per_day: number;
  sugar_g_per_day: number;
  
  // Activity
  exercise_mins_per_week: number;
  resistance_training_days: number;
  
  // Substances
  alcohol_drinks_per_week: number;
  smoking_status: "never" | "former" | "current";
  
  // Environment
  environmental_toxin_exposure: number;
  sunlight_mins_per_day: number;
  screen_time_hours: number;
}

// ─── Food ────────────────────────────────────────────────────────────────────
export interface Food {
  calories_per_day?: number;
  processed_food_pct?: number;
  red_meat_g_per_week?: number;
  fiber_g_per_day?: number;
  diet_type?: "omnivore" | "vegetarian" | "vegan" | "keto" | "mediterranean";
}

// ─── Extended Genetics ───────────────────────────────────────────────────────
export interface Genetics {
  cyp2d6_metabolizer: Phenotype;
  cyp2c19_metabolizer: Phenotype;
  cyp3a4_metabolizer?: Phenotype;
  cyp2c9_metabolizer?: Phenotype;
  cyp1a2_metabolizer?: Phenotype;
  slco1b1_function?: FunctionLevel;
  ugt1a1_function?: Phenotype;
  mthfr_c677t?: MthfrStatus;
  mthfr_a1298c?: MthfrStatus;
  diplotypes?: Record<string, string>;
  source?: "manual" | "23andme_upload" | "pgx_report" | "unknown";
}

// ─── Detailed Regimen Item ───────────────────────────────────────────────────
export interface RegimenItem {
  compound_id: string;
  dose_mg: number;
  frequency_per_day: number;
  duration_months?: number;
  // Enhanced fields
  timing?: Array<"morning" | "afternoon" | "evening" | "with_food" | "before_sleep">;
  prescribed_by?: "self" | "gp" | "specialist" | "online";
  is_rx?: boolean;
  reason_condition_ids?: string[];
  start_date?: string;  // "YYYY-MM"
  brand_name?: string;
}

// ─── Extended Labs ───────────────────────────────────────────────────────────
export interface Labs {
  // LFT
  ast_u_per_l?: number;
  alt_u_per_l?: number;
  ggt_u_per_l?: number;
  alp_u_per_l?: number;
  albumin_g_per_dl?: number;
  bilirubin_mg_per_dl?: number;
  // KFT
  creatinine_mg_per_dl?: number;
  egfr_ml_per_min?: number;
  bun_mg_per_dl?: number;
  uric_acid_mg_per_dl?: number;
  // Metabolic / Cardiac
  hba1c_pct?: number;
  glucose_mg_per_dl?: number;
  ldl_mg_per_dl?: number;
  hdl_mg_per_dl?: number;
  triglycerides_mg_per_dl?: number;
  hscrp_mg_per_l?: number;
  // Metadata
  lab_report_date?: string;
  lab_name?: string;
}

// ─── Analysis Request ────────────────────────────────────────────────────────
export interface AnalysisRequest {
  patient: Patient;
  conditions?: Condition[];
  lifestyle: LifestyleIntake;
  genetics: Genetics;
  regimen: RegimenItem[];
  labs?: Labs;
  food?: Food;
}

// ─── Response Models ─────────────────────────────────────────────────────────
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
  // Phase 2 multi-organ
  organ_scores?: OrganScore[];
  compound_gene_chains?: CompoundGeneChain[];
  ddi_flags?: DDIFlag[];
  active_pathways?: string[];
  gnn_version?: string;
  multi_organ_projection?: MultiOrganProjection;
}

// ─── Phase 2 Types ─────────────────────────────────────────────────────────

export interface OrganScore {
  organ: "liver" | "kidney" | "cardiovascular" | "metabolic";
  score: number;
  risk_level: "green" | "amber" | "red";
  primary_driver: string;
  active_pathways: string[];
  projected_5yr?: number;
}

export interface GeneInteractionDetail {
  gene: string;
  phenotype: string;
  multiplier: number;
  evidence: string;
}

export interface CompoundGeneChain {
  compound_id: string;
  display_name: string;
  gene_interactions: GeneInteractionDetail[];
  pathway_chain: string[];
  organ_impacts: Record<string, number>;
}

export interface DDIFlag {
  compound_a: string;
  compound_b: string;
  risk_level: "low" | "moderate" | "high";
  mechanism: string;
  recommendation: string;
  evidence: string;
}

// ─── Phase 3: Multi-Timeframe Projection Types ────────────────────────────────

export interface TimeframePoint {
  month: number;
  label: string;
  score: number;
  optimized_score: number;
  confidence_band: number;
}

export interface OrganTrajectory {
  organ: "liver" | "kidney" | "cardiovascular" | "metabolic";
  current_score: number;
  optimized_now: number;
  risk_level: "green" | "amber" | "red";
  timeframes: Record<string, TimeframePoint[]>;
  scores_at: Record<string, number>;
  optimized_at: Record<string, number>;
  improvement_at: Record<string, number>;
  guideline_rec?: string;
  guideline_source?: string;
}

export interface MultiOrganProjection {
  liver: OrganTrajectory;
  kidney: OrganTrajectory;
  cardiovascular: OrganTrajectory;
  metabolic: OrganTrajectory;
  organ_years_gained?: number;
  max_gain_organ?: string;
  max_gain_pct?: number;
}
