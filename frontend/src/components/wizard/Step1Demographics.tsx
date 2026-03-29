import { useWizardStore } from "../../store/wizardStore";
import { AlertTriangle } from "lucide-react";

export default function Step1Demographics() {
  const { patient, updatePatient } = useWizardStore();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Basic Information</h2>
        <p className="text-blue-gray-600">Let's start with your physical metrics.</p>
      </div>

      <div className="max-w-xl mx-auto mb-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex gap-3 text-amber-800">
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-bold mb-1">AI System Disclaimer</p>
          <p>
            Eirion uses experimental ML models (GNN/Tox21) to generate longevity insights. 
            This is <strong>not medical advice</strong>. Always consult a licensed clinician before altering your regimen.
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 max-w-xl mx-auto">
        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">Age</label>
          <input
            type="number"
            min="18"
            max="120"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={patient.age || ""}
            onChange={(e) => updatePatient({ age: isNaN(e.target.valueAsNumber) ? undefined : e.target.valueAsNumber })}
            placeholder="e.g. 35"
            onKeyDown={(e) => ["e", "E", "+", "-", "."].includes(e.key) && e.preventDefault()}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">Biological Sex</label>
          <select
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all bg-white"
            value={patient.sex || ""}
            onChange={(e) => updatePatient({ sex: e.target.value as "male" | "female" | "other" })}
          >
            <option value="" disabled>Select...</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">Weight (kg)</label>
          <input
            type="number"
            min="30"
            max="300"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={patient.weight_kg || ""}
            onChange={(e) => updatePatient({ weight_kg: isNaN(e.target.valueAsNumber) ? undefined : e.target.valueAsNumber })}
            placeholder="e.g. 70"
            onKeyDown={(e) => ["e", "E", "+", "-"].includes(e.key) && e.preventDefault()}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">Height (cm)</label>
          <input
            type="number"
            min="100"
            max="250"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={patient.height_cm || ""}
            onChange={(e) => updatePatient({ height_cm: isNaN(e.target.valueAsNumber) ? undefined : e.target.valueAsNumber })}
            placeholder="e.g. 170"
            onKeyDown={(e) => ["e", "E", "+", "-"].includes(e.key) && e.preventDefault()}
          />
        </div>
      </div>
    </div>
  );
}
