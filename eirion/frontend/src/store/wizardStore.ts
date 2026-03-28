import { create } from "zustand";
import { Patient, Lifestyle, Genetics, RegimenItem, Labs, AnalysisResponse } from "../types";
import { PRIYA_DATA } from "../data/priya";

export interface WizardState {
  step: number;
  patient: Partial<Patient>;
  lifestyle: Partial<Lifestyle>;
  genetics: Partial<Genetics>;
  regimen: RegimenItem[];
  labs: Partial<Labs>;
  analysisResult: AnalysisResponse | null;

  setStep: (step: number) => void;
  updatePatient: (data: Partial<Patient>) => void;
  updateLifestyle: (data: Partial<Lifestyle>) => void;
  updateGenetics: (data: Partial<Genetics>) => void;
  addCompound: (item: RegimenItem) => void;
  removeCompound: (compound_id: string) => void;
  updateCompound: (compound_id: string, dose_mg: number) => void;
  updateLabs: (data: Partial<Labs>) => void;
  setResult: (result: AnalysisResponse) => void;
  clearResult: () => void;
  loadPriyaExample: () => void;
  resetWizard: () => void;
  // Adopt/Skip toggle for recommendations
  adoptedRecs: Set<string>;
  toggleAdoptRec: (id: string) => void;
}

const initialState = {
  step: 1,
  patient: {},
  lifestyle: {
    sugar_g_per_day: 50,
    alcohol_units_per_week: 0,
    sleep_hours_per_night: 7,
    activity_level: "moderate" as const,
    stress_level: 5,
  },
  genetics: {
    cyp2d6_metabolizer: "unknown" as const,
    cyp2c19_metabolizer: "unknown" as const,
  },
  regimen: [],
  labs: {},
  analysisResult: null,
  adoptedRecs: new Set<string>(),
};

export const useWizardStore = create<WizardState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),

  updatePatient: (data) =>
    set((state) => ({ patient: { ...state.patient, ...data } })),

  updateLifestyle: (data) =>
    set((state) => ({ lifestyle: { ...state.lifestyle, ...data } })),

  updateGenetics: (data) =>
    set((state) => ({ genetics: { ...state.genetics, ...data } })),

  addCompound: (item) =>
    set((state) => {
      if (state.regimen.find((r) => r.compound_id === item.compound_id)) {
        return state;
      }
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

  updateLabs: (data) => set((state) => ({ labs: { ...state.labs, ...data } })),

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
      step: 6, // jump straight to confirm step
      analysisResult: null,
    }),

  resetWizard: () => set(initialState),
}));
