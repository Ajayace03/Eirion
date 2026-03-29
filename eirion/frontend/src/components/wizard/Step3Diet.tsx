import { useWizardStore } from "../../store/wizardStore";

const DIET_TYPES = [
  {
    id: "omnivore",
    label: "Omnivore",
    icon: "🥩",
    desc: "Mixed plant & animal",
  },
  {
    id: "vegetarian",
    label: "Vegetarian",
    icon: "🥗",
    desc: "No meat, includes dairy",
  },
  {
    id: "vegan",
    label: "Vegan",
    icon: "🌱",
    desc: "Fully plant-based",
  },
  {
    id: "keto",
    label: "Keto",
    icon: "🥑",
    desc: "High fat, low carb",
  },
  {
    id: "mediterranean",
    label: "Mediterranean",
    icon: "🫒",
    desc: "Fish, olive oil, veggies",
  },
] as const;

type DietType = (typeof DIET_TYPES)[number]["id"];

export default function Step3Diet() {
  const { food, updateFood } = useWizardStore();

  const cal = food.calories_per_day ?? 2000;
  const proc = food.processed_food_pct ?? 25;
  const meat = food.red_meat_g_per_week ?? 150;
  const fiber = food.fiber_g_per_day ?? 20;
  const diet = food.diet_type ?? "omnivore";

  const calColor =
    cal > 3000
      ? "text-brand-red"
      : cal > 2500
      ? "text-brand-amber"
      : "text-brand-green";
  const procColor =
    proc > 70
      ? "text-brand-red"
      : proc > 40
      ? "text-brand-amber"
      : "text-brand-green";
  const meatColor =
    meat > 500 ? "text-brand-red" : meat > 200 ? "text-brand-amber" : "text-brand-green";
  const fiberColor =
    fiber < 15
      ? "text-brand-red"
      : fiber < 25
      ? "text-brand-amber"
      : "text-brand-green";

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Diet & Nutrition
        </h2>
        <p className="text-blue-gray-600">
          Your food patterns directly influence liver inflammation and metabolic clearance.
        </p>
      </div>

      <div className="grid gap-8 max-w-xl mx-auto">

        {/* Diet Type Grid */}
        <div className="space-y-3">
          <label className="text-sm font-bold text-blue-gray-700">
            Dietary Pattern
          </label>
          <div className="grid grid-cols-5 gap-2">
            {DIET_TYPES.map((d) => (
              <button
                key={d.id}
                onClick={() => updateFood({ diet_type: d.id as DietType })}
                className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all text-center gap-1 ${
                  diet === d.id
                    ? "border-brand-green bg-brand-green/5 shadow-sm"
                    : "border-blue-gray-200 hover:border-blue-gray-400 bg-white"
                }`}
              >
                <span className="text-2xl">{d.icon}</span>
                <span
                  className={`text-xs font-bold leading-tight ${
                    diet === d.id ? "text-brand-green" : "text-blue-gray-700"
                  }`}
                >
                  {d.label}
                </span>
                <span className="text-[10px] text-blue-gray-400 leading-tight hidden sm:block">
                  {d.desc}
                </span>
              </button>
            ))}
          </div>
          {diet === "mediterranean" && (
            <p className="text-xs text-brand-green font-medium bg-brand-green/5 border border-brand-green/20 rounded-lg px-3 py-2">
              ✓ Best evidence for liver protection — reduces NAFLD risk by ~39%
            </p>
          )}
          {diet === "keto" && (
            <p className="text-xs text-brand-amber font-medium bg-brand-amber/5 border border-brand-amber/20 rounded-lg px-3 py-2">
              ⚠ High saturated fat increases hepatic processing load in some individuals
            </p>
          )}
        </div>

        {/* Calories */}
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">
              Daily Calories
            </label>
            <span className={`text-sm font-mono font-bold ${calColor}`}>
              {cal.toLocaleString()} kcal/day
            </span>
          </div>
          <input
            type="range"
            min="1200"
            max="4000"
            step="50"
            className="w-full accent-brand-green cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={cal}
            onChange={(e) =>
              updateFood({ calories_per_day: parseInt(e.target.value) })
            }
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>1,200</span>
            <span className="text-brand-green">Optimal 1,800–2,200</span>
            <span>4,000+</span>
          </div>
        </div>

        {/* Processed Food % */}
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">
              Ultra-Processed Foods
            </label>
            <span className={`text-sm font-mono font-bold ${procColor}`}>
              {proc}% of diet
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            className="w-full accent-brand-amber cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={proc}
            onChange={(e) =>
              updateFood({ processed_food_pct: parseInt(e.target.value) })
            }
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>0% (whole foods)</span>
            <span>Target &lt;20%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Fiber */}
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">
              Dietary Fiber
            </label>
            <span className={`text-sm font-mono font-bold ${fiberColor}`}>
              {fiber} g/day
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="60"
            step="1"
            className="w-full accent-brand-green cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={fiber}
            onChange={(e) =>
              updateFood({ fiber_g_per_day: parseInt(e.target.value) })
            }
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>Critical &lt;15g</span>
            <span className="text-brand-green">Target ≥25g</span>
            <span>60g</span>
          </div>
        </div>

        {/* Red Meat */}
        <div className="space-y-3">
          <div className="flex justify-between items-end">
            <label className="text-sm font-bold text-blue-gray-700">
              Red & Processed Meat
            </label>
            <span className={`text-sm font-mono font-bold ${meatColor}`}>
              {meat} g/week
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1000"
            step="25"
            className="w-full accent-brand-red cursor-pointer h-2 bg-blue-gray-100 rounded-lg appearance-none"
            value={meat}
            onChange={(e) =>
              updateFood({ red_meat_g_per_week: parseInt(e.target.value) })
            }
          />
          <div className="flex justify-between text-xs text-blue-gray-400 font-medium px-1">
            <span>None</span>
            <span>Limit &lt;300g</span>
            <span>1,000g+</span>
          </div>
        </div>
      </div>
    </div>
  );
}
