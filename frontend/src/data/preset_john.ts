

export const JOHN_DATA = {
  patient: {
    age: 42,
    sex: "male",
    weight_kg: 78,
    height_cm: 180,
    ethnicity: "Caucasian",
  },

  conditions: [
    { condition_id: "longevity_optimization", severity: "mild", diagnosed: false }
  ],

  lifestyle: {
    sleep_hours_avg: 7.5,
    sleep_quality: 9,
    stress_level: 3,
    cognitive_load: 6,
    diet_type: "mediterranean",
    processed_food_frequency: 1,
    hydration_oz_per_day: 120,
    sugar_g_per_day: 15,
    exercise_mins_per_week: 300,
    resistance_training_days: 4,
    alcohol_drinks_per_week: 0,
    smoking_status: "never",
    environmental_toxin_exposure: 2,
    sunlight_mins_per_day: 45,
    screen_time_hours: 6,
  },

  genetics: {
    cyp2d6_metabolizer: "normal",
    cyp2c19_metabolizer: "normal",
    mthfr_c677t: "homozygous",
    mthfr_a1298c: "normal",
    source: "23andme_upload",
  },

  regimen: [
    {
      compound_id: "creatine",
      dose_mg: 5000,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: [],
    },
    {
      compound_id: "nmn",
      dose_mg: 1000,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: [],
    },
    {
      compound_id: "methylfolate",
      dose_mg: 1,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: [],
    }
  ],

  labs: {
    ast_u_per_l: 22,
    alt_u_per_l: 25,
    alp_u_per_l: 60,
    bilirubin_mg_per_dl: 0.6,
    albumin_g_per_dl: 4.5,
    glucose_mg_per_dl: 82,
    hba1c_pct: 4.8,
    hscrp_mg_per_l: 0.4,
    triglycerides_mg_per_dl: 70,
    hdl_mg_per_dl: 65,
    ldl_mg_per_dl: 85,
  },

  food: {}
};
