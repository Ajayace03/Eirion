import { create } from "zustand";
import { Patient, LifestyleIntake, Genetics, RegimenItem, Labs, Food, Condition, AnalysisResponse } from "../types";
import { PRIYA_DATA } from "../data/priya";

export interface WizardState {
  step: number;
  patient: Partial<Patient>;
  conditions: Condition[];
  lifestyle: Partial<LifestyleIntake>;
  genetics: Partial<Genetics>;
  regimen: RegimenItem[];
  labs: Partial<Labs>;
  food: Partial<Food>;
  analysisResult: AnalysisResponse | null;
  adoptedRecs: Set<string>;

  setStep: (step: number) => void;
  updatePatient: (data: Partial<Patient>) => void;
  // Conditions
  addCondition: (c: Condition) => void;
  removeCondition: (condition_id: string) => void;
  updateCondition: (condition_id: string, data: Partial<Condition>) => void;
  // Genetics, lifestyle, food, labs
  updateLifestyle: (data: Partial<LifestyleIntake>) => void;
  updateGenetics: (data: Partial<Genetics>) => void;
  updateFood: (data: Partial<Food>) => void;
  updateLabs: (data: Partial<Labs>) => void;
  // Regimen
  addCompound: (item: RegimenItem) => void;
  removeCompound: (compound_id: string) => void;
  updateCompound: (compound_id: string, dose_mg: number) => void;
  updateRegimenItem: (compound_id: string, data: Partial<RegimenItem>) => void;
  // Result & lifecycle
  setResult: (result: AnalysisResponse) => void;
  clearResult: () => void;
  toggleAdoptRec: (id: string) => void;
  loadPriyaExample: () => void;
  loadPreset: (data: any) => void;
  resetWizard: () => void;
}

const initialState = {
  step: 1,
  patient: {},
  conditions: [] as Condition[],
  lifestyle: {
    sleep_hours_avg: 7.0,
    sleep_quality: 5,
    stress_level: 5,
    cognitive_load: 5,
    diet_type: "omnivore" as const,
    processed_food_frequency: 5,
    hydration_oz_per_day: 64,
    sugar_g_per_day: 50,
    exercise_mins_per_week: 150,
    resistance_training_days: 0,
    alcohol_drinks_per_week: 0,
    smoking_status: "never" as const,
    environmental_toxin_exposure: 5,
    sunlight_mins_per_day: 20,
    screen_time_hours: 6.0,
  },
  genetics: {
    cyp2d6_metabolizer: "unknown" as const,
    cyp2c19_metabolizer: "unknown" as const,
    cyp3a4_metabolizer: "unknown" as const,
    cyp2c9_metabolizer: "unknown" as const,
    cyp1a2_metabolizer: "unknown" as const,
    slco1b1_function: "unknown" as const,
    ugt1a1_function: "unknown" as const,
    mthfr_c677t: "unknown" as const,
    mthfr_a1298c: "unknown" as const,
    diplotypes: {} as Record<string, string>,
    source: "manual" as const,
  },
  food: {
    calories_per_day: 2000,
    processed_food_pct: 25,
    red_meat_g_per_week: 150,
    fiber_g_per_day: 20,
    diet_type: "omnivore" as const,
  },
  regimen: [] as RegimenItem[],
  labs: {} as Partial<Labs>,
  analysisResult: null as AnalysisResponse | null,
  adoptedRecs: new Set<string>(),
};

export const useWizardStore = create<WizardState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),

  updatePatient: (data) =>
    set((state) => ({ patient: { ...state.patient, ...data } })),

  // ── Conditions ──────────────────────────────────────────────────────────
  addCondition: (c) =>
    set((state) => {
      if (state.conditions.find((x) => x.condition_id === c.condition_id)) return state;
      return { conditions: [...state.conditions, c] };
    }),

  removeCondition: (condition_id) =>
    set((state) => ({
      conditions: state.conditions.filter((c) => c.condition_id !== condition_id),
    })),

  updateCondition: (condition_id, data) =>
    set((state) => ({
      conditions: state.conditions.map((c) =>
        c.condition_id === condition_id ? { ...c, ...data } : c
      ),
    })),

  // ── Lifestyle / Food / Labs / Genetics ──────────────────────────────────
  updateLifestyle: (data) =>
    set((state) => ({ lifestyle: { ...state.lifestyle, ...data } })),

  updateGenetics: (data) =>
    set((state) => ({ genetics: { ...state.genetics, ...data } })),

  updateFood: (data) =>
    set((state) => ({ food: { ...state.food, ...data } })),

  updateLabs: (data) =>
    set((state) => ({ labs: { ...state.labs, ...data } })),

  // ── Regimen ─────────────────────────────────────────────────────────────
  addCompound: (item) =>
    set((state) => {
      if (state.regimen.find((r) => r.compound_id === item.compound_id)) return state;
      return { regimen: [...state.regimen, item] };
    }),

  removeCompound: (compound_id) =>
    set((state) => ({
      regimen: state.regimen.filter((r) => r.compound_id !== compound_id),
    })),

  updateCompound: (compound_id, dose_mg) =>
    set((state) => ({
      regimen: state.regimen.map((r) =>
        r.compound_id === compound_id ? { ...r, dose_mg } : r
      ),
    })),

  updateRegimenItem: (compound_id, data) =>
    set((state) => ({
      regimen: state.regimen.map((r) =>
        r.compound_id === compound_id ? { ...r, ...data } : r
      ),
    })),

  // ── Results ─────────────────────────────────────────────────────────────
  setResult: (result) => set({ analysisResult: result }),
  clearResult: () => set({ analysisResult: null }),

  toggleAdoptRec: (id) =>
    set((state) => {
      const next = new Set(state.adoptedRecs);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { adoptedRecs: next };
    }),

  loadPriyaExample: () =>
    set({
      ...PRIYA_DATA,
      analysisResult: null,
    }),

  loadPreset: (data) =>
    set({
      ...data,
      step: 9,
      analysisResult: null,
    }),

  resetWizard: () => set({ ...initialState, adoptedRecs: new Set<string>() }),
}));
