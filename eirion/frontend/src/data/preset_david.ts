

export const DAVID_DATA = {
  patient: {
    age: 60,
    sex: "male",
    weight_kg: 95,
    height_cm: 175,
    ethnicity: "African American",
  },

  conditions: [
    { condition_id: "hyperlipidemia", severity: "moderate", diagnosed: true },
    { condition_id: "osteoarthritis", severity: "mild", diagnosed: true }
  ],

  lifestyle: {
    sleep_hours_avg: 6.5,
    sleep_quality: 5,
    stress_level: 5,
    cognitive_load: 4,
    diet_type: "standard_american",
    processed_food_frequency: 6,
    hydration_oz_per_day: 50,
    sugar_g_per_day: 85,
    exercise_mins_per_week: 60,
    resistance_training_days: 0,
    alcohol_drinks_per_week: 5,
    smoking_status: "never",
    environmental_toxin_exposure: 4,
    sunlight_mins_per_day: 20,
    screen_time_hours: 8,
  },

  genetics: {
    cyp2d6_metabolizer: "normal",
    cyp3a4_metabolizer: "poor",
    slco1b1_function: "poor",
    source: "manual",
  },

  regimen: [
    {
      compound_id: "atorvastatin",
      dose_mg: 40,
      frequency_per_day: 1,
      timing: ["evening"],
      prescribed_by: "clinician",
      is_rx: true,
      reason_condition_ids: ["hyperlipidemia"],
    },
    {
      compound_id: "ibuprofen",
      dose_mg: 400,
      frequency_per_day: 2,
      timing: ["morning", "evening"],
      prescribed_by: "self",
      is_rx: false,
      reason_condition_ids: ["osteoarthritis"],
    }
  ],

  labs: {
    ast_u_per_l: 35,
    alt_u_per_l: 42,
    alp_u_per_l: 85,
    bilirubin_mg_per_dl: 0.8,
    glucose_mg_per_dl: 98,
    hba1c_pct: 5.6,
    triglycerides_mg_per_dl: 150,
    hdl_mg_per_dl: 45,
    ldl_mg_per_dl: 110,
  },

  food: {}
} as any;
