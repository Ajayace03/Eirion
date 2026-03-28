import { useWizardStore } from "../store/wizardStore";
import { Link, useSearchParams } from "react-router-dom";
import { useMemo, useState } from "react";
import { Toaster } from "react-hot-toast";
import RiskSummaryCard from "../components/dashboard/RiskSummaryCard";
import TrajectoryChart from "../components/dashboard/TrajectoryChart";
import RecommendationFeed from "../components/dashboard/RecommendationFeed";
import CompoundContributions from "../components/dashboard/CompoundContributions";
import { BiologicalAgeWidget } from "../components/dashboard/BiologicalAgeWidget";
import RiskToastTrigger from "../components/dashboard/BiologicalAgeWidget";
import PaywallOverlay from "../components/dashboard/PaywallOverlay";
import CompoundCart from "../components/dashboard/CompoundCart";
import CircadianPanel from "../components/dashboard/CircadianPanel";
import ProgressChart from "../components/dashboard/ProgressChart";
import AskEirionPanel from "../components/chat/AskEirionPanel";
import ClinicianExportButton from "../components/dashboard/ClinicianExportButton";

export default function Dashboard() {
  const { analysisResult, patient, regimen, adoptedRecs } = useWizardStore();
  const [searchParams] = useSearchParams();
  const isPro = searchParams.get("upgraded") === "true";
  const [activeTab, setActiveTab] = useState<"overview" | "history">("overview");

  // Compute dynamic trajectory based on adopted recommendations
  const dynamicTrajectory = useMemo(() => {
    if (!analysisResult) return [];

    const adopted = analysisResult.recommendations.filter(r => adoptedRecs.has(r.id));
    
    return analysisResult.trajectory.map(point => {
      // Interpolate the improvement for this specific year (0 to 5)
      let totalImprovement = 0;
      for (const rec of adopted) {
        const { delta_index_now, delta_index_year5 } = rec.expected_improvement;
        // Linear interpolation of expected improvement over 5 years
        const impact = delta_index_now + (delta_index_year5 - delta_index_now) * (point.year / 5);
        totalImprovement += impact;
      }
      
      return {
        ...point,
        // Override the optimized line to be the dynamically selected protocol line
        optimized_liver_index: point.liver_index + totalImprovement
      };
    });
  }, [analysisResult, adoptedRecs]);

  if (!analysisResult) {
    return (
      <div className="max-w-6xl mx-auto p-6 mt-8 flex flex-col items-center justify-center min-h-[50vh]">
        <div className="w-16 h-16 bg-blue-gray-100 rounded-full mb-4 flex items-center justify-center animate-pulse" />
        <h2 className="text-2xl font-serif font-bold text-blue-gray-900 mb-2">No Profile Data Found</h2>
        <p className="text-blue-gray-600 mb-6 text-center max-w-md">
          You need to complete the metabolic onboarding before we can generate a longevity blueprint.
        </p>
        <Link 
          to="/onboarding" 
          className="px-6 py-3 bg-blue-gray-900 text-white rounded-xl font-bold shadow-md hover:shadow-lg transition-all"
        >
          Start Onboarding
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
      {/* Toast system - fires on mount if conditions met */}
      <Toaster position="top-right" />
      <RiskToastTrigger result={analysisResult} />

      {/* Top Header with Export Action */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-blue-gray-100 pb-4">
        <div>
          <h2 className="font-serif font-bold text-3xl text-blue-gray-900">Metabolic Overview</h2>
          <p className="text-sm text-blue-gray-500 mt-1">Your longevity blueprint and risk stratification</p>
        </div>
        {isPro && <ClinicianExportButton />}
      </div>

      {/* Header section with top-level metrics */}
      <RiskSummaryCard result={analysisResult} />

      {/* Tab Navigation */}
      <div className="flex items-center gap-4 border-b border-blue-gray-100 pb-px">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 px-1 text-sm font-bold border-b-2 transition-colors ${
            activeTab === "overview" ? "border-blue-gray-900 text-blue-gray-900" : "border-transparent text-blue-gray-500 hover:text-blue-gray-700"
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`pb-3 px-1 text-sm font-bold border-b-2 transition-colors ${
            activeTab === "history" ? "border-blue-gray-900 text-blue-gray-900" : "border-transparent text-blue-gray-500 hover:text-blue-gray-700"
          }`}
        >
          History
        </button>
      </div>

      {activeTab === "overview" ? (
        <>
          {/* Biological Age Widget */}
          <BiologicalAgeWidget
            biologicalAge={analysisResult.biological_age}
            chronologicalAge={patient.age ?? 30}
            riskLevel={analysisResult.risk_summary.risk_level}
            optimizedProjection={
              analysisResult.trajectory[analysisResult.trajectory.length - 1]?.optimized_liver_index
                ? analysisResult.biological_age - analysisResult.risk_summary.projected_drop_percent * 0.3
                : undefined
            }
          />

          {/* Trajectory Graph */}
          <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8">
            <h3 className="font-serif font-bold text-2xl text-blue-gray-900 mb-2">5-Year Liver Stress Projection</h3>
            <p className="text-blue-gray-600 mb-6 text-sm">
              Comparing your current trajectory against the selected protocol. Lower index indicates worsening liver function and accumulated stress.
            </p>
            <TrajectoryChart data={dynamicTrajectory} />
          </div>

          {/* Lower split column section */}
          <div className="grid lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3">
              {isPro
                ? <RecommendationFeed result={analysisResult} />
                : <PaywallOverlay recommendations={analysisResult.recommendations} />
              }
            </div>
            <div className="lg:col-span-2">
              <CompoundContributions result={analysisResult} />
            </div>
          </div>

          {/* Compound Cart — only shown when Pro */}
          {isPro && (
            <CompoundCart recommendations={analysisResult.recommendations} />
          )}

          {/* Circadian Dosing Panel */}
          {regimen.length > 0 && (
            <CircadianPanel regimen={regimen} />
          )}
        </>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8">
          <div className="mb-6">
            <h3 className="font-serif font-bold text-2xl text-blue-gray-900">Longitudinal Progress</h3>
            <p className="text-sm text-blue-gray-500 mt-1">Track your liver index improvements over time.</p>
          </div>
          <ProgressChart />
        </div>
      )}

      {/* Global AI Chat Drawer Overlay */}
      {isPro && <AskEirionPanel />}

    </div>
  );
}
