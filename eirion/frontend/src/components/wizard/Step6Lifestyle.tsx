import { useWizardStore } from "../../store/wizardStore";
import { Leaf, Moon, Zap, Wine, Droplets, Shield } from "lucide-react";

export default function Step6Lifestyle() {
  const { lifestyle, updateLifestyle } = useWizardStore();

  const handleUpdate = (field: keyof typeof lifestyle, value: any) => {
    updateLifestyle({ [field]: value });
  };

  return (
    <div className="animate-in fade-in slide-in-from-right-8 duration-500">
      <div className="text-center mb-10">
        <div className="w-16 h-16 rounded-2xl bg-brand-green/10 flex items-center justify-center mx-auto mb-4 border border-brand-green/20">
          <Leaf className="w-8 h-8 text-brand-green" />
        </div>
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-3">
          Lifestyle & Environment
        </h2>
        <p className="text-blue-gray-500 max-w-lg mx-auto">
          These factors significantly impact multi-organ health, modifying the baseline load computed from your regimen.
        </p>
      </div>

      <div className="space-y-6">
        
        {/* Sleep & Stress */}
        <div className="bg-white p-6 rounded-2xl border border-blue-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-50 rounded-lg">
              <Moon className="w-5 h-5 text-indigo-500" />
            </div>
            <h3 className="text-lg font-bold text-blue-gray-900">Sleep & Stress</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Average Sleep Time</label>
                <span className="text-sm font-mono text-indigo-600 font-bold">{lifestyle.sleep_hours_avg}h</span>
              </div>
              <input
                type="range" min={3} max={12} step={0.5}
                value={lifestyle.sleep_hours_avg}
                onChange={(e) => handleUpdate("sleep_hours_avg", parseFloat(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-indigo-500"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Sleep Quality (1-10)</label>
                <span className="text-sm font-mono text-indigo-600 font-bold">{lifestyle.sleep_quality}/10</span>
              </div>
              <input
                type="range" min={1} max={10} step={1}
                value={lifestyle.sleep_quality}
                onChange={(e) => handleUpdate("sleep_quality", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Stress Level (1-10)</label>
                <span className="text-sm font-mono text-brand-red font-bold">{lifestyle.stress_level}/10</span>
              </div>
              <input
                type="range" min={1} max={10} step={1}
                value={lifestyle.stress_level}
                onChange={(e) => handleUpdate("stress_level", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-brand-red"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Cognitive Load (1-10)</label>
                <span className="text-sm font-mono text-brand-amber font-bold">{lifestyle.cognitive_load}/10</span>
              </div>
              <input
                type="range" min={1} max={10} step={1}
                value={lifestyle.cognitive_load}
                onChange={(e) => handleUpdate("cognitive_load", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-brand-amber"
              />
            </div>
          </div>
        </div>

        {/* Activity */}
        <div className="bg-white p-6 rounded-2xl border border-blue-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-orange-50 rounded-lg">
              <Zap className="w-5 h-5 text-orange-500" />
            </div>
            <h3 className="text-lg font-bold text-blue-gray-900">Activity</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Aerobic Exercise</label>
                <span className="text-sm font-mono text-orange-600 font-bold">{lifestyle.exercise_mins_per_week} min/wk</span>
              </div>
              <input
                type="range" min={0} max={600} step={15}
                value={lifestyle.exercise_mins_per_week}
                onChange={(e) => handleUpdate("exercise_mins_per_week", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-orange-500"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Resistance Training</label>
                <span className="text-sm font-mono text-orange-600 font-bold">{lifestyle.resistance_training_days} days/wk</span>
              </div>
              <input
                type="range" min={0} max={7} step={1}
                value={lifestyle.resistance_training_days}
                onChange={(e) => handleUpdate("resistance_training_days", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-orange-500"
              />
            </div>
          </div>
        </div>

        {/* Diet & Hydration */}
        <div className="bg-white p-6 rounded-2xl border border-blue-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-rose-50 rounded-lg">
              <Droplets className="w-5 h-5 text-rose-500" />
            </div>
            <h3 className="text-lg font-bold text-blue-gray-900">Diet & Hydration</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-bold text-blue-gray-700 block mb-2">Diet Type</label>
              <div className="flex flex-wrap gap-2">
                {["omnivore", "mediterranean", "vegan", "keto", "standard_american"].map((type) => (
                  <button
                    key={type}
                    onClick={() => handleUpdate("diet_type", type)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all ${
                      lifestyle.diet_type === type
                        ? "bg-rose-500 text-white shadow-sm"
                        : "bg-blue-gray-50 text-blue-gray-600 hover:bg-blue-gray-100"
                    }`}
                  >
                    {type.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Processed Food Frequency</label>
                <span className="text-sm font-mono text-rose-600 font-bold">{lifestyle.processed_food_frequency}/10</span>
              </div>
              <input
                type="range" min={1} max={10} step={1}
                value={lifestyle.processed_food_frequency}
                onChange={(e) => handleUpdate("processed_food_frequency", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-rose-500"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Hydration</label>
                <span className="text-sm font-mono text-rose-600 font-bold">{lifestyle.hydration_oz_per_day} oz/day</span>
              </div>
              <input
                type="range" min={0} max={200} step={10}
                value={lifestyle.hydration_oz_per_day}
                onChange={(e) => handleUpdate("hydration_oz_per_day", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-rose-500"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Added Sugar Intake</label>
                <span className="text-sm font-mono text-rose-600 font-bold">{lifestyle.sugar_g_per_day} g/day</span>
              </div>
              <input
                type="range" min={0} max={250} step={5}
                value={lifestyle.sugar_g_per_day}
                onChange={(e) => handleUpdate("sugar_g_per_day", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-rose-500"
              />
            </div>
          </div>
        </div>

        {/* Substances */}
        <div className="bg-white p-6 rounded-2xl border border-blue-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-50 rounded-lg">
              <Wine className="w-5 h-5 text-purple-500" />
            </div>
            <h3 className="text-lg font-bold text-blue-gray-900">Substances</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Alcohol Intake</label>
                <span className="text-sm font-mono text-purple-600 font-bold">{lifestyle.alcohol_drinks_per_week} drinks/wk</span>
              </div>
              <input
                type="range" min={0} max={30} step={1}
                value={lifestyle.alcohol_drinks_per_week}
                onChange={(e) => handleUpdate("alcohol_drinks_per_week", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-purple-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-bold text-blue-gray-700 mb-2 block">Smoking Status</label>
              <div className="flex gap-2">
                {["never", "former", "current"].map((status) => (
                  <button
                    key={status}
                    onClick={() => handleUpdate("smoking_status", status)}
                    className={`flex-1 py-2 rounded-xl text-xs font-bold capitalize transition-all ${
                      lifestyle.smoking_status === status
                        ? "bg-purple-600 text-white shadow-sm"
                        : "bg-blue-gray-50 text-blue-gray-600 hover:bg-blue-gray-100"
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Environment & Habits */}
        <div className="bg-white p-6 rounded-2xl border border-blue-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-emerald-50 rounded-lg">
              <Shield className="w-5 h-5 text-emerald-500" />
            </div>
            <h3 className="text-lg font-bold text-blue-gray-900">Environment</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700 flex items-center gap-1">Toxin Exposure <span className="text-[10px] bg-blue-gray-100 px-1.5 py-0.5 rounded text-blue-gray-500">Air, Water, Mold</span></label>
                <span className="text-sm font-mono text-emerald-600 font-bold">{lifestyle.environmental_toxin_exposure}/10</span>
              </div>
              <input
                type="range" min={1} max={10} step={1}
                value={lifestyle.environmental_toxin_exposure}
                onChange={(e) => handleUpdate("environmental_toxin_exposure", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-emerald-500"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Sunlight Exposure</label>
                <span className="text-sm font-mono text-emerald-600 font-bold">{lifestyle.sunlight_mins_per_day} min/day</span>
              </div>
              <input
                type="range" min={0} max={120} step={10}
                value={lifestyle.sunlight_mins_per_day}
                onChange={(e) => handleUpdate("sunlight_mins_per_day", parseInt(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-emerald-500"
              />
            </div>

            <div className="space-y-2 md:col-span-2 max-w-md">
              <div className="flex justify-between">
                <label className="text-sm font-bold text-blue-gray-700">Screen Time</label>
                <span className="text-sm font-mono text-emerald-600 font-bold">{lifestyle.screen_time_hours} hrs/day</span>
              </div>
              <input
                type="range" min={0} max={16} step={0.5}
                value={lifestyle.screen_time_hours}
                onChange={(e) => handleUpdate("screen_time_hours", parseFloat(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none bg-blue-gray-100 accent-emerald-500"
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
