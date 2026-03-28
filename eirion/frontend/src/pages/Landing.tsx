import { useNavigate } from "react-router-dom";
import { useWizardStore } from "../store/wizardStore";
import { ArrowRight, Activity, ShieldPlus, Dna } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();
  const { loadPriyaExample } = useWizardStore();

  const handleStart = () => {
    navigate("/onboarding");
  };

  const handlePriyaDemo = () => {
    loadPriyaExample();
    navigate("/onboarding");
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-3xl space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
        
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm font-medium border border-blue-100 mb-4">
          <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse"></span>
          ETGen AI Hackathon 2026 Prototype
        </div>

        <h1 className="text-5xl md:text-7xl font-serif font-bold tracking-tight text-blue-gray-900">
          Precision <span className="text-brand-green">Longevity</span>
        </h1>
        
        <p className="text-xl text-blue-gray-600 max-w-2xl mx-auto leading-relaxed">
          The first pharmacogenomics-powered liver toxicity scoring suite. 
          Optimize your supplement stack for maximum longevity with zero guesswork.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
          <button
            onClick={handleStart}
            className="group relative px-8 py-4 bg-blue-gray-900 text-white rounded-xl font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2 overflow-hidden"
          >
            <span className="relative z-10">Start Your Analysis</span>
            <ArrowRight className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
          </button>
          
          <button
            onClick={handlePriyaDemo}
            className="px-8 py-4 bg-white text-blue-gray-900 border-2 border-blue-gray-200 rounded-xl font-bold shadow-sm hover:border-blue-gray-400 hover:bg-blue-gray-50 transition-all"
          >
            Load Priya Example
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-24 pt-16 border-t border-blue-gray-100 text-left">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-green/10 flex items-center justify-center text-brand-green">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg">Dynamic Risk Scoring</h3>
            <p className="text-sm text-blue-gray-600">Calculates cumulative hepatic stress across 15+ longevity compounds and lifestyle factors.</p>
          </div>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-600">
              <Dna className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg">Pharmacogenomics</h3>
            <p className="text-sm text-blue-gray-600">Adjusts clearance rates based on CYP2D6/CYP2C19 gene variants using CPIC standards.</p>
          </div>
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-amber/10 flex items-center justify-center text-brand-amber">
              <ShieldPlus className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg">Actionable Trajectories</h3>
            <p className="text-sm text-blue-gray-600">Forecasts 5-year organ health and provides exact reduction/swap protocols.</p>
          </div>
        </div>

      </div>
    </div>
  );
}
