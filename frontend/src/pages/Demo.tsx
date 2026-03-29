import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useWizardStore } from "../store/wizardStore";
import { runAnalysis } from "../api/analysis";
import { AnalysisRequest } from "../types";
import { PRIYA_DATA } from "../data/priya";
import { JOHN_DATA } from "../data/preset_john";
import { SARAH_DATA } from "../data/preset_sarah";
import { DAVID_DATA } from "../data/preset_david";
import {
  Loader2, Zap, RotateCcw, Dna, User, Leaf,
  Utensils, Pill, FlaskConical, AlertTriangle, ChevronDown, ChevronUp,
} from "lucide-react";

const AVAILABLE_COMPOUNDS = [
  { id: "ashwagandha", name: "Ashwagandha", defaultDose: 300 },
  { id: "metformin", name: "Metformin", defaultDose: 500 },
  { id: "omega3", name: "Omega-3 Fish Oil", defaultDose: 2000 },
  { id: "vitamin_d", name: "Vitamin D3", defaultDose: 2000 },
  { id: "nac", name: "NAC (N-Acetyl Cysteine)", defaultDose: 600 },
  { id: "magnesium", name: "Magnesium Glycinate", defaultDose: 400 },
  { id: "zinc", name: "Zinc", defaultDose: 15 },
  { id: "quercetin", name: "Quercetin", defaultDose: 500 },
  { id: "berberine", name: "Berberine", defaultDose: 500 },
  { id: "curcumin", name: "Curcumin / Turmeric", defaultDose: 500 },
  { id: "coq10", name: "CoQ10 (Ubiquinol)", defaultDose: 200 },
  { id: "atorvastatin", name: "Atorvastatin (Lipitor)", defaultDose: 10 },
  { id: "rosuvastatin", name: "Rosuvastatin (Crestor)", defaultDose: 10 },
  { id: "sertraline", name: "Sertraline (Zoloft)", defaultDose: 50 },
  { id: "escitalopram", name: "Escitalopram (Lexapro)", defaultDose: 10 },
];

const DIET_TYPES = [
  { id: "omnivore", icon: "🥩", label: "Omnivore" },
  { id: "vegetarian", icon: "🥗", label: "Vegetarian" },
  { id: "vegan", icon: "🌱", label: "Vegan" },
  { id: "keto", icon: "🥑", label: "Keto" },
  { id: "mediterranean", icon: "🫒", label: "Mediterranean" },
] as const;

const CYP2D6_SUBSTRATES = new Set(["ashwagandha", "berberine", "sertraline", "escitalopram"]);

function SectionCard({
  title, icon, summary, children,
}: {
  title: string;
  icon: React.ReactNode;
  summary?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-blue-gray-50/60 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-gray-900/5 flex items-center justify-center text-blue-gray-700">
            {icon}
          </div>
          <div className="text-left">
            <p className="text-sm font-bold text-blue-gray-900">{title}</p>
            {summary && <p className="text-xs text-blue-gray-500 mt-0.5">{summary}</p>}
          </div>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-blue-gray-400" /> : <ChevronDown className="w-4 h-4 text-blue-gray-400" />}
      </button>
      {open && <div className="px-6 pb-6 pt-2 border-t border-blue-gray-50">{children}</div>}
    </div>
  );
}

