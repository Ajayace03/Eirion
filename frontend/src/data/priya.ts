// Priya Sharma — canonical demo profile (v2)
// 35F · Mumbai · Software Engineer · Poor CYP2D6 · Prediabetic

import { Patient, LifestyleIntake, Genetics, RegimenItem, Labs, Food, Condition } from "../types";

interface PriyaData {
  patient: Partial<Patient>;
  conditions: Condition[];
  lifestyle: Partial<LifestyleIntake>;
  genetics: Partial<Genetics>;
  regimen: RegimenItem[];
  labs: Partial<Labs>;
  food: Partial<Food>;
}

export const PRIYA_DATA: PriyaData = {
  patient: {
    age: 35,
    sex: "female",
    weight_kg: 62,
    height_cm: 165,
    ethnicity: "South Asian",
  },

  conditions: [
    { condition_id: "prediabetes", severity: "mild", diagnosed: true, onset_year: 2023 },
    { condition_id: "anxiety", severity: "moderate", diagnosed: false },
    { condition_id: "hyperlipidemia", severity: "mild", diagnosed: true, onset_year: 2023 },
  ],

  lifestyle: {
    sleep_hours_avg: 6.0,
    sleep_quality: 4,
    stress_level: 7,
    cognitive_load: 8,
    diet_type: "omnivore",
    processed_food_frequency: 7,
    hydration_oz_per_day: 40,
    sugar_g_per_day: 140,
    exercise_mins_per_week: 45,
    resistance_training_days: 0,
    alcohol_drinks_per_week: 2,
    smoking_status: "never",
    environmental_toxin_exposure: 6,
    sunlight_mins_per_day: 10,
    screen_time_hours: 10,
  },

  genetics: {
    cyp2d6_metabolizer: "poor",
    cyp2c19_metabolizer: "intermediate",
    cyp3a4_metabolizer: "normal",
    cyp2c9_metabolizer: "normal",
    cyp1a2_metabolizer: "normal",
    slco1b1_function: "normal",
    ugt1a1_function: "unknown",
    mthfr_c677t: "heterozygous",
    mthfr_a1298c: "normal",
    diplotypes: {
      CYP2D6: "*4/*4",
      CYP2C19: "*1/*2",
    },
    source: "23andme_upload",
  },

  regimen: [
    {
      compound_id: "omega3",
      dose_mg: 2000,
      frequency_per_day: 1,
      timing: ["with_food"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: ["cardiovascular_risk"],
      start_date: "2022-03",
    },
    {
      compound_id: "vitamin_d",
      dose_mg: 5000,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: ["general_health"],
      start_date: "2023-01",
    },
    {
      compound_id: "ashwagandha",
      dose_mg: 600,
      frequency_per_day: 1,
      timing: ["evening"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: ["anxiety"],
      start_date: "2024-03",
    },
    {
      compound_id: "metformin",
      dose_mg: 500,
      frequency_per_day: 2,
      timing: ["morning", "evening"],
      prescribed_by: "gp",
      is_rx: true,
      reason_condition_ids: ["prediabetes"],
      start_date: "2023-06",
    },
  ],

  labs: {
    ast_u_per_l: 20,
    alt_u_per_l: 22,
    ggt_u_per_l: 28,
    bilirubin_mg_per_dl: 0.8,
    creatinine_mg_per_dl: 0.85,
    egfr_ml_per_min: 92,
    hba1c_pct: 5.9,
    glucose_mg_per_dl: 108,
    ldl_mg_per_dl: 142,
    hdl_mg_per_dl: 48,
    triglycerides_mg_per_dl: 189,
    hscrp_mg_per_l: 2.8,
    lab_report_date: "2025-01-10",
    lab_name: "Thyrocare",
  },

  food: {
    calories_per_day: 2200,
    processed_food_pct: 45,
    red_meat_g_per_week: 200,
    fiber_g_per_day: 18,
    diet_type: "omnivore",
  },
};
