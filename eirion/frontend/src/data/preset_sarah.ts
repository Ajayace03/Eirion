

export const SARAH_DATA = {
  patient: {
    age: 55,
    sex: "female",
    weight_kg: 85,
    height_cm: 162,
    ethnicity: "Caucasian",
  },

  conditions: [
    { condition_id: "hypertension", severity: "moderate", diagnosed: true },
    { condition_id: "insomnia", severity: "severe", diagnosed: true },
    { condition_id: "gerd", severity: "moderate", diagnosed: true }
  ],

  lifestyle: {
    sleep_hours_avg: 4.5,
    sleep_quality: 2,
    stress_level: 9,
    cognitive_load: 9,
    diet_type: "standard_american",
    processed_food_frequency: 8,
    hydration_oz_per_day: 30,
    sugar_g_per_day: 120,
    exercise_mins_per_week: 15,
    resistance_training_days: 0,
    alcohol_drinks_per_week: 14,
    smoking_status: "former",
    environmental_toxin_exposure: 7,
    sunlight_mins_per_day: 5,
    screen_time_hours: 12,
  },

  genetics: {
    cyp2d6_metabolizer: "ultrarapid",
    cyp2c19_metabolizer: "poor",
    source: "manual",
  },

  regimen: [
    {
      compound_id: "lisinopril",
      dose_mg: 20,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "clinician",
      is_rx: true,
      reason_condition_ids: ["hypertension"],
    },
    {
      compound_id: "omeprazole",
      dose_mg: 40,
      frequency_per_day: 1,
      timing: ["morning"],
      prescribed_by: "clinician",
      is_rx: true,
      reason_condition_ids: ["gerd"],
    },
    {
      compound_id: "zolpidem",
      dose_mg: 10,
      frequency_per_day: 1,
      timing: ["evening"],
      prescribed_by: "clinician",
      is_rx: true,
      reason_condition_ids: ["insomnia"],
    }
  ],

  labs: {
    ast_u_per_l: 45,
    alt_u_per_l: 52,
    alp_u_per_l: 110,
    bilirubin_mg_per_dl: 1.1,
    glucose_mg_per_dl: 110,
    hba1c_pct: 6.1,
    hscrp_mg_per_l: 4.2,
    triglycerides_mg_per_dl: 190,
    hdl_mg_per_dl: 40,
    ldl_mg_per_dl: 145,
  },

  food: {}
} as any;
