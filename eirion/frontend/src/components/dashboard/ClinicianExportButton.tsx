import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { useWizardStore } from "../../store/wizardStore";
import toast from "react-hot-toast";

export default function ClinicianExportButton() {
  const { analysisResult } = useWizardStore();
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (!analysisResult) return;
    setIsExporting(true);

    try {
      const response = await fetch("http://localhost:8000/export/clinician-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer bypass-string",
        },
        body: JSON.stringify({ analysis_payload: analysisResult }),
      });

      if (!response.ok) throw new Error("Failed to generate PDF");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Eirion_Clinical_Report.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      
      toast.success("Clinical Report Downloaded Successfully");
    } catch (e) {
      console.error(e);
      toast.error("Export process failed.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={isExporting}
      className="flex items-center gap-2 px-4 py-2 bg-white border border-blue-gray-200 text-blue-gray-700 font-bold rounded-xl shadow-sm hover:shadow-md hover:border-blue-gray-300 disabled:opacity-50 transition-all text-sm"
    >
      {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
      {isExporting ? "Generating PDF..." : "Export Medical PDF"}
    </button>
  );
}
