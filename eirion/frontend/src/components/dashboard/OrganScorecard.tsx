// Organ Scorecard — 4-organ health index display
// Shows liver / kidney / cardiovascular / metabolic scores with pathway breakdown

import { OrganScore } from "../../types";

const ORGAN_META: Record<string, { icon: string; label: string; desc: string; color: string }> = {
  liver: {
    icon: "🫀",
    label: "Liver",
    desc: "Hepatic function, detox capacity, CYP450 load",
    color: "from-rose-500 to-red-600",
  },
  kidney: {
    icon: "🫘",
    label: "Kidneys",
    desc: "eGFR, renal clearance, drug accumulation",
    color: "from-indigo-500 to-blue-600",
  },
  cardiovascular: {
    icon: "❤️",
    label: "Cardiovascular",
    desc: "LDL burden, CRP, cardiac risk profile",
    color: "from-pink-500 to-rose-600",
  },
  metabolic: {
    icon: "⚗️",
    label: "Metabolic",
    desc: "HbA1c, insulin resistance, cortisol axis",
    color: "from-amber-500 to-orange-600",
  },
};

const RISK_CONFIG = {
  green: {
    label: "Optimal",
    bg: "bg-brand-green/10",
    border: "border-brand-green/30",
    text: "text-brand-green",
    bar: "bg-brand-green",
    glow: "shadow-brand-green/20",
  },
  amber: {
    label: "Caution",
    bg: "bg-brand-amber/10",
    border: "border-brand-amber/30",
    text: "text-brand-amber",
    bar: "bg-brand-amber",
    glow: "shadow-brand-amber/20",
  },
  red: {
    label: "Risk",
    bg: "bg-brand-red/10",
    border: "border-brand-red/30",
    text: "text-brand-red",
    bar: "bg-brand-red",
    glow: "shadow-brand-red/20",
  },
};

function ScoreRing({ score, risk }: { score: number; risk: "green" | "amber" | "red" }) {
  const cfg = RISK_CONFIG[risk];
  const r = 28;
  const circumference = 2 * Math.PI * r;
  const dashOffset = circumference * (1 - score / 100);

  return (
    <div className="relative w-20 h-20">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 64 64">
        {/* Track */}
        <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="6" className="text-blue-gray-100" />
        {/* Fill */}
        <circle
          cx="32" cy="32" r={r}
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className={`${cfg.bar} transition-all duration-1000`}
          style={{ stroke: "currentColor" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-lg font-black font-mono ${cfg.text}`}>{Math.round(score)}</span>
        <span className="text-[9px] text-blue-gray-400 font-medium">/100</span>
      </div>
    </div>
  );
}

function PathwayBadge({ pathway }: { pathway: string }) {
  const label = pathway.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <span className="inline-block text-[10px] px-2 py-0.5 rounded-full bg-blue-gray-100 text-blue-gray-600 font-medium">
      {label}
    </span>
  );
}

export function OrganCard({ organ_score }: { organ_score: OrganScore }) {
  const meta = ORGAN_META[organ_score.organ] || ORGAN_META.liver;
  const cfg = RISK_CONFIG[organ_score.risk_level];
  const delta5yr = organ_score.projected_5yr ? organ_score.score - organ_score.projected_5yr : 0;

  return (
    <div
      className={`rounded-2xl border ${cfg.border} ${cfg.bg} p-5 flex flex-col gap-3 shadow-sm ${cfg.glow}`}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${meta.color} flex items-center justify-center text-lg`}>
          {meta.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-black text-blue-gray-900">{meta.label}</p>
          <p className="text-[10px] text-blue-gray-500 truncate">{meta.desc}</p>
        </div>
        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${cfg.text} ${cfg.bg} border ${cfg.border}`}>
          {cfg.label}
        </span>
      </div>

      {/* Score row */}
      <div className="flex items-center gap-4">
        <ScoreRing score={organ_score.score} risk={organ_score.risk_level} />
        <div className="flex-1 space-y-1.5">
          {/* Progress bar */}
          <div className="h-2 w-full bg-blue-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full ${cfg.bar} rounded-full transition-all duration-1000`}
              style={{ width: `${organ_score.score}%` }}
            />
          </div>
          {organ_score.primary_driver && (
            <p className="text-[11px] text-blue-gray-600">
              <span className="font-bold">Top driver:</span> {organ_score.primary_driver}
            </p>
          )}
          {organ_score.projected_5yr !== undefined && (
            <p className={`text-[11px] font-bold ${delta5yr > 5 ? "text-brand-red" : "text-blue-gray-500"}`}>
              {delta5yr > 0 ? `↓ ${delta5yr.toFixed(1)} pts over 5 years` : `→ Stable over 5 years`}
            </p>
          )}
        </div>
      </div>

      {/* Active pathways */}
      {organ_score.active_pathways && organ_score.active_pathways.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1 border-t border-blue-gray-100/50">
          {organ_score.active_pathways.map((p) => (
            <PathwayBadge key={p} pathway={p} />
          ))}
        </div>
      )}
    </div>
  );
}

export function OrganScorecard({ organ_scores }: { organ_scores: OrganScore[] }) {
  if (!organ_scores || organ_scores.length === 0) return null;

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-6 bg-brand-green rounded-full" />
        <h2 className="text-lg font-black text-blue-gray-900">Multi-Organ Health Index</h2>
        <span className="ml-auto text-[10px] text-blue-gray-400 font-medium bg-blue-gray-50 px-2.5 py-1 rounded-full">
          Knowledge Graph Engine — v2
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {organ_scores.map((os) => (
          <OrganCard key={os.organ} organ_score={os} />
        ))}
      </div>
    </section>
  );
}
