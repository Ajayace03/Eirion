import { AnalysisResponse } from "../../types";
import { Activity, Beaker, Dna, ShieldAlert } from "lucide-react";

interface Props {
  result: AnalysisResponse;
}

export default function RiskSummaryCard({ result }: Props) {
  const { risk_summary, biological_age, polypharmacy_score } = result;
  
  const riskColors = {
    green: "text-brand-green bg-brand-green/10 border-brand-green/20",
    amber: "text-brand-amber bg-brand-amber/10 border-brand-amber/20",
    red: "text-brand-red bg-red-500/10 border-red-500/20",
  };

  const riskColor = riskColors[risk_summary.risk_level] || riskColors.amber;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8">
      
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-8 border-b border-blue-gray-100 pb-8">
        <div className="space-y-4 max-w-xl">
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border font-bold text-sm uppercase tracking-wider ${riskColor}`}>
            {risk_summary.risk_level === "red" ? <ShieldAlert className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
            {risk_summary.risk_level} Risk Level
          </div>
          <h2 className="text-4xl font-serif font-bold text-blue-gray-900 leading-tight">
            {risk_summary.headline}
          </h2>
        </div>

        <div className="flex flex-col items-center justify-center p-6 bg-blue-gray-900 text-white rounded-2xl min-w-[200px] shrink-0">
          <span className="text-sm font-bold text-blue-gray-400 uppercase tracking-widest mb-2">Liver Index</span>
          <div className="flex items-baseline gap-1">
            <span className="text-6xl font-bold font-serif">{Math.round(risk_summary.liver_index_now)}</span>
            <span className="text-xl text-blue-gray-400">/100</span>
          </div>
          <div className="mt-4 px-4 py-1.5 rounded-full bg-white/10 text-sm font-medium">
            ↓ {risk_summary.projected_drop_percent.toFixed(1)}% in 5 Yrs
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-6">
        <div className="flex items-center gap-4 p-4 rounded-xl bg-blue-50/50 border border-blue-100">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
            <Dna className="w-6 h-6" />
          </div>
          <div>
            <span className="text-sm text-blue-gray-500 font-bold uppercase tracking-wider block mb-0.5">Biological Age</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-blue-gray-900">{biological_age.toFixed(1)}</span>
              <span className="text-sm text-blue-gray-500">years</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 p-4 rounded-xl bg-purple-50/50 border border-purple-100">
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center text-purple-600">
            <Beaker className="w-6 h-6" />
          </div>
          <div>
            <span className="text-sm text-purple-900/60 font-bold uppercase tracking-wider block mb-0.5">Polypharmacy Score</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-purple-900">{polypharmacy_score}</span>
              <span className="text-sm text-purple-900/60">/100 load</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
