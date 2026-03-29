import { useWizardStore } from "../../store/wizardStore";
import { AlertTriangle } from "lucide-react";

const GENE_ROWS = [
  { field: "cyp2d6_metabolizer", label: "CYP2D6", note: "Metabolizes ashwagandha, SSRIs, codeine, many herbs" },
  { field: "cyp2c19_metabolizer", label: "CYP2C19", note: "PPIs, clopidogrel, some antidepressants" },
  { field: "cyp3a4_metabolizer", label: "CYP3A4", note: "~50% of all drugs — statins, curcumin, CoQ10" },
  { field: "cyp2c9_metabolizer", label: "CYP2C9", note: "NSAIDs, warfarin, losartan" },
  { field: "cyp1a2_metabolizer", label: "CYP1A2", note: "Caffeine, melatonin, olanzapine" },
];

const TRANSPORTER_ROWS = [
  { field: "slco1b1_function", label: "SLCO1B1", note: "Statin hepatic uptake — reduced function ↑ myopathy risk" },
  { field: "ugt1a1_function", label: "UGT1A1", note: "Bilirubin conjugation — relevant for irinotecan, some supplements" },
];

const MTHFR_ROWS = [
  { field: "mthfr_c677t", label: "MTHFR C677T", note: "Folate/B12 metabolism — homozygous reduces by ~70%" },
  { field: "mthfr_a1298c", label: "MTHFR A1298C", note: "Secondary folate variant — compound heterozygosity matters" },
];

const CYP_OPTIONS = ["unknown", "poor", "intermediate", "normal", "ultra_rapid"];
const FUNCTION_OPTIONS = ["unknown", "normal", "reduced", "poor"];
const MTHFR_OPTIONS = ["unknown", "normal", "heterozygous", "homozygous"];

const PHENOTYPE_COLORS: Record<string, string> = {
  poor: "text-brand-red",
  intermediate: "text-brand-amber",
  normal: "text-brand-green",
  ultra_rapid: "text-blue-600",
  reduced: "text-brand-amber",
  heterozygous: "text-brand-amber",
  homozygous: "text-brand-red",
  unknown: "text-blue-gray-400",
};

function GeneRow({ field, label, note, options }: { field: string; label: string; note: string; options: string[] }) {
  const { genetics, updateGenetics } = useWizardStore();
  const val = (genetics as any)[field] ?? "unknown";
  const isRisk = val === "poor" || val === "homozygous" || val === "reduced";

  return (
    <div className={`flex items-start gap-4 py-3.5 border-b border-blue-gray-50 last:border-0 ${isRisk ? "bg-amber-50/40 -mx-2 px-2 rounded-lg" : ""}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-bold text-blue-gray-900 font-mono">{label}</p>
          {isRisk && <AlertTriangle className="w-3.5 h-3.5 text-brand-amber" />}
        </div>
        <p className="text-xs text-blue-gray-500 mt-0.5 leading-tight">{note}</p>
      </div>
      <select
        className={`px-3 py-1.5 rounded-xl border border-blue-gray-200 text-sm font-bold capitalize focus:outline-none focus:ring-2 focus:ring-brand-green/40 min-w-[140px] ${PHENOTYPE_COLORS[val] || ""}`}
        value={val}
        onChange={(e) => updateGenetics({ [field]: e.target.value } as any)}
      >
        {options.map((o) => (
          <option key={o} value={o} className="text-blue-gray-900 font-normal">
            {o.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function Step4GeneticManual() {
  const { genetics } = useWizardStore();
  const poorGenes = [
    ...(genetics.cyp2d6_metabolizer === "poor" ? ["CYP2D6"] : []),
    ...(genetics.cyp2c19_metabolizer === "poor" ? ["CYP2C19"] : []),
    ...(genetics.slco1b1_function === "poor" || genetics.slco1b1_function === "reduced" ? ["SLCO1B1"] : []),
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-4">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Pharmacogenomics
        </h2>
        <p className="text-blue-gray-600 text-sm">
          These 8 genes determine how your liver and gut process compounds.
          Upload a genetic file on the previous step for auto-fill.
        </p>
      </div>

      {poorGenes.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-amber-800">High-impact variants detected</p>
            <p className="text-sm text-amber-700 mt-0.5">
              As a <strong>{poorGenes.join(" & ")}</strong> poor metabolizer, some compounds in your stack
              will clear significantly slower. EIRION adjusts load scores and recommendations accordingly.
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm p-6">
        <p className="text-xs font-bold text-blue-gray-500 uppercase tracking-wider mb-3">CYP450 Phase I Enzymes</p>
        {CYP_OPTIONS && GENE_ROWS.map((row) => (
          <GeneRow key={row.field} {...row} options={CYP_OPTIONS} />
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm p-6">
        <p className="text-xs font-bold text-blue-gray-500 uppercase tracking-wider mb-3">Transporter Variants</p>
        {TRANSPORTER_ROWS.map((row) => (
          <GeneRow key={row.field} {...row} options={FUNCTION_OPTIONS} />
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm p-6">
        <p className="text-xs font-bold text-blue-gray-500 uppercase tracking-wider mb-3">Folate Cycle (MTHFR)</p>
        {MTHFR_ROWS.map((row) => (
          <GeneRow key={row.field} {...row} options={MTHFR_OPTIONS} />
        ))}
      </div>

      <p className="text-xs text-blue-gray-400 text-center">
        If unknown, EIRION uses population-average clearance rates · Sources: CPIC, PharmGKB
      </p>
    </div>
  );
}