export default function Demo() {
  const navigate = useNavigate();
  const store = useWizardStore();
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [addCompoundId, setAddCompoundId] = useState("");
  const [preset, setPreset] = useState("priya");

  // Pre-fill data on mount or preset change
  useEffect(() => {
    handleLoadPreset(preset);
  }, [preset]);

  const handleLoadPreset = (key: string) => {
    if (key === "priya") store.loadPreset(PRIYA_DATA);
    else if (key === "john") store.loadPreset(JOHN_DATA);
    else if (key === "sarah") store.loadPreset(SARAH_DATA);
    else if (key === "david") store.loadPreset(DAVID_DATA);
  };

  const handleReset = () => handleLoadPreset(preset);

  const handleRun = async () => {
    setIsRunning(true);
    setError("");
    const payload: AnalysisRequest = {
      patient: store.patient as any,
      lifestyle: store.lifestyle as any,
      genetics: store.genetics as any,
      regimen: store.regimen,
      labs: store.labs,
      food: store.food as any,
    };
    try {
      const result = await runAnalysis(payload);
      store.setResult(result);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Analysis failed — is the backend running?");
    } finally {
      setIsRunning(false);
    }
  };

  const handleAddCompound = () => {
    if (!addCompoundId) return;
    const c = AVAILABLE_COMPOUNDS.find((x) => x.id === addCompoundId);
    if (c) store.addCompound({ compound_id: c.id, dose_mg: c.defaultDose, frequency_per_day: 1 });
    setAddCompoundId("");
  };

  const cyp2d6Status = store.genetics?.cyp2d6_metabolizer ?? "unknown";
  const isPoorCYP2D6 = cyp2d6Status === "poor";
  const cyp2d6Conflicts = isPoorCYP2D6
    ? store.regimen.filter((r) => CYP2D6_SUBSTRATES.has(r.compound_id))
    : [];

  const p = store.patient;
  const ls = store.lifestyle;
  const g = store.genetics;
  const fd = store.food;

  const unaddedCompounds = AVAILABLE_COMPOUNDS.filter(
    (c) => !store.regimen.some((r) => r.compound_id === c.id)
  );

  const presetMeta = ({
    priya: { name: "Priya Sharma", emoji: "👩🏽‍💼", desc: "35F · Mumbai · Software Engineer · Poor CYP2D6 metabolizer" },
    john: { name: "John Doe", emoji: "👨🏼‍💻", desc: "42M · Austin · Biohacker · MTHFR Homozygous" },
    sarah: { name: "Sarah Jenkins", emoji: "👩🏻‍⚕️", desc: "55F · Chicago · Chronic Issues · Poor CYP2C19" },
    david: { name: "David Miller", emoji: "👨🏾‍🦳", desc: "60M · Atlanta · Sedentary · Statin User" },
  } as any)[preset] || { name: "", emoji: "", desc: "" };

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 animate-in fade-in slide-in-from-bottom-6 duration-500">
      
      {/* Hero Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-gray-900 to-slate-700 flex items-center justify-center text-2xl shadow-lg">
            {presetMeta.emoji}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-serif font-bold text-blue-gray-900">{presetMeta.name}</h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
                Demo Profile
              </span>
            </div>
            <p className="text-sm text-blue-gray-500">
              {presetMeta.desc}
            </p>
            <p className="text-xs text-blue-gray-400 mt-0.5 italic">
              Review her profile below, edit any values, then run the analysis.
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <select 
            value={preset} 
            onChange={e => setPreset(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-blue-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40 bg-white shadow-sm"
          >
            <option value="priya">Priya (Default)</option>
            <option value="john">John (Biohacker)</option>
            <option value="sarah">Sarah (Chronic)</option>
            <option value="david">David (Standard)</option>
          </select>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-bold text-blue-gray-500 hover:text-blue-gray-900 hover:bg-blue-gray-100 rounded-xl transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>
      </div>

      <div className="space-y-4">

        {/* Genetics */}
        <SectionCard
          title="Pharmacogenomics"
          icon={<Dna className="w-4 h-4" />}
          summary={`CYP2D6: ${cyp2d6Status} · CYP2C19: ${g?.cyp2c19_metabolizer ?? "unknown"}`}
        >
          <div className="grid grid-cols-2 gap-4 mt-3">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-blue-gray-600">CYP2D6 Metabolizer</label>
              <select
                className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
                value={g?.cyp2d6_metabolizer ?? "unknown"}
                onChange={(e) => store.updateGenetics({ cyp2d6_metabolizer: e.target.value as any })}
              >
                {["poor", "intermediate", "normal", "ultra_rapid", "unknown"].map((v) => (
                  <option key={v} value={v}>{v.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
                ))}
              </select>
              {isPoorCYP2D6 && (
                <p className="text-xs text-amber-600 font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Clears CYP2D6 substrates ~50% slower
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-blue-gray-600">CYP2C19 Metabolizer</label>
              <select
                className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
                value={g?.cyp2c19_metabolizer ?? "unknown"}
                onChange={(e) => store.updateGenetics({ cyp2c19_metabolizer: e.target.value as any })}
              >
                {["poor", "intermediate", "normal", "ultra_rapid", "unknown"].map((v) => (
                  <option key={v} value={v}>{v.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
                ))}
              </select>
            </div>
          </div>
        </SectionCard>

        {/* Demographics */}
        <SectionCard
          title="Demographics"
          icon={<User className="w-4 h-4" />}
          summary={`${p?.age ?? "—"}y · ${p?.sex ?? "—"} · ${p?.weight_kg ?? "—"}kg · ${p?.height_cm ?? "—"}cm`}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
            {[
              { label: "Age", field: "age", unit: "yrs", min: 18, max: 120 },
              { label: "Weight", field: "weight_kg", unit: "kg", min: 30, max: 300 },
              { label: "Height", field: "height_cm", unit: "cm", min: 100, max: 250 },
            ].map(({ label, field, unit, min, max }) => (
              <div key={field} className="space-y-1.5">
                <label className="text-xs font-bold text-blue-gray-600">{label}</label>
                <div className="relative">
                  <input
                    type="number"
                    min={min}
                    max={max}
                    className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40 pr-8"
                    value={(p as any)?.[field] ?? ""}
                    onChange={(e) => store.updatePatient({ [field]: parseFloat(e.target.value) || undefined } as any)}
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-blue-gray-400">{unit}</span>
                </div>
              </div>
            ))}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-blue-gray-600">Sex</label>
              <select
                className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
                value={p?.sex ?? ""}
                onChange={(e) => store.updatePatient({ sex: e.target.value as any })}
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </SectionCard>

        {/* Lifestyle */}
        <SectionCard
          title="Lifestyle"
          icon={<Leaf className="w-4 h-4" />}
          summary={`Sugar ${ls?.sugar_g_per_day ?? "—"}g · Sleep ${ls?.sleep_hours_avg ?? "—"}h · Stress ${ls?.stress_level ?? "—"}/10`}
        >
          <div className="space-y-5 mt-3">
            {[
              { label: "Added Sugar", field: "sugar_g_per_day", unit: "g/day", min: 0, max: 300, step: 10, danger: 120, color: "accent-brand-amber" },
              { label: "Alcohol", field: "alcohol_drinks_per_week", unit: "drinks/wk", min: 0, max: 30, step: 1, danger: 7, color: "accent-brand-amber" },
              { label: "Sleep", field: "sleep_hours_avg", unit: "h/night", min: 3, max: 12, step: 0.5, danger: null, color: "accent-brand-green" },
              { label: "Stress", field: "stress_level", unit: "/10", min: 1, max: 10, step: 1, danger: 8, color: "accent-brand-red" },
            ].map(({ label, field, unit, min, max, step, danger, color }) => {
              const val = (ls as any)?.[field] ?? min;
              const isDanger = danger !== null && val > danger;
              return (
                <div key={field} className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="text-xs font-bold text-blue-gray-600">{label}</label>
                    <span className={`text-sm font-mono font-bold ${isDanger ? "text-brand-red" : "text-brand-green"}`}>
                      {val}{unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    className={`w-full ${color} cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none`}
                    value={val}
                    onChange={(e) => store.updateLifestyle({ [field]: parseFloat(e.target.value) } as any)}
                  />
                </div>
              );
            })}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-blue-gray-600">Exercise</label>
                <span className={`text-sm font-mono font-bold ${ls?.exercise_mins_per_week && ls.exercise_mins_per_week < 150 ? "text-brand-red" : "text-brand-green"}`}>
                  {ls?.exercise_mins_per_week ?? 0} mins/wk
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={500}
                step={15}
                className="w-full accent-brand-green cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
                value={ls?.exercise_mins_per_week ?? 0}
                onChange={(e) => store.updateLifestyle({ exercise_mins_per_week: parseFloat(e.target.value) })}
              />
            </div>
          </div>
        </SectionCard>

        {/* Diet */}
        <SectionCard
          title="Diet & Nutrition"
          icon={<Utensils className="w-4 h-4" />}
          summary={`${fd?.diet_type ?? "omnivore"} · ${fd?.calories_per_day ?? "—"} kcal · ${fd?.processed_food_pct ?? "—"}% processed · ${fd?.fiber_g_per_day ?? "—"}g fiber`}
        >
          <div className="space-y-5 mt-3">
            {/* Diet type */}
            <div className="grid grid-cols-5 gap-2">
              {DIET_TYPES.map((d) => (
                <button
                  key={d.id}
                  onClick={() => store.updateFood({ diet_type: d.id })}
                  className={`flex flex-col items-center py-2.5 px-1 rounded-xl border-2 text-center transition-all ${
                    fd?.diet_type === d.id
                      ? "border-brand-green bg-brand-green/5"
                      : "border-blue-gray-200 hover:border-blue-gray-300 bg-white"
                  }`}
                >
                  <span className="text-xl">{d.icon}</span>
                  <span className={`text-[10px] font-bold mt-1 ${fd?.diet_type === d.id ? "text-brand-green" : "text-blue-gray-600"}`}>
                    {d.label}
                  </span>
                </button>
              ))}
            </div>

            {[
              { label: "Daily Calories", field: "calories_per_day", unit: "kcal", min: 1200, max: 4000, step: 50, color: "accent-brand-green", danger: 2500 },
              { label: "Ultra-Processed Foods", field: "processed_food_pct", unit: "%", min: 0, max: 100, step: 5, color: "accent-brand-amber", danger: 40 },
              { label: "Fiber", field: "fiber_g_per_day", unit: "g/day", min: 0, max: 60, step: 1, color: "accent-brand-green", danger: null },
              { label: "Red Meat", field: "red_meat_g_per_week", unit: "g/wk", min: 0, max: 1000, step: 25, color: "accent-brand-red", danger: 500 },
            ].map(({ label, field, unit, min, max, step, color, danger }) => {
              const val = (fd as any)?.[field] ?? min;
              const isDanger = danger !== null && val > danger;
              return (
                <div key={field} className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="text-xs font-bold text-blue-gray-600">{label}</label>
                    <span className={`text-sm font-mono font-bold ${isDanger ? "text-brand-red" : "text-brand-green"}`}>
                      {typeof val === "number" ? val.toLocaleString() : val}{unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    className={`w-full ${color} cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none`}
                    value={val}
                    onChange={(e) => store.updateFood({ [field]: parseFloat(e.target.value) } as any)}
                  />
                </div>
              );
            })}
          </div>
        </SectionCard>

        {/* Regimen */}
        <SectionCard
          title="Supplement & Medication Stack"
          icon={<Pill className="w-4 h-4" />}
          summary={`${store.regimen.length} compounds active${cyp2d6Conflicts.length > 0 ? " · ⚠️ CYP2D6 interaction" : ""}`}
        >
          <div className="space-y-3 mt-3">
            {/* CYP2D6 warning banner */}
            {cyp2d6Conflicts.length > 0 && (
              <div className="flex items-start gap-2.5 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-xs text-amber-700 font-medium">
                  <strong>CYP2D6 interaction:</strong>{" "}
                  {cyp2d6Conflicts.map((r) => AVAILABLE_COMPOUNDS.find((c) => c.id === r.compound_id)?.name || r.compound_id).join(", ")}{" "}
                  cleared ~50% slower. Hepatic load elevated.
                </p>
              </div>
            )}

            {/* Compound list */}
            {store.regimen.map((item) => {
              const compound = AVAILABLE_COMPOUNDS.find((c) => c.id === item.compound_id);
              const isCYP2D6 = isPoorCYP2D6 && CYP2D6_SUBSTRATES.has(item.compound_id);
              return (
                <div
                  key={item.compound_id}
                  className={`flex items-center gap-3 p-3 rounded-xl border ${
                    isCYP2D6 ? "border-amber-200 bg-amber-50/50" : "border-blue-gray-100 bg-white"
                  }`}
                >
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${isCYP2D6 ? "bg-amber-100 text-amber-700" : "bg-blue-gray-100 text-blue-gray-600"}`}>
                    {isCYP2D6 ? "⚠️" : "💊"}
                  </span>
                  <span className="flex-1 text-sm font-semibold text-blue-gray-900">
                    {compound?.name || item.compound_id}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min={1}
                      className="w-20 px-2 py-1.5 rounded-lg border border-blue-gray-200 text-right text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
                      value={item.dose_mg}
                      onChange={(e) => store.updateCompound(item.compound_id, parseFloat(e.target.value) || 0)}
                    />
                    <span className="text-xs text-blue-gray-500 font-medium">mg</span>
                  </div>
                  <button
                    onClick={() => store.removeCompound(item.compound_id)}
                    className="p-1.5 rounded-lg text-blue-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                  >
                    ✕
                  </button>
                </div>
              );
            })}

            {/* Add compound */}
            {unaddedCompounds.length > 0 && (
              <div className="flex gap-2 mt-2">
                <select
                  value={addCompoundId}
                  onChange={(e) => setAddCompoundId(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
                >
                  <option value="">Add a compound…</option>
                  {unaddedCompounds.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <button
                  onClick={handleAddCompound}
                  disabled={!addCompoundId}
                  className="px-4 py-2 bg-blue-gray-900 text-white rounded-xl text-sm font-bold hover:bg-black transition-colors disabled:opacity-40"
                >
                  + Add
                </button>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Labs */}
        <SectionCard
          title="Laboratory Values"
          icon={<FlaskConical className="w-4 h-4" />}
          summary={`AST ${store.labs?.ast_u_per_l ?? "—"} · ALT ${store.labs?.alt_u_per_l ?? "—"} · Bili ${store.labs?.bilirubin_mg_per_dl ?? "—"}`}
        >
          <div className="grid grid-cols-3 gap-4 mt-3">
            {[
              { label: "AST", field: "ast_u_per_l", unit: "U/L", warn: 40 },
              { label: "ALT", field: "alt_u_per_l", unit: "U/L", warn: 40 },
              { label: "Bilirubin", field: "bilirubin_mg_per_dl", unit: "mg/dL", warn: 1.2 },
            ].map(({ label, field, unit, warn }) => {
              const val = (store.labs as any)?.[field];
              const isHigh = val != null && val > warn;
              return (
                <div key={field} className="space-y-1.5">
                  <label className="text-xs font-bold text-blue-gray-600">{label}</label>
                  <div className="relative">
                    <input
                      type="number"
                      min={0}
                      step={0.1}
                      placeholder="—"
                      className={`w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 pr-10 ${
                        isHigh ? "border-amber-300 text-amber-700 focus:ring-amber-300/40" : "border-blue-gray-200 focus:ring-brand-green/40"
                      }`}
                      value={val ?? ""}
                      onChange={(e) => store.updateLabs({ [field]: parseFloat(e.target.value) || undefined } as any)}
                    />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-blue-gray-400 font-medium">{unit}</span>
                  </div>
                  {isHigh && <p className="text-[10px] text-amber-600 font-medium">↑ Elevated</p>}
                </div>
              );
            })}
          </div>
        </SectionCard>

      </div>

      {/* Error banner */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Sticky Run button */}
      <div className="mt-8 flex flex-col items-center gap-3">
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="group relative w-full max-w-md py-5 bg-gradient-to-r from-blue-gray-900 to-black text-white rounded-2xl font-bold shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all flex items-center justify-center gap-3 overflow-hidden text-lg disabled:opacity-60 disabled:hover:translate-y-0"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin relative z-10" />
              <span className="relative z-10">Analysing Priya's Stack…</span>
            </>
          ) : (
            <>
              <Zap className="w-6 h-6 relative z-10 text-brand-amber group-hover:scale-110 transition-transform" />
              <span className="relative z-10">Run Analysis</span>
            </>
          )}
          <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
        </button>
        <p className="text-xs text-blue-gray-400 text-center">
          Phase 0 prototype · Not medical advice
        </p>
      </div>
    </div>
  );
}
