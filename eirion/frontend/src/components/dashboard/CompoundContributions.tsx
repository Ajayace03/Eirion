import { AnalysisResponse } from "../../types";
import { ShieldAlert, ShieldCheck } from "lucide-react";

interface Props {
  result: AnalysisResponse;
}

export default function CompoundContributions({ result }: Props) {
  const { contributions } = result;

  // Find max load to calculate width percentage properly
  const maxLoad = Math.max(...contributions.map((c) => Math.abs(c.load)), 10);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8">
      <h3 className="font-serif font-bold text-2xl text-blue-gray-900 mb-6">Load Breakdown</h3>

      <div className="space-y-6">
        {contributions.map((c) => {
          const widthPct = Math.min(100, (Math.abs(c.load) / maxLoad) * 100);
          const isHarmful = !c.is_protective && c.load > 0;
          
          return (
            <div key={c.compound_id} className="space-y-2">
              <div className="flex justify-between items-end">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-blue-gray-900">{c.name}</span>
                  {c.is_protective ? (
                    <ShieldCheck className="w-4 h-4 text-brand-green" />
                  ) : c.load >= 5 ? (
                    <ShieldAlert className="w-4 h-4 text-brand-red" />
                  ) : null}
                </div>
                <span className={`font-mono font-bold text-sm ${isHarmful ? "text-brand-amber" : "text-brand-green"}`}>
                  {isHarmful ? "+" : "-"}{Math.abs(c.load).toFixed(1)} stress
                </span>
              </div>
              
              <div className="relative h-3 w-full bg-blue-gray-100 rounded-full overflow-hidden">
                <div 
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ${
                    isHarmful ? (c.load >= 5 ? "bg-brand-red" : "bg-brand-amber") : "bg-brand-green"
                  }`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
              
              <p className="text-xs text-blue-gray-500 max-w-[90%] leading-snug">
                {c.reason}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
