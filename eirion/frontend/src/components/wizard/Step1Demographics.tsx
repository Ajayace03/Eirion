import { useWizardStore } from "../../store/wizardStore";

export default function Step1Demographics() {
  const { patient, updatePatient } = useWizardStore();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Basic Information</h2>
        <p className="text-blue-gray-600">Let's start with your physical metrics.</p>
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
            onChange={(e) => updatePatient({ age: parseInt(e.target.value) || undefined })}
            placeholder="e.g. 35"
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
            onChange={(e) => updatePatient({ weight_kg: parseInt(e.target.value) || undefined })}
            placeholder="e.g. 70"
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
            onChange={(e) => updatePatient({ height_cm: parseInt(e.target.value) || undefined })}
            placeholder="e.g. 170"
          />
        </div>
      </div>
    </div>
  );
}
