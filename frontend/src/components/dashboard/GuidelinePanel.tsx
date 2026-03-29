// GuidelinePanel — per-organ evidence-based clinical guideline recommendations
// Shown below multi-timeframe charts, grounded in EASL/KDIGO/AHA-ACC/ADA

import { MultiOrganProjection, OrganTrajectory } from "../../types";

const ORGAN_ICONS: Record<string, string> = {
  liver: "🫀", kidney: "🫘", cardiovascular: "❤️", metabolic: "⚗️",
};

const ORGAN_LABELS: Record<string, string> = {
  liver: "Liver (EASL)", kidney: "Kidney (KDIGO)",
  cardiovascular: "Cardiovascular (AHA/ACC)", metabolic: "Metabolic (ADA)",
};

const RISK_PILL: Record<string, string> = {
  green: "bg-brand-green/10 text-brand-green border-brand-green/20",
  amber: "bg-brand-amber/10 text-brand-amber border-brand-amber/20",
  red:   "bg-brand-red/10 text-brand-red border-brand-red/20",
};

function GuidelineCard({ traj }: { traj: OrganTrajectory }) {
  if (!traj.guideline_rec) return null;

  const best10 = traj.improvement_at?.["10yr"] ?? 0;
  const best5  = traj.improvement_at?.["5yr"]  ?? 0;

  return (
    <div className="rounded-2xl border border-blue-gray-100 bg-white p-5 space-y-3">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="text-xl shrink-0 mt-0.5">{ORGAN_ICONS[traj.organ]}</div>
        <div className="flex-1">
          <p className="text-sm font-black text-blue-gray-900">{ORGAN_LABELS[traj.organ]}</p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${RISK_PILL[traj.risk_level]}`}>
              Score {Math.round(traj.current_score)} — {traj.risk_level.toUpperCase()}
            </span>
            {best5 > 1 && (
              <span className="text-[10px] text-brand-green font-bold">
                +{best5.toFixed(0)} pts gain at 5yr if optimized
              </span>
            )}
            {best10 > 1 && (
              <span className="text-[10px] text-blue-gray-400">
                +{best10.toFixed(0)} at 10yr
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Guideline text */}
      <div className="bg-blue-gray-50/60 rounded-xl px-4 py-3">
        <p className="text-xs text-blue-gray-700 leading-relaxed">{traj.guideline_rec}</p>
      </div>

      {/* Source */}
      {traj.guideline_source && (
        <p className="text-[10px] text-blue-gray-400 font-medium">
          📚 {traj.guideline_source}
        </p>
      )}

      {/* Horizon snapshot */}
      <div className="grid grid-cols-5 gap-1 pt-1 border-t border-blue-gray-50 text-center">
        {["1yr", "2yr", "5yr", "10yr", "lifetime"].map((tf) => (
          <div key={tf}>
            <p className="text-[9px] text-blue-gray-400 font-medium">{tf}</p>
            <p className="text-xs font-black text-blue-gray-700">
              {Math.round(traj.scores_at?.[tf] ?? traj.current_score)}
            </p>
            {(traj.improvement_at?.[tf] ?? 0) > 0.5 && (
              <p className="text-[9px] text-brand-green font-bold">
                +{Math.round(traj.improvement_at[tf])}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function GuidelinePanel({ projection }: { projection: MultiOrganProjection }) {
  const organs = ["liver", "kidney", "cardiovascular", "metabolic"] as const;

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-6 bg-purple-500 rounded-full" />
        <h2 className="text-lg font-black text-blue-gray-900">Clinical Guidelines</h2>
        <span className="ml-auto text-[10px] text-blue-gray-400 font-medium bg-blue-gray-50 px-2.5 py-1 rounded-full">
          EASL · KDIGO · AHA/ACC · ADA 2023–2024
        </span>
      </div>

      {/* Cross-organ summary banner */}
      {projection.organ_years_gained && projection.organ_years_gained > 0.5 && (
        <div className="mb-4 flex items-center gap-3 p-4 rounded-2xl bg-gradient-to-r from-brand-green/10 to-blue-500/5 border border-brand-green/20">
          <div className="text-2xl">✨</div>
          <div>
            <p className="text-sm font-black text-blue-gray-900">
              {projection.organ_years_gained} healthy organ-years at stake
            </p>
            <p className="text-xs text-blue-gray-600">
              Greatest gain opportunity:{" "}
              <strong className="capitalize">{projection.max_gain_organ}</strong>
              {" "}(+{projection.max_gain_pct?.toFixed(0)} index pts at 10yr)
              {" "}if all recommendations are adopted.
            </p>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        {organs.map((organ) => (
          <GuidelineCard key={organ} traj={projection[organ]} />
        ))}
      </div>
    </section>
  );
}
