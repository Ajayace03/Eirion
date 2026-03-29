// Pathway Chain Panel — shows compound→gene→pathway→organ mechanistic chains
// Drug-Drug Interaction Panel — flags DDIs with risk level and evidence

import { CompoundGeneChain, DDIFlag } from "../../types";

const RISK_COLORS = {
  high: "bg-brand-red/10 text-brand-red border-brand-red/30",
  moderate: "bg-brand-amber/10 text-brand-amber border-brand-amber/30",
  low: "bg-brand-green/10 text-brand-green border-brand-green/30",
};

const PHENOTYPE_CHIP_COLORS: Record<string, string> = {
  poor: "bg-brand-red text-white",
  intermediate: "bg-brand-amber text-white",
  normal: "bg-brand-green text-white",
  ultra_rapid: "bg-blue-500 text-white",
  reduced: "bg-brand-amber text-white",
  unknown: "bg-blue-gray-300 text-white",
};

function MultiplierBadge({ multiplier }: { multiplier: number }) {
  const isHigh = multiplier > 1.2;
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isHigh ? "bg-brand-red/10 text-brand-red" : "bg-blue-gray-100 text-blue-gray-500"}`}>
      {multiplier.toFixed(1)}×
    </span>
  );
}

function ChainItem({ chain }: { chain: string }) {
  if (chain.startsWith("→")) {
    return (
      <div className="flex items-start gap-2 ml-4">
        <span className="text-blue-gray-300 font-bold mt-0.5">↓</span>
        <p className="text-xs text-blue-gray-600 leading-tight">{chain.replace("→ ", "")}</p>
      </div>
    );
  }
  return <p className="text-xs font-bold text-blue-gray-800">{chain}</p>;
}

function CompoundChainCard({ chain }: { chain: CompoundGeneChain }) {
  const hasIssues = chain.gene_interactions.some((g) => g.multiplier > 1.2);

  return (
    <div className={`rounded-xl border p-4 space-y-3 ${hasIssues ? "border-amber-200 bg-amber-50/30" : "border-blue-gray-100 bg-white"}`}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <p className="text-sm font-bold text-blue-gray-900 flex-1">{chain.display_name}</p>
        {hasIssues && (
          <span className="text-[10px] bg-brand-amber/10 text-brand-amber border border-brand-amber/30 px-2 py-0.5 rounded-full font-bold">
            ⚠ Gene Interaction
          </span>
        )}
      </div>

      {/* Gene interactions */}
      {chain.gene_interactions.length > 0 && (
        <div className="space-y-1.5">
          {chain.gene_interactions.map((gi, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="font-mono font-bold text-blue-gray-700 w-16">{gi.gene}</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${PHENOTYPE_CHIP_COLORS[gi.phenotype] || PHENOTYPE_CHIP_COLORS.unknown}`}>
                {gi.phenotype}
              </span>
              <MultiplierBadge multiplier={gi.multiplier} />
              {gi.evidence && (
                <span className="text-[10px] text-blue-gray-400 truncate flex-1" title={gi.evidence}>
                  {gi.evidence.split("—")[0].trim()}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pathway chain */}
      {chain.pathway_chain.length > 0 && (
        <div className="space-y-1 pt-2 border-t border-blue-gray-100">
          {chain.pathway_chain.map((c, i) => (
            <ChainItem key={i} chain={c} />
          ))}
        </div>
      )}

      {/* Organ impacts */}
      {Object.keys(chain.organ_impacts).length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-blue-gray-100">
          {Object.entries(chain.organ_impacts).map(([organ, impact]) => (
            <span
              key={organ}
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${impact < 0 ? "bg-brand-green/10 text-brand-green" : "bg-blue-gray-100 text-blue-gray-600"}`}
            >
              {organ}: {impact > 0 ? "+" : ""}{impact.toFixed(1)} load pts
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function PathwayChainPanel({ chains, pathways }: { chains: CompoundGeneChain[]; pathways?: string[] }) {
  if (!chains || chains.length === 0) return null;

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-6 bg-blue-500 rounded-full" />
        <h2 className="text-lg font-black text-blue-gray-900">Compound → Gene → Pathway</h2>
        <span className="ml-auto text-[10px] text-blue-gray-400">
          {chains.length} compounds · {pathways?.length ?? 0} active pathways
        </span>
      </div>

      {pathways && pathways.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {pathways.map((p) => (
            <span key={p} className="text-[10px] px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">
              {p.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-3">
        {chains.map((chain) => (
          <CompoundChainCard key={chain.compound_id} chain={chain} />
        ))}
      </div>
    </section>
  );
}

export function DDIPanel({ flags }: { flags: DDIFlag[] }) {
  if (!flags || flags.length === 0) return null;

  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-6 bg-brand-red rounded-full" />
        <h2 className="text-lg font-black text-blue-gray-900">Drug-Drug Interactions</h2>
        <span className={`ml-auto text-xs font-bold px-2.5 py-1 rounded-full ${flags.some((f) => f.risk_level === "high") ? "bg-brand-red/10 text-brand-red" : "bg-brand-amber/10 text-brand-amber"}`}>
          {flags.length} interaction{flags.length > 1 ? "s" : ""} detected
        </span>
      </div>

      <div className="space-y-3">
        {flags.map((flag, i) => (
          <div key={i} className={`rounded-xl border p-4 space-y-2 ${RISK_COLORS[flag.risk_level]}`}>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${RISK_COLORS[flag.risk_level]}`}>
                {flag.risk_level} risk
              </span>
              <p className="text-sm font-black text-blue-gray-900">
                {flag.compound_a.replace(/_/g, " ")} + {flag.compound_b.replace(/_/g, " ")}
              </p>
            </div>
            <p className="text-xs text-blue-gray-700 leading-relaxed">{flag.mechanism}</p>
            <div className="flex items-start gap-1.5 pt-1">
              <span className="text-[10px] text-brand-green font-bold shrink-0">→ Rec:</span>
              <p className="text-xs text-blue-gray-600">{flag.recommendation}</p>
            </div>
            {flag.evidence && (
              <p className="text-[10px] text-blue-gray-400">{flag.evidence}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
