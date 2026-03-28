import { useWizardStore } from "../../store/wizardStore";
import { useState, useRef } from "react";

export default function Step2Genetics() {
  const { genetics, updateGenetics } = useWizardStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/extract-genetics`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Failed to extract data");
      }

      const data = await res.json();
      updateGenetics({
        cyp2d6_metabolizer: data.cyp2d6_metabolizer,
        cyp2c19_metabolizer: data.cyp2c19_metabolizer,
      });
    } catch (err: any) {
      setUploadError("Could not process report. Please select variants manually.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif font-bold text-blue-gray-900 mb-2">Pharmacogenomics</h2>
        <p className="text-blue-gray-600">Knowing your CYP450 variants radically improves app scoring accuracy.</p>
      </div>

      <div className="grid gap-6 max-w-xl mx-auto">
        <div 
          className="bg-white border-2 border-dashed border-blue-gray-200 rounded-2xl p-8 text-center hover:border-brand-green hover:bg-brand-green/5 transition-all cursor-pointer relative shadow-sm"
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
            <div className="flex flex-col items-center justify-center space-y-4 py-4">
              <div className="w-10 h-10 rounded-full border-4 border-brand-green/20 border-t-brand-green animate-spin" />
              <p className="font-semibold text-brand-green text-lg animate-pulse">Gemini AI is parsing your report...</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="w-14 h-14 bg-brand-green/10 text-brand-green rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
              </div>
              <h3 className="font-bold text-xl text-blue-gray-900">Upload Clinical Genetics Report</h3>
              <p className="text-sm text-blue-gray-500">AccuGen, GeneSight, or 23andMe Health (PDF/Image)</p>
            </div>
          )}
          {uploadError && <p className="text-red-500 text-sm mt-4 font-medium">{uploadError}</p>}
        </div>

        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-blue-gray-200" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-[#FAF9F6] px-4 text-sm text-blue-gray-500 uppercase tracking-widest font-semibold">Or verify manually</span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-blue-gray-700">CYP2D6 Metabolizer Status</label>
            <select
              className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all bg-white"
              value={genetics.cyp2d6_metabolizer || "unknown"}
              onChange={(e) => updateGenetics({ cyp2d6_metabolizer: e.target.value as any })}
            >
              <option value="unknown">Unknown (Default to Normal)</option>
              <option value="poor">Poor Metabolizer (PM)</option>
              <option value="intermediate">Intermediate Metabolizer (IM)</option>
              <option value="normal">Normal Metabolizer (NM)</option>
              <option value="ultra_rapid">Ultra-Rapid Metabolizer (UM)</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-blue-gray-700">CYP2C19 Metabolizer Status</label>
            <select
              className="w-full px-4 py-3 rounded-xl border border-blue-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all bg-white"
              value={genetics.cyp2c19_metabolizer || "unknown"}
              onChange={(e) => updateGenetics({ cyp2c19_metabolizer: e.target.value as any })}
            >
              <option value="unknown">Unknown (Default to Normal)</option>
              <option value="poor">Poor Metabolizer (PM)</option>
              <option value="intermediate">Intermediate Metabolizer (IM)</option>
              <option value="normal">Normal Metabolizer (NM)</option>
              <option value="ultra_rapid">Ultra-Rapid Metabolizer (UM)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
