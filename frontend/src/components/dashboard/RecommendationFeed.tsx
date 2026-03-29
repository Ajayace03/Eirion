import { useWizardStore } from "../../store/wizardStore";
import { AnalysisResponse } from "../../types";
import { ArrowRight, CheckCircle2, FlaskConical, Stethoscope, ThumbsUp, ThumbsDown } from "lucide-react";

interface Props {
  result: AnalysisResponse;
}

export default function RecommendationFeed({ result }: Props) {
  const { recommendations } = result;
  const { adoptedRecs, toggleAdoptRec } = useWizardStore();

  const getIcon = (action_type: string) => {
    switch (action_type) {
      case "swap": return <ArrowRight className="w-5 h-5" />;
      case "reduce": return <CheckCircle2 className="w-5 h-5" />;
      case "add": return <FlaskConical className="w-5 h-5" />;
      case "consult": return <Stethoscope className="w-5 h-5" />;
      default: return <CheckCircle2 className="w-5 h-5" />;
    }
  };

  const getColor = (action_type: string) => {
    switch (action_type) {
      case "swap": return "text-blue-600 bg-blue-100";
      case "reduce": return "text-amber-600 bg-amber-100";
      case "add": return "text-emerald-600 bg-emerald-100";
      case "consult": return "text-purple-600 bg-purple-100";
      default: return "text-blue-gray-600 bg-blue-gray-100";
    }
  };

  const adoptedCount = recommendations.filter((r) => adoptedRecs.has(r.id)).length;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8 h-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-serif font-bold text-2xl text-blue-gray-900">Optimization Protocol</h3>
          {adoptedCount > 0 && (
            <p className="text-sm text-emerald-600 font-semibold mt-1">
              ✓ {adoptedCount} action{adoptedCount > 1 ? "s" : ""} adopted
            </p>
          )}
        </div>
        <span className="text-sm font-bold bg-blue-gray-100 text-blue-gray-600 px-3 py-1 rounded-full">
          {recommendations.length} Actions
        </span>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-12 text-blue-gray-400 border-2 border-dashed border-blue-gray-100 rounded-xl">
          Your stack is optimal. No critical recommendations.
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => {
            const adopted = adoptedRecs.has(rec.id);
            const isLowConfidence = rec.confidence < 0.7;
            return (
              <div
                key={rec.id}
                className={`p-5 rounded-xl border shadow-sm transition-all duration-200 ${
                  adopted
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-blue-gray-100 hover:shadow-md"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`mt-1 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${getColor(rec.action_type)}`}>
                    {getIcon(rec.action_type)}
                  </div>

                  <div className="flex-1 space-y-2">
                    <div className="flex justify-between items-start gap-4 flex-wrap">
                      <div className="space-y-1">
                        <h4 className="font-bold text-blue-gray-900 text-lg leading-tight">{rec.title}</h4>
                        {isLowConfidence && (
                          <span className="inline-block text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                            ⚠ Experimental — consult your physician
                          </span>
                        )}
                      </div>
                      {rec.expected_improvement.delta_index_now > 0 && (
                        <div className="text-right shrink-0">
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                            +{rec.expected_improvement.delta_index_now.toFixed(1)} pts now
                          </span>
                          {rec.expected_improvement.delta_index_year5 > 0 && (
                            <div className="text-xs text-blue-gray-400 mt-1 text-right">
                              +{rec.expected_improvement.delta_index_year5.toFixed(1)} at yr 5
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <p className="text-sm text-blue-gray-600 leading-relaxed">{rec.details}</p>

                    {rec.evidence_refs.length > 0 && (
                      <div className="pt-2 mt-2 border-t border-blue-gray-100 flex flex-wrap gap-2">
                        <span className="text-xs font-bold text-blue-gray-400 uppercase tracking-wider">Refs:</span>
                        {rec.evidence_refs.map((ref) => (
                          <span key={ref} className="text-xs text-blue-gray-500 bg-blue-gray-50 px-2 py-0.5 rounded border border-blue-gray-100">
                            {ref}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Adopt / Skip toggle */}
                    <div className="flex items-center gap-3 pt-3 mt-1 border-t border-blue-gray-100">
                      <button
                        onClick={() => toggleAdoptRec(rec.id)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                          adopted
                            ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                            : "bg-blue-gray-900 text-white hover:bg-blue-gray-700"
                        }`}
                      >
                        <ThumbsUp className="w-4 h-4" />
                        {adopted ? "Adopted ✓" : "Adopt This"}
                      </button>
                      {!adopted && (
                        <button
                          onClick={() => {/* Skip — just leaves unadopted */}}
                          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-blue-gray-400 hover:text-blue-gray-600 transition-colors"
                        >
                          <ThumbsDown className="w-4 h-4" />
                          Skip
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Phase 0 disclaimer */}
      <p className="text-xs text-blue-gray-400 mt-6 text-center border-t border-blue-gray-100 pt-4">
        Phase 0 — Rules-based prototype. Not medical advice. Consult a licensed physician before making changes.
      </p>
    </div>
  );
}
