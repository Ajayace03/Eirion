import { useState } from "react";
import { useWizardStore } from "../../store/wizardStore";
import { runAnalysis } from "../../api/analysis";
import { useNavigate } from "react-router-dom";
import { Loader2, Zap, Utensils, Dna, Activity, Pill } from "lucide-react";
import { AnalysisRequest } from "../../types";

export default function Step6Confirm() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const store = useWizardStore();
  const navigate = useNavigate();

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setError("");

    const payload: AnalysisRequest = {
      patient: store.patient as any,
      conditions: store.conditions,
      lifestyle: store.lifestyle as any,
      genetics: store.genetics as any,
      regimen: store.regimen,
      labs: Object.keys(store.labs).length > 0 ? store.labs : undefined,
      food: store.food as any,
    };

    try {
      const result = await runAnalysis(payload);
      store.setResult(result);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to run analysis — check backend connection");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const diet = store.food?.diet_type ?? "omnivore";
  const dietIcon: Record<string, string> = {
    omnivore: "🥩",
    vegetarian: "🥗",
    vegan: "🌱",
    keto: "🥑",
    mediterranean: "🫒",
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Ready for Analysis
        </h2>
        <p className="text-blue-gray-600">
          All inputs captured. The compute engine will generate your organ health
          trajectory and personalized protocols.
        </p>
      </div>

      {/* Summary Card */}
      <div className="bg-white border text-left border-blue-gray-100 rounded-2xl shadow-sm p-6 max-w-xl mx-auto divide-y divide-blue-gray-50">
        <div className="py-3 flex justify-between items-center gap-2">
          <span className="flex items-center gap-2 text-blue-gray-500 font-medium">
            <Pill className="w-4 h-4" />
            Compounds In Stack
          </span>
          <span className="font-bold text-blue-gray-900">{store.regimen.length} active</span>
        </div>
        <div className="py-3 flex justify-between items-center gap-2">
          <span className="flex items-center gap-2 text-blue-gray-500 font-medium">
            <Dna className="w-4 h-4" />
            Pharmacogenomics
          </span>
          <span className="font-bold text-blue-gray-900">
            CYP2D6:{" "}
            {store.genetics.cyp2d6_metabolizer === "unknown"
              ? "Population Avg"
              : store.genetics.cyp2d6_metabolizer}
          </span>
        </div>
        <div className="py-3 flex justify-between items-center gap-2">
          <span className="flex items-center gap-2 text-blue-gray-500 font-medium">
            <Activity className="w-4 h-4" />
            Age & Sex
          </span>
          <span className="font-bold text-blue-gray-900">
            {store.patient.age}y / {store.patient.sex}
          </span>
        </div>
        <div className="py-3 flex justify-between items-center gap-2">
          <span className="flex items-center gap-2 text-blue-gray-500 font-medium">
            <Utensils className="w-4 h-4" />
            Diet Pattern
          </span>
          <span className="font-bold text-blue-gray-900 capitalize">
            {dietIcon[diet]} {diet}
            {store.food?.calories_per_day
              ? ` · ${store.food.calories_per_day.toLocaleString()} kcal`
              : ""}
          </span>
        </div>
        <div className="py-3 flex justify-between items-center gap-2">
          <span className="text-blue-gray-500 font-medium">Sugar / Alcohol</span>
          <span className="font-bold text-blue-gray-900">
            {store.lifestyle.sugar_g_per_day}g /{" "}
            {store.lifestyle.alcohol_drinks_per_week} drinks/wk
          </span>
        </div>
      </div>

      {error && (
        <div className="max-w-xl mx-auto p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
          {error}
        </div>
      )}

      <div className="flex justify-center pt-8">
        <button
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="group relative px-10 py-5 bg-gradient-to-r from-blue-gray-900 to-black text-white rounded-2xl font-bold shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all flex items-center justify-center gap-3 overflow-hidden text-lg min-w-[300px]"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin relative z-10" />
              <span className="relative z-10">Analysing your stack…</span>
            </>
          ) : (
            <>
              <Zap className="w-6 h-6 relative z-10 text-brand-amber group-hover:scale-110 transition-transform" />
              <span className="relative z-10">Generate Blueprint</span>
            </>
          )}
          <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
        </button>
      </div>
    </div>
  );
}
