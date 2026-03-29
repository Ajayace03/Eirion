import { useState } from "react";
import { useWizardStore } from "../../store/wizardStore";
import { Plus, AlertTriangle, X, ChevronDown, ChevronUp } from "lucide-react";

const AVAILABLE_COMPOUNDS = [
  { id: "ashwagandha", name: "Ashwagandha (KSM-66)", defaultDose: 300, category: "Adaptogen" },
  { id: "metformin", name: "Metformin", defaultDose: 500, category: "Medication" },
  { id: "omega3", name: "Omega-3 Fish Oil", defaultDose: 2000, category: "Supplement" },
  { id: "vitamin_d", name: "Vitamin D3", defaultDose: 2000, category: "Supplement" },
  { id: "nac", name: "NAC (N-Acetyl Cysteine)", defaultDose: 600, category: "Supplement" },
  { id: "magnesium", name: "Magnesium Glycinate", defaultDose: 400, category: "Supplement" },
  { id: "zinc", name: "Zinc", defaultDose: 15, category: "Supplement" },
  { id: "quercetin", name: "Quercetin", defaultDose: 500, category: "Supplement" },
  { id: "berberine", name: "Berberine", defaultDose: 500, category: "Supplement" },
  { id: "curcumin", name: "Curcumin / Turmeric", defaultDose: 500, category: "Supplement" },
  { id: "coq10", name: "CoQ10 (Ubiquinol)", defaultDose: 200, category: "Supplement" },
  { id: "atorvastatin", name: "Atorvastatin (Lipitor)", defaultDose: 10, category: "Medication" },
  { id: "rosuvastatin", name: "Rosuvastatin (Crestor)", defaultDose: 10, category: "Medication" },
  { id: "sertraline", name: "Sertraline (Zoloft)", defaultDose: 50, category: "Medication" },
  { id: "escitalopram", name: "Escitalopram (Lexapro)", defaultDose: 10, category: "Medication" },
];

const TIMING_OPTIONS = [
  { id: "morning", label: "🌅 Morning" },
  { id: "afternoon", label: "☀️ Afternoon" },
  { id: "with_food", label: "🍽️ With Food" },
  { id: "evening", label: "🌆 Evening" },
  { id: "before_sleep", label: "🌙 Before Sleep" },
];

const CYP2D6_SUBSTRATES = new Set(["ashwagandha", "berberine", "sertraline", "escitalopram"]);

function getCompoundName(id: string) {
  return AVAILABLE_COMPOUNDS.find((c) => c.id === id)?.name || id;
}
function getCompoundCategory(id: string) {
  return AVAILABLE_COMPOUNDS.find((c) => c.id === id)?.category || "Supplement";
}

