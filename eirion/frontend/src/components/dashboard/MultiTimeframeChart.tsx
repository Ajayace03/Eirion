// MultiTimeframeChart — animated multi-organ, multi-timeframe projection
// Shows current path vs optimized path with confidence band
// Tabs: 1yr · 2yr · 5yr · 10yr · Lifetime
// Organs: Liver · Kidney · Cardiovascular · Metabolic

import { useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from "recharts";
import { MultiOrganProjection, OrganTrajectory } from "../../types";

const TIMEFRAMES = ["1yr", "2yr", "5yr", "10yr", "lifetime"] as const;
type Timeframe = typeof TIMEFRAMES[number];

const ORGANS = ["liver", "kidney", "cardiovascular", "metabolic"] as const;
type Organ = typeof ORGANS[number];

const ORGAN_META: Record<Organ, { icon: string; label: string; color: string }> = {
  liver:          { icon: "🫀", label: "Liver",          color: "#ef4444" },
  kidney:         { icon: "🫘", label: "Kidneys",        color: "#6366f1" },
  cardiovascular: { icon: "❤️", label: "Cardiovascular", color: "#ec4899" },
  metabolic:      { icon: "⚗️", label: "Metabolic",      color: "#f59e0b" },
};



const RISK_BG: Record<string, string> = {
  green: "bg-brand-green/10 text-brand-green border-brand-green/30",
  amber: "bg-brand-amber/10 text-brand-amber border-brand-amber/30",
  red:   "bg-brand-red/10 text-brand-red border-brand-red/30",
};

function ScoreDelta({
  current, optimized, label,
}: { current: number; optimized: number; label: string }) {
  const delta = optimized - current;
  return (
    <div className="text-center">
      <p className="text-[10px] text-blue-gray-500 font-medium">{label}</p>
      <p className="text-sm font-black text-blue-gray-900">{Math.round(current)}</p>
      {delta > 0.5 && (
        <p className="text-[10px] text-brand-green font-bold">+{delta.toFixed(1)} opt</p>
      )}
    </div>
  );
}

interface ChartPoint {
  label: string;
  score: number;
  optimized: number;
  upper: number;
  lower: number;
}

function prepareChartData(trajectory: OrganTrajectory, timeframe: Timeframe): ChartPoint[] {
  const series = trajectory.timeframes[timeframe] || [];
  return series.map((p) => ({
    label: p.label,
    score: Number(p.score.toFixed(1)),
    optimized: Number(p.optimized_score.toFixed(1)),
    upper: Number(Math.min(98, p.score + p.confidence_band).toFixed(1)),
    lower: Number(Math.max(10, p.score - p.confidence_band).toFixed(1)),
  }));
}

function OrganChart({ trajectory }: { trajectory: OrganTrajectory }) {
  const [timeframe, setTimeframe] = useState<Timeframe>("5yr");
  const data = prepareChartData(trajectory, timeframe);
  const meta = ORGAN_META[trajectory.organ as Organ];
  const riskCfg = RISK_BG[trajectory.risk_level];
  const improvement = trajectory.improvement_at[timeframe] ?? 0;

  return (
    <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center text-base shrink-0"
          style={{ background: `${meta.color}18` }}
        >
          {meta.icon}
        </div>
        <div className="flex-1">
          <p className="text-sm font-black text-blue-gray-900">{meta.label}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${riskCfg}`}>
              {trajectory.risk_level.toUpperCase()}
            </span>
            <span className="text-[11px] text-blue-gray-500 font-medium">
              Now: {trajectory.current_score}
            </span>
          </div>
        </div>
        {improvement > 1 && (
          <div className="text-right shrink-0">
            <p className="text-xs font-black text-brand-green">+{improvement.toFixed(0)} pts</p>
            <p className="text-[10px] text-blue-gray-400">if adopted</p>
          </div>
        )}
      </div>

      {/* Timeframe tabs */}
      <div className="flex gap-1">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`flex-1 py-1.5 text-[10px] font-bold rounded-xl transition-all ${
              timeframe === tf
                ? "bg-blue-gray-900 text-white shadow-sm"
                : "text-blue-gray-500 hover:bg-blue-gray-50"
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad_main_${trajectory.organ}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={meta.color} stopOpacity={0.15} />
                <stop offset="95%" stopColor={meta.color} stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id={`grad_opt_${trajectory.organ}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" />
            <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 11, borderRadius: 10, border: "1px solid #e2e8f0" }}
              formatter={(val, name) => {
                const v = typeof val === "number" ? val : Number(val);
                const label = name === "score" ? "Current path" : name === "optimized" ? "Optimized" : String(name);
                return [`${v.toFixed(0)}/100`, label];
              }}
            />
            {/* Confidence band */}
            <Area type="monotone" dataKey="upper" stroke="none" fill={`url(#grad_main_${trajectory.organ})`} fillOpacity={0.4} dot={false} legendType="none" />
            <Area type="monotone" dataKey="lower" stroke="none" fill="white" fillOpacity={1} dot={false} legendType="none" />
            {/* Zone lines */}
            <ReferenceLine y={75} stroke="#10b981" strokeDasharray="4 3" strokeWidth={1} label={{ value: "Optimal", fill: "#10b981", fontSize: 8, position: "insideRight" }} />
            <ReferenceLine y={55} stroke="#f59e0b" strokeDasharray="4 3" strokeWidth={1} label={{ value: "Caution", fill: "#f59e0b", fontSize: 8, position: "insideRight" }} />
            {/* Lines */}
            <Area type="monotone" dataKey="score" stroke={meta.color} strokeWidth={2} fill="none" dot={false} name="score" />
            <Area type="monotone" dataKey="optimized" stroke="#10b981" strokeWidth={2} strokeDasharray="6 3" fill={`url(#grad_opt_${trajectory.organ})`} dot={false} name="optimized" />
            <Legend
              wrapperStyle={{ fontSize: 9, paddingTop: 4 }}
              formatter={(val) => val === "score" ? "Current path" : "Optimized"}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Horizon summary row */}
      <div className="grid grid-cols-5 gap-1 pt-2 border-t border-blue-gray-50">
        {TIMEFRAMES.map((tf) => (
          <ScoreDelta
            key={tf}
            label={tf}
            current={trajectory.scores_at[tf] ?? trajectory.current_score}
            optimized={trajectory.optimized_at[tf] ?? trajectory.optimized_now}
          />
        ))}
      </div>
    </div>
  );
}

export function MultiTimeframeChart({ projection }: { projection: MultiOrganProjection }) {
  const [activeOrgan, setActiveOrgan] = useState<Organ>("liver");
  const trajectory = projection[activeOrgan];

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="w-1 h-6 bg-indigo-500 rounded-full shrink-0" />
        <h2 className="text-lg font-black text-blue-gray-900">Multi-Organ Projections</h2>

        {/* Cross-organ summary badges */}
        {projection.organ_years_gained && (
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] text-brand-green font-bold bg-brand-green/10 px-2.5 py-1 rounded-full border border-brand-green/20">
              +{projection.organ_years_gained} healthy organ-years if optimized
            </span>
          </div>
        )}
      </div>

      {/* Organ selector pills */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {ORGANS.map((organ) => {
          const mt = ORGAN_META[organ];
          const traj = projection[organ];
          const isActive = activeOrgan === organ;
          return (
            <button
              key={organ}
              onClick={() => setActiveOrgan(organ)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all border ${
                isActive
                  ? "bg-blue-gray-900 text-white border-blue-gray-900 shadow"
                  : "bg-white text-blue-gray-600 border-blue-gray-200 hover:border-blue-gray-400"
              }`}
            >
              <span>{mt.icon}</span>
              <span>{mt.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full font-black ${
                  isActive ? "bg-white/20 text-white" : RISK_BG[traj.risk_level]
                }`}
              >
                {Math.round(traj.current_score)}
              </span>
            </button>
          );
        })}
      </div>

      {/* Single organ detailed chart */}
      <OrganChart trajectory={trajectory} />
    </section>
  );
}

export function AllOrgansGrid({ projection }: { projection: MultiOrganProjection }) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-6 bg-indigo-500 rounded-full" />
        <h2 className="text-lg font-black text-blue-gray-900">All Organ Trajectories</h2>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        {ORGANS.map((organ) => (
          <OrganChart key={organ} trajectory={projection[organ]} />
        ))}
      </div>
    </section>
  );
}
