import { useRef, useState } from "react";
import { useWizardStore } from "../../store/wizardStore";
import { Upload, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Lab fields: field key → { label, unit, normalRange, flagHigh, flagLow }
const LAB_SECTIONS = [
  {
    title: "Liver Function (LFT)",
    icon: "🫀",
    fields: [
      { key: "ast_u_per_l", label: "AST (SGOT)", unit: "U/L", high: 40, low: 10 },
      { key: "alt_u_per_l", label: "ALT (SGPT)", unit: "U/L", high: 56, low: 7 },
      { key: "ggt_u_per_l", label: "GGT", unit: "U/L", high: 60, low: 12 },
      { key: "alp_u_per_l", label: "ALP", unit: "U/L", high: 147, low: 44 },
      { key: "albumin_g_per_dl", label: "Albumin", unit: "g/dL", high: 5.2, low: 3.4 },
      { key: "bilirubin_mg_per_dl", label: "T. Bilirubin", unit: "mg/dL", high: 1.2, low: 0.1 },
    ],
  },
  {
    title: "Kidney Function (KFT)",
    icon: "🫘",
    fields: [
      { key: "creatinine_mg_per_dl", label: "Creatinine", unit: "mg/dL", high: 1.3, low: 0.7 },
      { key: "egfr_ml_per_min", label: "eGFR (CKD-EPI)", unit: "mL/min", high: 999, low: 60 },
      { key: "bun_mg_per_dl", label: "BUN", unit: "mg/dL", high: 24, low: 6 },
      { key: "uric_acid_mg_per_dl", label: "Uric Acid", unit: "mg/dL", high: 7.0, low: 3.4 },
    ],
  },
  {
    title: "Metabolic / Cardiac",
    icon: "❤️",
    fields: [
      { key: "hba1c_pct", label: "HbA1c", unit: "%", high: 5.7, low: 4.0 },
      { key: "glucose_mg_per_dl", label: "Fasting Glucose", unit: "mg/dL", high: 99, low: 70 },
      { key: "ldl_mg_per_dl", label: "LDL Cholesterol", unit: "mg/dL", high: 100, low: 0 },
      { key: "hdl_mg_per_dl", label: "HDL Cholesterol", unit: "mg/dL", high: 999, low: 40 },
      { key: "triglycerides_mg_per_dl", label: "Triglycerides", unit: "mg/dL", high: 150, low: 0 },
      { key: "hscrp_mg_per_l", label: "hsCRP", unit: "mg/L", high: 1.0, low: 0 },
    ],
  },
];

function flagStatus(val: number | undefined, high: number, low: number) {
  if (val === undefined || val === null) return null;
  if (val > high) return "high";
  if (val < low) return "low";
  return "normal";
}

export default function Step5LabUpload() {
  const { labs, updateLabs } = useWizardStore();
  const [uploading, setUploading] = useState(false);
  const [uploadDone, setUploadDone] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const clearAllLabs = () => {
    const blank: Record<string, undefined> = {};
    LAB_SECTIONS.flatMap(s => s.fields).forEach(f => { blank[f.key] = undefined; });
    updateLabs(blank as any);
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError("");
    setFileName(file.name);
    try {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch(`${API_BASE}/extraction/parse-labs`, { method: "POST", body: form });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed");
      }
      const { extracted_data } = await resp.json();
      updateLabs(extracted_data);
      setUploadDone(true);
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-4">
        <div className="text-center flex-1">
          <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Lab Report</h2>
          <p className="text-blue-gray-600 text-sm">
            Upload your blood test results for automatic extraction, or fill manually. All lab values inform the risk calculation.
          </p>
        </div>
        <button
          onClick={clearAllLabs}
          className="shrink-0 text-xs font-semibold text-blue-gray-400 hover:text-red-500 border border-blue-gray-200 hover:border-red-300 px-3 py-1.5 rounded-lg transition-colors ml-4"
          title="Reset all lab values"
        >
          Clear all
        </button>
      </div>

      {/* Upload zone */}
      {!uploadDone && !uploading && (
        <div
          className="border-2 border-dashed border-blue-gray-200 hover:border-blue-gray-400 rounded-2xl p-8 text-center cursor-pointer transition-all"
          onClick={() => fileRef.current?.click()}
        >
          <Upload className="w-10 h-10 text-blue-gray-400 mx-auto mb-3" />
          <p className="font-bold text-blue-gray-800 mb-1">Upload Lab Report</p>
          <p className="text-xs text-blue-gray-500">PDF, JPEG, or PNG · Max 10MB</p>
          <p className="text-[10px] text-blue-gray-400 mt-1">Supports Thyrocare, SRL, LabCorp, Quest, Redcliffe …</p>
        </div>
      )}

      <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />

      {uploading && (
        <div className="flex items-center justify-center gap-3 py-6">
          <Loader2 className="w-6 h-6 animate-spin text-brand-green" />
          <p className="text-sm text-blue-gray-700">Extracting lab values from {fileName}…</p>
        </div>
      )}

      {uploadError && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
          <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{uploadError}</p>
        </div>
      )}

      {uploadDone && (
        <div className="flex items-center gap-2 p-3 bg-brand-green/5 border border-brand-green/20 rounded-xl">
          <CheckCircle className="w-5 h-5 text-brand-green" />
          <p className="text-sm font-bold text-brand-green">Auto-filled from {fileName}</p>
          <button onClick={() => setUploadDone(false)} className="ml-auto text-xs text-blue-gray-400 underline hover:text-red-500">Re-upload</button>
        </div>
      )}

      {/* Manual entry — always shown */}
      <div className="space-y-6">
        {LAB_SECTIONS.map((section) => (
          <div key={section.title} className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-blue-gray-50 flex items-center gap-2">
              <span className="text-lg">{section.icon}</span>
              <p className="text-xs font-bold text-blue-gray-600 uppercase tracking-wider">{section.title}</p>
            </div>
            <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-3">
              {section.fields.map(({ key, label, unit, high, low }) => {
                const val = (labs as any)?.[key];
                const flag = flagStatus(val, high, low);
                return (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <label className="text-[11px] font-bold text-blue-gray-600">{label}</label>
                      {flag === "high" && <span className="text-[10px] font-bold text-brand-red">↑ HIGH</span>}
                      {flag === "low" && <span className="text-[10px] font-bold text-blue-500">↓ LOW</span>}
                      {flag === "normal" && <span className="text-[10px] text-brand-green">Normal</span>}
                    </div>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        placeholder="—"
                        className={`w-full px-2.5 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 pr-10 ${
                          flag === "high" ? "border-brand-red/40 text-brand-red focus:ring-brand-red/20" :
                          flag === "low" ? "border-blue-400/40 text-blue-600 focus:ring-blue-300/20" :
                          "border-blue-gray-200 focus:ring-brand-green/30"
                        }`}
                        value={val !== undefined && val !== null ? val : ""}
                        onChange={(e) => {
                          const parsed = parseFloat(e.target.value);
                          updateLabs({ [key]: e.target.value === "" ? undefined : (isNaN(parsed) ? undefined : parsed) } as any);
                        }}
                      />
                      <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-blue-gray-400">{unit}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
