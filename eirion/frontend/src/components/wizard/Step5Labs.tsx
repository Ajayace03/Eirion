import { useWizardStore } from "../../store/wizardStore";
import { useState, useRef } from "react";

export default function Step5Labs() {
  const { labs, updateLabs } = useWizardStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError("");
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/extraction/parse-labs`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to extract data");

      const raw = await res.json();
      const extracted = raw.extracted_data;
      
      updateLabs({
        ast_u_per_l: extracted.ast ?? undefined,
        alt_u_per_l: extracted.alt ?? undefined,
        // Bilirubin wasn't added to the schema prompt, handle gracefully if missing
      });
      setUploadSuccess(true);
    } catch {
      setUploadError("Could not read the report. Please enter values manually below.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Recent Bloodwork</h2>
        <p className="text-blue-gray-600">Upload your blood panel or enter values manually. Calibrates trajectory accuracy significantly.</p>
      </div>

      {/* Upload Dropzone */}
      <div
        className={`max-w-2xl mx-auto border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all shadow-sm
          ${uploadSuccess
            ? "border-brand-green bg-brand-green/5 hover:bg-brand-green/10"
            : "border-blue-gray-200 bg-white hover:border-brand-green hover:bg-brand-green/5"
          }`}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="application/pdf,image/*"
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center space-y-4 py-4">
            <div className="w-10 h-10 rounded-full border-4 border-brand-green/20 border-t-brand-green animate-spin" />
            <p className="font-semibold text-brand-green text-lg animate-pulse">Gemini AI is reading your blood panel...</p>
          </div>
        ) : uploadSuccess ? (
          <div className="space-y-2">
            <div className="w-14 h-14 bg-brand-green/20 text-brand-green rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="font-bold text-xl text-brand-green">Lab Values Extracted!</h3>
            <p className="text-sm text-blue-gray-500">Values auto-filled below. Click to upload a different report.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="w-14 h-14 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-bold text-xl text-blue-gray-900">Upload Blood Panel Report</h3>
            <p className="text-sm text-blue-gray-500">Quest, LabCorp, or any metabolic panel PDF/image</p>
          </div>
        )}

        {uploadError && <p className="text-red-500 text-sm mt-4 font-medium">{uploadError}</p>}
      </div>

      {/* Divider */}
      <div className="relative py-2 max-w-2xl mx-auto">
        <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-blue-gray-200" /></div>
        <div className="relative flex justify-center">
          <span className="bg-[#FAF9F6] px-4 text-sm text-blue-gray-500 uppercase tracking-widest font-semibold">Or enter manually</span>
        </div>
      </div>

      {/* Manual Input Grid */}
      <div className="grid md:grid-cols-3 gap-6 max-w-2xl mx-auto">
        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">AST (U/L)</label>
          <input
            type="number" min="0"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={labs.ast_u_per_l || ""}
            onChange={(e) => updateLabs({ ast_u_per_l: parseFloat(e.target.value) || undefined })}
            placeholder="e.g. 20"
          />
          <p className="text-xs text-blue-gray-400">Normal: 8–40 U/L</p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">ALT (U/L)</label>
          <input
            type="number" min="0"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={labs.alt_u_per_l || ""}
            onChange={(e) => updateLabs({ alt_u_per_l: parseFloat(e.target.value) || undefined })}
            placeholder="e.g. 22"
          />
          <p className="text-xs text-blue-gray-400">Normal: 7–56 U/L</p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-blue-gray-700">Bilirubin (mg/dL)</label>
          <input
            type="number" min="0" step="0.1"
            className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
            value={labs.bilirubin_mg_per_dl || ""}
            onChange={(e) => updateLabs({ bilirubin_mg_per_dl: parseFloat(e.target.value) || undefined })}
            placeholder="e.g. 0.8"
          />
          <p className="text-xs text-blue-gray-400">Normal: 0.1–1.2</p>
        </div>
      </div>
    </div>
  );
}
