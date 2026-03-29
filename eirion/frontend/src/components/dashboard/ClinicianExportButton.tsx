import { useState } from "react";
import { FileText, Loader2 } from "lucide-react";
import { useWizardStore } from "../../store/wizardStore";
import { useAuthStore } from "../../store/authStore";
import toast from "react-hot-toast";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ClinicianExportButton() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    const state = useWizardStore.getState();
    if (!state.analysisResult) {
      toast.error("Run an analysis first before exporting.");
      return;
    }
    setIsExporting(true);

    const token = useAuthStore.getState().token;

    try {
      const requestPayload = {
        patient:    state.patient,
        conditions: state.conditions,
        lifestyle:  state.lifestyle,
        genetics:   state.genetics,
        regimen:    state.regimen,
        labs:       Object.keys(state.labs ?? {}).length > 0 ? state.labs : undefined,
        food:       state.food,
      };

      const response = await fetch(`${API}/export/clinician-report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          request_payload:  requestPayload,
          response_payload: state.analysisResult,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to generate PDF");
      }

      const blob = await response.blob();
      const url  = window.URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = "Eirion_Clinical_Report.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      toast.success("Clinical report downloaded ✓");
    } catch (e: any) {
      console.error(e);
      toast.error(e.message || "Export failed — check backend connection.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      id="clinician-export-btn"
      onClick={handleExport}
      disabled={isExporting}
      className="group flex items-center gap-2 px-5 py-2.5 bg-blue-gray-900 text-white font-bold rounded-xl shadow-md hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:translate-y-0 transition-all text-sm"
    >
      {isExporting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <FileText className="w-4 h-4 group-hover:scale-110 transition-transform" />
      )}
      {isExporting ? "Generating PDF…" : "Download Clinical Report"}
    </button>
  );
}
