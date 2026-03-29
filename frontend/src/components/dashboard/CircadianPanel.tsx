import { RegimenItem } from "../../types";
import { Clock } from "lucide-react";

// Circadian dosing knowledge table
const CIRCADIAN_GUIDE: Record<string, {
  timing: string;
  window: string;
  reason: string;
  color: string;
}> = {
  ashwagandha: {
    timing: "Evening",
    window: "8–10 PM",
    reason: "Cortisol-lowering effect is most beneficial before sleep; reduces nighttime stress response.",
    color: "bg-indigo-50 border-indigo-100 text-indigo-700",
  },
  rhodiola: {
    timing: "Morning",
    window: "7–9 AM",
    reason: "Adaptogenic stimulation aligns with natural morning cortisol peak for maximum alertness benefit.",
    color: "bg-amber-50 border-amber-100 text-amber-700",
  },
  nac: {
    timing: "Morning",
    window: "With breakfast",
    reason: "Food enhances absorption and reduces GI upset. Morning dosing optimizes hepatic glutathione synthesis.",
    color: "bg-sky-50 border-sky-100 text-sky-700",
  },
  milk_thistle: {
    timing: "With meals",
    window: "Lunch or Dinner",
    reason: "Fat-soluble silymarin bioavailability increases 2-3× when taken with dietary fat.",
    color: "bg-green-50 border-green-100 text-green-700",
  },
  berberine: {
    timing: "Before meals",
    window: "15 min pre-meal",
    reason: "Pre-meal dosing activates AMPK before glucose surge, maximizing glycemic control effect.",
    color: "bg-orange-50 border-orange-100 text-orange-700",
  },
  nmn: {
    timing: "Morning",
    window: "7–9 AM (fasted)",
    reason: "NAD+ precursor activity follows circadian clock. Morning fasted dosing aligns with peak NAMPT expression.",
    color: "bg-purple-50 border-purple-100 text-purple-700",
  },
  curcumin: {
    timing: "With meals",
    window: "Lunch or Dinner",
    reason: "Lipophilic compound. Requires dietary fat for absorption — take with the largest meal of the day.",
    color: "bg-yellow-50 border-yellow-100 text-yellow-700",
  },
  coq10: {
    timing: "Morning",
    window: "With breakfast",
    reason: "Mitochondrial energetics need the ATP co-factor available early in the active metabolic window.",
    color: "bg-rose-50 border-rose-100 text-rose-700",
  },
  alpha_lipoic_acid: {
    timing: "Before meals",
    window: "30 min pre-meal",
    reason: "Taken fasted for maximum absorption. Acts as antioxidant across lipid and aqueous compartments.",
    color: "bg-teal-50 border-teal-100 text-teal-700",
  },
};

const TIME_ORDER = ["7–9 AM (fasted)", "7–9 AM", "With breakfast", "15 min pre-meal", "30 min pre-meal", "8–10 AM", "Lunch or Dinner", "8–10 PM"];

interface Props {
  regimen: RegimenItem[];
}

export default function CircadianPanel({ regimen }: Props) {
  const items = regimen
    .map((r) => {
      const guide = CIRCADIAN_GUIDE[r.compound_id];
      if (!guide) return null;
      return { ...guide, compound_id: r.compound_id, dose_mg: r.dose_mg };
    })
    .filter(Boolean) as Array<typeof CIRCADIAN_GUIDE[string] & { compound_id: string; dose_mg: number }>;

  const sorted = [...items].sort(
    (a, b) => TIME_ORDER.indexOf(a.window) - TIME_ORDER.indexOf(b.window)
  );

  if (sorted.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-blue-gray-900 rounded-xl flex items-center justify-center">
          <Clock className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-serif font-bold text-2xl text-blue-gray-900">Circadian Dosing Schedule</h3>
          <p className="text-sm text-blue-gray-500 mt-0.5">Optimal timing for your current supplement stack</p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((item) => (
          <div
            key={item.compound_id}
            className={`p-4 rounded-xl border ${item.color} transition-all hover:shadow-sm`}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-bold text-base capitalize">
                  {item.compound_id.replace(/_/g, " ")}
                </p>
                <p className="text-xs opacity-70">{item.dose_mg}mg</p>
              </div>
              <div className="text-right shrink-0 ml-3">
                <span className="text-xs font-bold uppercase tracking-wide opacity-60">{item.timing}</span>
                <p className="text-xs font-bold mt-0.5">{item.window}</p>
              </div>
            </div>
            <p className="text-xs leading-relaxed opacity-75 mt-2 border-t border-current/10 pt-2">
              {item.reason}
            </p>
          </div>
        ))}
      </div>

      <p className="text-xs text-blue-gray-400 mt-6 text-center">
        Circadian timing recommendations based on published pharmacokinetic data. Phase 1 feature.
      </p>
    </div>
  );
}
