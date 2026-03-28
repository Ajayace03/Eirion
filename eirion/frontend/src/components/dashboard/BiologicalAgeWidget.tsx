import { useEffect } from "react";
import { AnalysisResponse } from "../../types";
import { Activity, TrendingDown, Zap } from "lucide-react";
import toast from "react-hot-toast";

interface Props {
  result: AnalysisResponse;
}

const RISK_TOASTS: Array<{
  condition: (result: AnalysisResponse) => boolean;
  message: string;
  icon: string;
}> = [
  {
    condition: (result) =>
      result.risk_summary.risk_level === "red",
    message: "⚠️ High Risk Detected — Your liver index indicates significant stress. Follow the optimization protocol immediately.",
    icon: "🚨",
  },
  {
    condition: (result) =>
      result.contributions.some((c) => c.compound_id === "ashwagandha") &&
      result.contributions.some((c) => c.load > 10 && !c.is_protective),
    message: "⚠️ Ashwagandha + CYP2D6 interaction detected — reduced metabolic clearance increasing hepatic load.",
    icon: "🧬",
  },
  {
    condition: (result) =>
      result.polypharmacy_score >= 60,
    message: `📦 High polypharmacy score — stacking multiple CYP substrates compounds toxicity risk.`,
    icon: "💊",
  },
];

export default function RiskToastTrigger({ result }: Props) {
  useEffect(() => {
    let delay = 800;
    for (const rule of RISK_TOASTS) {
      if (rule.condition(result)) {
        const msg = rule.message;
        const isRed = result.risk_summary.risk_level === "red";
        setTimeout(() => {
          toast(msg, {
            icon: rule.icon,
            duration: 8000,
            style: {
              background: isRed ? "#fef2f2" : "#fffbeb",
              color: isRed ? "#991b1b" : "#92400e",
              border: `1px solid ${isRed ? "#fecaca" : "#fde68a"}`,
              fontWeight: "600",
              fontSize: "0.875rem",
              maxWidth: "420px",
              padding: "14px 18px",
              borderRadius: "14px",
              boxShadow: "0 4px 24px rgba(0,0,0,0.1)",
            },
          });
        }, delay);
        delay += 1200;
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result.risk_summary.risk_level]);

  return null; // Pure-side-effect component
}

// ─────────────────────────────────────────────────────────────────────────
// Biological Age Widget
// ─────────────────────────────────────────────────────────────────────────

interface BioAgeProps {
  biologicalAge: number;
  chronologicalAge: number;
  riskLevel: "green" | "amber" | "red";
  optimizedProjection?: number;
}

export function BiologicalAgeWidget({
  biologicalAge,
  chronologicalAge,
  riskLevel,
  optimizedProjection,
}: BioAgeProps) {
  const delta = +(biologicalAge - chronologicalAge).toFixed(1);
  const isOlder = delta > 0;

  const ringColor = {
    green: "stroke-emerald-500",
    amber: "stroke-amber-500",
    red: "stroke-red-500",
  }[riskLevel];

  const textColor = {
    green: "text-emerald-600",
    amber: "text-amber-600",
    red: "text-red-600",
  }[riskLevel];

  const bgColor = {
    green: "bg-emerald-50 border-emerald-100",
    amber: "bg-amber-50 border-amber-100",
    red: "bg-red-50 border-red-100",
  }[riskLevel];

  // SVG arc for the ring
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  // Clamp bio age ratio between 0-1 for the ring fill
  const ratio = Math.min(1, Math.max(0, (120 - biologicalAge) / 80));
  const dashOffset = circumference * (1 - ratio);

  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-serif font-bold text-2xl text-blue-gray-900">Biological Age</h3>
          <p className="text-blue-gray-500 text-sm mt-1">Based on your liver stress index</p>
        </div>
        <Activity className="w-6 h-6 text-blue-gray-300" />
      </div>

      <div className="flex items-center gap-8">
        {/* SVG Ring */}
        <div className="relative shrink-0 w-36 h-36 flex items-center justify-center">
          <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 140 140">
            <circle cx="70" cy="70" r={radius} strokeWidth="10" className="stroke-blue-gray-100 fill-none" />
            <circle
              cx="70" cy="70" r={radius}
              strokeWidth="10"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              className={`${ringColor} transition-all duration-1000`}
            />
          </svg>
          <div className="text-center z-10">
            <span className={`text-4xl font-bold font-serif ${textColor}`}>{biologicalAge.toFixed(0)}</span>
            <span className="block text-xs text-blue-gray-400 font-semibold uppercase tracking-wide mt-1">bio years</span>
          </div>
        </div>

        {/* Stats column */}
        <div className="flex-1 space-y-4">
          <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${bgColor}`}>
            <span className="text-sm font-bold text-blue-gray-600">Chronological Age</span>
            <span className="font-bold text-blue-gray-900">{chronologicalAge} yrs</span>
          </div>

          <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${bgColor}`}>
            <span className="text-sm font-bold text-blue-gray-600">Age Gap</span>
            <span className={`font-bold text-base flex items-center gap-1 ${isOlder ? textColor : "text-emerald-600"}`}>
              {isOlder ? <TrendingDown className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
              {isOlder ? `+${delta} older` : `${Math.abs(delta)} younger`}
            </span>
          </div>

          {optimizedProjection !== undefined && (
            <div className="flex items-center justify-between px-4 py-3 rounded-xl border bg-emerald-50 border-emerald-100">
              <span className="text-sm font-bold text-emerald-700">Optimized (5yr)</span>
              <span className="font-bold text-emerald-700 text-base">
                {optimizedProjection.toFixed(1)} yrs
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