function CompoundCard({ item }: { item: any }) {
  const { removeCompound, updateCompound, updateRegimenItem, genetics } = useWizardStore();
  const [expanded, setExpanded] = useState(false);
  const isPoorCYP2D6 = genetics?.cyp2d6_metabolizer === "poor";
  const isCYP2D6Alert = isPoorCYP2D6 && CYP2D6_SUBSTRATES.has(item.compound_id);
  const category = getCompoundCategory(item.compound_id);
  const isRx = category === "Medication";

  const categoryColor = {
    Medication: "bg-blue-100 text-blue-700",
    Adaptogen: "bg-purple-100 text-purple-700",
    Supplement: "bg-brand-green/10 text-brand-green",
  }[category] || "bg-blue-gray-100 text-blue-gray-600";

  const toggleTiming = (t: string) => {
    const current: string[] = item.timing || [];
    const next = (current.includes(t) ? current.filter((x: string) => x !== t) : [...current, t]) as Array<"morning"|"afternoon"|"evening"|"with_food"|"before_sleep">;
    updateRegimenItem(item.compound_id, { timing: next });
  };

  return (
    <div className={`rounded-2xl border shadow-sm overflow-hidden ${isCYP2D6Alert ? "border-amber-300" : "border-blue-gray-100"}`}>
      {/* Header row */}
      <div className={`flex items-center gap-3 px-4 py-3.5 ${isCYP2D6Alert ? "bg-amber-50" : "bg-white"}`}>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${categoryColor}`}>
          {isRx ? "Rx" : category}
        </span>
        <span className="flex-1 text-sm font-bold text-blue-gray-900 truncate">
          {getCompoundName(item.compound_id)}
        </span>
        {isCYP2D6Alert && <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />}
        <div className="flex items-center gap-1.5">
          <input
            type="number"
            min={1}
            className="w-20 px-2.5 py-1.5 rounded-xl border border-blue-gray-200 text-sm text-right focus:outline-none focus:ring-2 focus:ring-brand-green/30"
            value={item.dose_mg}
            onChange={(e) => updateCompound(item.compound_id, parseFloat(e.target.value) || 0)}
          />
          <span className="text-xs text-blue-gray-500 font-medium">mg</span>
        </div>
        <button onClick={() => setExpanded((x) => !x)} className="p-1.5 rounded-lg hover:bg-blue-gray-100 transition-colors">
          {expanded ? <ChevronUp className="w-4 h-4 text-blue-gray-400" /> : <ChevronDown className="w-4 h-4 text-blue-gray-400" />}
        </button>
        <button onClick={() => removeCompound(item.compound_id)} className="p-1.5 rounded-lg hover:bg-red-50 text-blue-gray-400 hover:text-red-500 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Expanded detail panel */}
      {expanded && (
        <div className="border-t border-blue-gray-100 bg-blue-gray-50/30 px-4 py-4 grid grid-cols-2 gap-4 text-sm">
          {/* Timing */}
          <div className="col-span-2 space-y-2">
            <label className="text-xs font-bold text-blue-gray-600">When do you take it?</label>
            <div className="flex flex-wrap gap-2">
              {TIMING_OPTIONS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => toggleTiming(t.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    (item.timing || []).includes(t.id)
                      ? "border-blue-gray-700 bg-blue-gray-900 text-white"
                      : "border-blue-gray-200 bg-white text-blue-gray-600 hover:border-blue-gray-400"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Frequency */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-blue-gray-600">Times per day</label>
            <select
              className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
              value={item.frequency_per_day || 1}
              onChange={(e) => updateRegimenItem(item.compound_id, { frequency_per_day: parseFloat(e.target.value) })}
            >
              <option value={0.5}>Every 2 days</option>
              <option value={1}>Once daily</option>
              <option value={2}>Twice daily</option>
              <option value={3}>3× daily</option>
            </select>
          </div>

          {/* Prescribed by */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-blue-gray-600">Prescribed / sourced by</label>
            <select
              className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none"
              value={item.prescribed_by || "self"}
              onChange={(e) => updateRegimenItem(item.compound_id, { prescribed_by: e.target.value as any })}
            >
              <option value="self">Self · OTC</option>
              <option value="gp">GP / Doctor</option>
              <option value="specialist">Specialist</option>
              <option value="online">Online consultation</option>
            </select>
          </div>

          {/* Started since */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-blue-gray-600">Started (approx.)</label>
            <input
              type="month"
              className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
              value={item.start_date || ""}
              onChange={(e) => updateRegimenItem(item.compound_id, { start_date: e.target.value })}
            />
          </div>

          {/* Reason / condition */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-blue-gray-600">Taken for (condition)</label>
            <input
              type="text"
              placeholder="e.g. stress, prediabetes…"
              className="w-full px-3 py-2 rounded-xl border border-blue-gray-200 bg-white text-sm focus:outline-none"
              value={(item.reason_condition_ids || []).join(", ")}
              onChange={(e) =>
                updateRegimenItem(item.compound_id, {
                  reason_condition_ids: e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean),
                })
              }
            />
          </div>

          {isCYP2D6Alert && (
            <div className="col-span-2 flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-700">
                <strong>CYP2D6 Poor Metabolizer:</strong> {getCompoundName(item.compound_id)} clears ~50% slower than average,
                leading to compound accumulation and elevated hepatic load over months of use.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Step8Regimen() {
  const { regimen, addCompound, genetics } = useWizardStore();
  const [selectedId, setSelectedId] = useState("");
  const isPoorCYP2D6 = genetics?.cyp2d6_metabolizer === "poor";
  const cyp2d6Conflicts = isPoorCYP2D6 ? regimen.filter((r: any) => CYP2D6_SUBSTRATES.has(r.compound_id)) : [];
  const unaddedCompounds = AVAILABLE_COMPOUNDS.filter((c) => !regimen.some((r: any) => r.compound_id === c.id));

  const handleAdd = () => {
    const c = AVAILABLE_COMPOUNDS.find((x) => x.id === selectedId);
    if (c) {
      addCompound({
        compound_id: c.id,
        dose_mg: c.defaultDose,
        frequency_per_day: 1,
        timing: [] as Array<"morning" | "afternoon" | "evening" | "with_food" | "before_sleep">,
        prescribed_by: "self",
        is_rx: c.category === "Medication",
        reason_condition_ids: [],
        start_date: undefined,
      });
      setSelectedId("");
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-4">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Supplement & Medication Stack
        </h2>
        <p className="text-blue-gray-600 text-sm">
          Add each compound with timing, dosage, and reason. Expand any card for full detail.
        </p>
      </div>

      {/* CYP2D6 top-level warning */}
      {cyp2d6Conflicts.length > 0 && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-2xl">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-amber-800">CYP2D6 Interaction Detected</p>
            <p className="text-sm text-amber-700 mt-0.5">
              {cyp2d6Conflicts.map((r: any) => getCompoundName(r.compound_id)).join(" and ")}{" "}
              are CYP2D6 substrates. As a poor metabolizer you clear these ~50% slower,
              significantly increasing hepatic accumulation and load.
            </p>
          </div>
        </div>
      )}

      {/* Compound cards */}
      <div className="space-y-3">
        {regimen.length === 0 && (
          <div className="text-center py-8 text-blue-gray-400 text-sm italic">
            No compounds added yet. Use the picker below.
          </div>
        )}
        {regimen.map((item: any) => (
          <CompoundCard key={item.compound_id} item={item} />
        ))}
      </div>

      {/* Add compound */}
      {unaddedCompounds.length > 0 && (
        <div className="flex gap-2 pt-4 border-t border-blue-gray-100">
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="flex-1 px-4 py-3 rounded-2xl border border-blue-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/40"
          >
            <option value="">Add a compound to your stack…</option>
            {["Medication", "Adaptogen", "Supplement"].map((cat) => (
              <optgroup key={cat} label={cat}>
                {unaddedCompounds.filter((c) => c.category === cat).map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.defaultDose}mg default)</option>
                ))}
              </optgroup>
            ))}
          </select>
          <button
            onClick={handleAdd}
            disabled={!selectedId}
            className="px-5 py-3 bg-blue-gray-900 text-white rounded-2xl text-sm font-bold disabled:opacity-40 hover:bg-black transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Add
          </button>
        </div>
      )}
    </div>
  );
}
