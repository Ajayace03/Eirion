import { useWizardStore } from "../../store/wizardStore";

export default function Step3Lifestyle() {
  const { lifestyle, updateLifestyle } = useWizardStore();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Lifestyle Stressors</h2>
        <p className="text-blue-gray-600">Environmental inputs directly throttle metabolic clearance capacity.</p>
      </div>

      <div className="grid gap-8 max-w-xl mx-auto">
        
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">Added Sugar (Fructose)</label>
            <span className="text-sm font-mono text-brand-amber font-bold">{lifestyle.sugar_g_per_day} g/day</span>
          </div>
          <input
            type="range"
            min="0"
            max="300"
            step="10"
            className="w-full accent-brand-amber cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={lifestyle.sugar_g_per_day}
            onChange={(e) => updateLifestyle({ sugar_g_per_day: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>0g</span>
            <span>Optimal &lt;60g</span>
            <span>300g</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">Alcohol Intake</label>
            <span className="text-sm font-mono text-brand-amber font-bold">{lifestyle.alcohol_drinks_per_week} drinks/wk</span>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            step="1"
            className="w-full accent-brand-amber cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={lifestyle.alcohol_drinks_per_week}
            onChange={(e) => updateLifestyle({ alcohol_drinks_per_week: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>0</span>
            <span>Limit ≤7</span>
            <span>30+</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">Average Sleep</label>
            <span className="text-sm font-mono text-brand-green font-bold">{lifestyle.sleep_hours_avg} hours/night</span>
          </div>
          <input
            type="range"
            min="3"
            max="12"
            step="0.5"
            className="w-full accent-brand-green cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={lifestyle.sleep_hours_avg}
            onChange={(e) => updateLifestyle({ sleep_hours_avg: parseFloat(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>Critical &lt;5h</span>
            <span>Target ≥7h</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">Chronic Stress Load</label>
            <span className="text-sm font-mono text-brand-red font-bold">{lifestyle.stress_level}/10</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            className="w-full accent-brand-red cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={lifestyle.stress_level}
            onChange={(e) => updateLifestyle({ stress_level: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>Low (1)</span>
            <span>High Risk (≥8)</span>
            <span>Extreme (10)</span>
          </div>
        </div>

      </div>
    </div>
  );
}
