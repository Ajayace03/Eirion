
export const PRIYA_DATA = {
  patient: {
    age: 35,
    sex: "female" as const,
    weight_kg: 62,
    height_cm: 165,
  },
  lifestyle: {
    sugar_g_per_day: 140,
    alcohol_units_per_week: 0,
    sleep_hours_per_night: 6,
    activity_level: "moderate" as const,
    stress_level: 7,
  },
  genetics: {
    cyp2d6_metabolizer: "poor" as const,
    cyp2c19_metabolizer: "unknown" as const,
  },
  regimen: [
    { compound_id: "omega3", dose_mg: 2000, frequency_per_day: 1 },
    { compound_id: "vitamin_d", dose_mg: 5000, frequency_per_day: 1 },
    { compound_id: "ashwagandha", dose_mg: 600, frequency_per_day: 1 },
    { compound_id: "metformin", dose_mg: 500, frequency_per_day: 1 },
  ],
  labs: {
    ast_u_per_l: 20,
    alt_u_per_l: 22,
    bilirubin_mg_per_dl: 0.8,
  },
};
