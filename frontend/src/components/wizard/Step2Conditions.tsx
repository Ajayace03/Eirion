import { useWizardStore } from "../../store/wizardStore";
import { Plus, X } from "lucide-react";
import { useState } from "react";

const CONDITION_GROUPS = [
  {
    group: "Metabolic",
    icon: "🧬",
    conditions: [
      { id: "prediabetes", label: "Prediabetes" },
      { id: "type2_diabetes", label: "Type 2 Diabetes" },
      { id: "metabolic_syndrome", label: "Metabolic Syndrome" },
      { id: "hyperlipidemia", label: "High Cholesterol" },
      { id: "nafld", label: "Fatty Liver / NAFLD" },
      { id: "gout", label: "Gout / High Uric Acid" },
    ],
  },
  {
    group: "Cardiovascular",
    icon: "❤️",
    conditions: [
      { id: "hypertension", label: "Hypertension" },
      { id: "cardiovascular_risk", label: "Cardiovascular Risk" },
      { id: "osteoporosis", label: "Osteoporosis" },
    ],
  },
  {
    group: "Mental & Stress",
    icon: "🧠",
    conditions: [
      { id: "anxiety", label: "Anxiety / Stress" },
      { id: "depression", label: "Depression" },
      { id: "burnout", label: "Burnout / Chronic Fatigue" },
      { id: "sleep_disorder", label: "Sleep Disorder" },
    ],
  },
  {
    group: "Hormonal & Immune",
    icon: "⚗️",
    conditions: [
      { id: "hypothyroidism", label: "Hypothyroidism" },
      { id: "hyperthyroidism", label: "Hyperthyroidism" },
      { id: "pcos", label: "PCOS / Hormonal Imbalance" },
      { id: "autoimmune", label: "Autoimmune / Inflammatory" },
    ],
  },
  {
    group: "Organ Health",
    icon: "🫘",
    conditions: [
      { id: "kidney_disease", label: "Kidney Disease / CKD" },
      { id: "cancer_history", label: "Cancer History" },
    ],
  },
];

const SEVERITY_LABELS = {
  mild: { label: "Mild", color: "text-brand-green bg-brand-green/10" },
  moderate: { label: "Moderate", color: "text-brand-amber bg-brand-amber/10" },
  severe: { label: "Severe", color: "text-brand-red bg-brand-red/10" },
};

export default function Step2Conditions() {
  const { conditions, addCondition, removeCondition, updateCondition } = useWizardStore();
  const [customInput, setCustomInput] = useState("");

  const activeIds = new Set(conditions.map((c: any) => c.condition_id));

  const toggleCondition = (id: string) => {
    if (activeIds.has(id)) {
      removeCondition(id);
    } else {
      addCondition({ condition_id: id, severity: "mild", diagnosed: false });
    }
  };

  const addCustom = () => {
    const id = customInput.trim().toLowerCase().replace(/\s+/g, "_");
    if (!id || activeIds.has(id)) return;
    addCondition({ condition_id: id, severity: "mild", diagnosed: false });
    setCustomInput("");
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Health Conditions
        </h2>
        <p className="text-blue-gray-600">
          Select any conditions you are managing or optimising for. This drives which
          pathways EIRION prioritises and which compounds are recommended.
        </p>
      </div>

      {conditions.length === 0 && (
        <p className="text-sm text-blue-gray-400 text-center italic py-2">
          No conditions selected — the engine will run a general longevity analysis.
        </p>
      )}

      {/* Active conditions — severity chips */}
      {conditions.length > 0 && (
        <div className="flex flex-wrap gap-2 pb-2 border-b border-blue-gray-100">
          {conditions.map((c: any) => (
            <div
              key={c.condition_id}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-blue-gray-200 bg-white shadow-sm text-sm"
            >
              <span className="font-semibold text-blue-gray-800 capitalize">
                {c.condition_id.replace(/_/g, " ")}
              </span>
              <select
                className={`text-xs font-bold rounded-full px-2 py-0.5 border-0 focus:outline-none cursor-pointer ${
                  SEVERITY_LABELS[c.severity as keyof typeof SEVERITY_LABELS]?.color
                }`}
                value={c.severity}
                onChange={(e) => updateCondition(c.condition_id, { severity: e.target.value as any })}
              >
                <option value="mild">Mild</option>
                <option value="moderate">Moderate</option>
                <option value="severe">Severe</option>
              </select>
              <label className="flex items-center gap-1 text-xs text-blue-gray-500 cursor-pointer">
                <input
                  type="checkbox"
                  checked={c.diagnosed}
                  onChange={(e) => updateCondition(c.condition_id, { diagnosed: e.target.checked })}
                  className="accent-brand-green"
                />
                Dx
              </label>
              <button
                onClick={() => removeCondition(c.condition_id)}
                className="text-blue-gray-400 hover:text-red-500 transition-colors ml-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Condition Groups Grid */}
      <div className="space-y-6">
        {CONDITION_GROUPS.map((group) => (
          <div key={group.group}>
            <p className="text-xs font-bold text-blue-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
              <span>{group.icon}</span> {group.group}
            </p>
            <div className="flex flex-wrap gap-2">
              {group.conditions.map(({ id, label }) => {
                const active = activeIds.has(id);
                return (
                  <button
                    key={id}
                    onClick={() => toggleCondition(id)}
                    className={`px-4 py-2 rounded-xl text-sm font-semibold border-2 transition-all ${
                      active
                        ? "border-blue-gray-900 bg-blue-gray-900 text-white shadow-sm"
                        : "border-blue-gray-200 bg-white text-blue-gray-700 hover:border-blue-gray-400"
                    }`}
                  >
                    {active && <span className="mr-1.5">✓</span>}
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Custom condition input */}
      <div className="flex gap-2 pt-4 border-t border-blue-gray-100">
        <input
          type="text"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCustom()}
          placeholder="Add a custom condition…"
          className="flex-1 px-4 py-2.5 rounded-xl border border-blue-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
        />
        <button
          onClick={addCustom}
          disabled={!customInput.trim()}
          className="px-4 py-2.5 bg-blue-gray-900 text-white rounded-xl text-sm font-bold disabled:opacity-40 hover:bg-black transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add
        </button>
      </div>

      <p className="text-xs text-blue-gray-400 text-center">
        "Dx" = formally diagnosed · Severity affects pathway weighting in the engine
      </p>
    </div>
  );
}
