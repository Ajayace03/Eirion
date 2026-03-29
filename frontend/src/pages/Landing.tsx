import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, Activity, ShieldPlus, Dna, LayoutDashboard } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useWizardStore } from "../store/wizardStore";

export default function Landing() {
  const navigate    = useNavigate();
  const { isAuthenticated, user } = useAuthStore();
  const { analysisResult }        = useWizardStore();

  // Determine what the primary CTA should do
  const handlePrimaryCTA = () => {
    if (isAuthenticated && analysisResult) {
      navigate("/dashboard");
    } else if (isAuthenticated) {
      navigate("/onboarding");
    } else {
      navigate("/register");
    }
  };

  const primaryLabel = isAuthenticated && analysisResult
    ? "Go to Dashboard"
    : isAuthenticated
    ? "Continue Onboarding"
    : "Get Started — it's free";

  const PrimaryIcon = isAuthenticated && analysisResult ? LayoutDashboard : ArrowRight;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-3xl space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm font-medium border border-blue-100 mb-4">
          <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
          ETGen AI Hackathon 2026 Prototype
        </div>

        <h1 className="text-5xl md:text-7xl font-serif font-bold tracking-tight text-blue-gray-900">
          Precision <span className="text-brand-green">Longevity</span>
        </h1>

        {isAuthenticated && (
          <p className="text-sm font-medium text-blue-gray-500">
            Welcome back, <span className="text-blue-gray-900 font-bold">{user?.full_name?.split(" ")[0] ?? "there"}</span> 👋
          </p>
        )}

        <p className="text-xl text-blue-gray-600 max-w-2xl mx-auto leading-relaxed">
          The first pharmacogenomics-powered liver toxicity scoring suite.
          Optimize your supplement stack and diet for maximum longevity.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
          {/* Primary CTA — auth-aware */}
          <button
            id="landing-primary-cta"
            onClick={handlePrimaryCTA}
            className="group relative px-8 py-4 bg-blue-gray-900 text-white rounded-xl font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2 overflow-hidden"
          >
            <span className="relative z-10">{primaryLabel}</span>
            <PrimaryIcon className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
          </button>

          {/* Secondary CTA — show Sign In if not authenticated, or Demo otherwise */}
          {!isAuthenticated ? (
            <Link
              to="/login"
              id="landing-signin-link"
              className="px-8 py-4 bg-white text-blue-gray-900 border-2 border-blue-gray-200 rounded-xl font-bold shadow-sm hover:border-blue-gray-400 hover:bg-blue-gray-50 transition-all"
            >
              Sign In
            </Link>
          ) : (
            <button
              onClick={() => navigate("/demo")}
              className="px-8 py-4 bg-white text-blue-gray-900 border-2 border-blue-gray-200 rounded-xl font-bold shadow-sm hover:border-blue-gray-400 hover:bg-blue-gray-50 transition-all"
            >
              ⚡ Try Priya Demo
            </button>
          )}
        </div>

        {/* Sub-links for unauthenticated users */}
        {!isAuthenticated && (
          <p className="text-sm text-blue-gray-500">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-gray-900 font-bold underline underline-offset-2 hover:text-brand-green transition-colors">
              Sign in
            </Link>
            {" "}·{" "}
            <button
              onClick={() => navigate("/demo")}
              className="text-blue-gray-900 font-bold underline underline-offset-2 hover:text-brand-green transition-colors"
            >
              View demo
            </button>
          </p>
        )}

        <div className="grid md:grid-cols-3 gap-8 mt-24 pt-16 border-t border-blue-gray-100 text-left">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-green/10 flex items-center justify-center text-brand-green">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg">Dynamic Risk Scoring</h3>
            <p className="text-sm text-blue-gray-600">Calculates cumulative hepatic stress across compounds, lifestyle factors, and dietary patterns.</p>
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
            <h3 className="font-bold text-lg">Actionable Blueprints</h3>
            <p className="text-sm text-blue-gray-600">Forecasts 5-year organ health and provides exact swap/reduction/diet protocols.</p>
          </div>
        </div>

      </div>
    </div>
  );
}
