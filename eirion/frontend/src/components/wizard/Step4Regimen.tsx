import { useState } from "react";
import { useWizardStore } from "../../store/wizardStore";
import { Plus, Trash2 } from "lucide-react";

// Mocking the knowledge tables from the backend for the frontend UI
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

export default function Step4Regimen() {
  const { regimen, addCompound, removeCompound, updateCompound } = useWizardStore();
  const [selectedId, setSelectedId] = useState("");

  const handleAdd = () => {
    if (!selectedId) return;
    const compound = AVAILABLE_COMPOUNDS.find((c) => c.id === selectedId);
    if (compound) {
      addCompound({
        compound_id: compound.id,
        dose_mg: compound.defaultDose,
        frequency_per_day: 1,
      });
    }
    setSelectedId("");
  };

  const getCompoundName = (id: string) => {
    return AVAILABLE_COMPOUNDS.find((c) => c.id === id)?.name || id;
  };

  const unselectedCompounds = AVAILABLE_COMPOUNDS.filter(
    (c) => !regimen.some((r) => r.compound_id === c.id)
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Supplement Stack</h2>
        <p className="text-blue-gray-600">Add the longevity compounds and daily medications you take.</p>
      </div>

      <div className="max-w-2xl mx-auto space-y-6">
        
        {/* Add new compound */}
        <div className="flex gap-4 items-end bg-blue-50/50 p-4 rounded-xl border border-blue-100">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium text-blue-gray-700">Select Compound</label>
            <select
              className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green bg-white"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="" disabled>Search or select...</option>
              {unselectedCompounds.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleAdd}
            disabled={!selectedId}
            className="h-[50px] px-6 bg-blue-gray-900 text-white rounded-xl font-bold hover:bg-black transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" /> Add
          </button>
        </div>

        {/* Current Stack List */}
        <div className="space-y-3">
          {regimen.length === 0 ? (
            <div className="text-center py-8 text-blue-gray-400 border-2 border-dashed border-blue-gray-200 rounded-xl">
              Your stack is empty.<br />Add a compound above to begin.
            </div>
          ) : (
            regimen.map((item) => (
              <div key={item.compound_id} className="flex gap-4 items-center bg-white border border-blue-gray-100 p-4 rounded-xl shadow-sm animate-in fade-in slide-in-from-left-4">
                <div className="flex-1">
                  <span className="font-bold text-blue-gray-900 block">{getCompoundName(item.compound_id)}</span>
                </div>
                <div className="w-32 flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    className="w-full px-3 py-2 rounded-lg border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 text-right"
                    value={item.dose_mg || ""}
                    onChange={(e) => updateCompound(item.compound_id, parseInt(e.target.value) || 0)}
                  />
                  <span className="text-sm text-blue-gray-500 font-medium">mg</span>
                </div>
                <button
                  onClick={() => removeCompound(item.compound_id)}
                  className="p-2 text-blue-gray-400 hover:text-brand-red hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))
          )}
        </div>

      </div>
    </div>
  );
}
