import { useState, useRef } from "react";
import { useWizardStore } from "../../store/wizardStore";
import { CheckCircle, AlertTriangle, Loader2, FileText, Dna } from "lucide-react";

const GENE_LABELS: Record<string, string> = {
  cyp2d6_metabolizer: "CYP2D6",
  cyp2c19_metabolizer: "CYP2C19",
  cyp3a4_metabolizer: "CYP3A4",
  cyp2c9_metabolizer: "CYP2C9",
  cyp1a2_metabolizer: "CYP1A2",
  slco1b1_function: "SLCO1B1",
  ugt1a1_function: "UGT1A1",
  mthfr_c677t: "MTHFR C677T",
};

const PHENOTYPE_COLORS: Record<string, string> = {
  poor: "bg-brand-red/10 text-brand-red border-brand-red/20",
  intermediate: "bg-brand-amber/10 text-brand-amber border-brand-amber/20",
  normal: "bg-brand-green/10 text-brand-green border-brand-green/20",
  ultra_rapid: "bg-blue-100 text-blue-700 border-blue-200",
  reduced: "bg-brand-amber/10 text-brand-amber border-brand-amber/20",
  unknown: "bg-blue-gray-100 text-blue-gray-500 border-blue-gray-200",
};

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Step3GeneticUpload() {
  const { updateGenetics } = useWizardStore();
  const [uploading, setUploading] = useState(false);
  const [uploadMode, setUploadMode] = useState<"23andme" | "pgx" | null>(null);
  const [parsed, setParsed] = useState<Record<string, unknown> | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File, mode: "23andme" | "pgx") => {
    setUploading(true);
    setUploadError("");
    setFileName(file.name);

    const endpoint = mode === "23andme"
      ? `${API_BASE}/extraction/parse-genetic-file`
      : `${API_BASE}/extraction/parse-pgx-report`;

    try {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch(endpoint, { method: "POST", body: form });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed");
      }
      const { extracted_data } = await resp.json();
      setParsed(extracted_data as Record<string, unknown>);
      // Apply to wizard store
      const { diplotypes, source, ...geneticFields } = extracted_data;
      updateGenetics({ ...geneticFields, diplotypes, source });
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>, mode: "23andme" | "pgx") => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadMode(mode);
      handleUpload(file, mode);
    }
  };

  const geneFields = Object.entries(GENE_LABELS).filter(([key]) => key !== "mthfr_c677t");

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">
          Genetic Data Upload
        </h2>
        <p className="text-blue-gray-600">
          Upload your raw genetic file for automated pharmacogenomic profiling — or skip to enter manually.
        </p>
      </div>

      {/* Upload Option Cards */}
      {!parsed && (
        <div className="grid md:grid-cols-2 gap-4">
          {/* 23andMe */}
          <div
            className="relative border-2 border-dashed border-blue-gray-200 hover:border-blue-gray-400 rounded-2xl p-6 text-center cursor-pointer transition-all group"
            onClick={() => { fileRef.current?.setAttribute("data-mode", "23andme"); fileRef.current?.click(); }}
          >
            <div className="w-12 h-12 bg-blue-gray-900 rounded-xl flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <p className="font-bold text-blue-gray-900 mb-1">23andMe Raw Data</p>
            <p className="text-xs text-blue-gray-500">genome_*.txt file (~600k SNPs)</p>
            <p className="text-[10px] text-blue-gray-400 mt-2">Tab-delimited · GRCh37 build</p>
          </div>

          {/* PGx Report */}
          <div
            className="relative border-2 border-dashed border-blue-gray-200 hover:border-blue-gray-400 rounded-2xl p-6 text-center cursor-pointer transition-all"
            onClick={() => { fileRef.current?.setAttribute("data-mode", "pgx"); fileRef.current?.click(); }}
          >
            <div className="w-12 h-12 bg-brand-green rounded-xl flex items-center justify-center mx-auto mb-3">
              <Dna className="w-6 h-6 text-white" />
            </div>
            <p className="font-bold text-blue-gray-900 mb-1">PGx Clinical Report</p>
            <p className="text-xs text-blue-gray-500">GeneSight / Strand / Dante Labs PDF</p>
            <p className="text-[10px] text-blue-gray-400 mt-2">Star-allele diplotype panel</p>
          </div>
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept=".txt,.pdf,.jpg,.jpeg,.png"
        className="hidden"
        onChange={(e) => {
          const mode = (fileRef.current?.getAttribute("data-mode") || "23andme") as "23andme" | "pgx";
          onFileChange(e, mode);
        }}
      />

      {/* Uploading state */}
      {uploading && (
        <div className="flex flex-col items-center py-8 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-green" />
          <p className="text-sm font-medium text-blue-gray-700">
            {uploadMode === "23andme" ? "Scanning SNPs for 15 pharmacogenomic markers…" : "Extracting gene phenotypes from report…"}
          </p>
          <p className="text-xs text-blue-gray-400">{fileName}</p>
        </div>
      )}

      {/* Error */}
      {uploadError && (
        <div className="flex items-start gap-2.5 p-4 bg-red-50 border border-red-200 rounded-xl">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{uploadError}</p>
        </div>
      )}

      {/* Success — show parsed results */}
      {parsed && !uploading && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-brand-green/5 border border-brand-green/20 rounded-xl">
            <CheckCircle className="w-5 h-5 text-brand-green shrink-0" />
            <div>
              <p className="text-sm font-bold text-brand-green">
                Extraction successful — {fileName}
              </p>
              <p className="text-xs text-blue-gray-500 mt-0.5">
                Review extracted phenotypes below. You can override any value.
              </p>
            </div>
            <button
              onClick={() => { setParsed(null); setFileName(""); }}
              className="ml-auto text-xs text-blue-gray-400 hover:text-red-500 underline"
            >
              Re-upload
            </button>
          </div>

          {/* Gene phenotype grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {geneFields.map(([field, label]) => {
              const val = ((parsed[field] as string) || "unknown");
              const diplotypes = parsed.diplotypes as Record<string, string> | undefined;
              const diploKey = label.split(" ")[0];
              return (
                <div key={field} className="space-y-1.5">
                  <p className="text-xs font-bold text-blue-gray-600">{label}</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border capitalize ${PHENOTYPE_COLORS[val] || PHENOTYPE_COLORS.unknown}`}>
                    {val.replace("_", " ")}
                  </span>
                  {diplotypes?.[diploKey] && (
                    <p className="text-[10px] text-blue-gray-400 font-mono">
                      {diplotypes[diploKey]}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="pt-4 border-t border-blue-gray-100 text-center">
        <p className="text-xs text-blue-gray-400">
          Files are processed via end-to-end encrypted AI. Not stored. <br />
          <span className="font-medium">Continue without uploading</span> — use Next to enter genes manually.
        </p>
      </div>
    </div>
  );
}
