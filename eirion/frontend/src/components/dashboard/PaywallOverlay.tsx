import { useState } from "react";
import { Recommendation } from "../../types";
import { Lock, Sparkles, Zap } from "lucide-react";

interface Props {
  recommendations: Recommendation[];
}

export default function PaywallOverlay({ recommendations }: Props) {
  const [isUpgrading, setIsUpgrading] = useState(false);

  const handleUpgrade = async () => {
    setIsUpgrading(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/billing/create-checkout-session`, {
        method: "POST",
      });
      const { url } = await res.json();
      window.location.href = url;
    } catch {
      setIsUpgrading(false);
      alert("Could not initiate checkout. Please try again.");
    }
  };

  // Show locked preview of up to 2 recs
  const preview = recommendations.slice(0, 2);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-blue-gray-100 p-8 h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-serif font-bold text-2xl text-blue-gray-900">Optimization Protocol</h3>
        <span className="text-sm font-bold bg-blue-gray-100 text-blue-gray-600 px-3 py-1 rounded-full">
          {recommendations.length} Actions
        </span>
      </div>

      {/* Blurred preview cards */}
      <div className="relative space-y-4">
        <div className="space-y-4 select-none pointer-events-none">
          {preview.map((rec) => (
            <div key={rec.id} className="p-5 rounded-xl border border-blue-gray-100 blur-sm opacity-60">
              <div className="flex items-start gap-4">
                <div className="mt-1 flex-shrink-0 w-10 h-10 rounded-full bg-blue-gray-100" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-blue-gray-200 rounded-md w-3/4" />
                  <div className="h-4 bg-blue-gray-100 rounded-md w-full" />
                  <div className="h-4 bg-blue-gray-100 rounded-md w-5/6" />
                </div>
              </div>
            </div>
          ))}
          {recommendations.length > 2 && (
            <div className="p-5 rounded-xl border border-blue-gray-100 blur-sm opacity-40">
              <div className="h-20 bg-blue-gray-50 rounded-xl" />
            </div>
          )}
        </div>

        {/* Paywall CTA overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-t from-white via-white/90 to-transparent rounded-xl px-6 pt-10">
          <div className="w-16 h-16 bg-blue-gray-900 rounded-full flex items-center justify-center mb-4 shadow-xl">
            <Lock className="w-7 h-7 text-white" />
          </div>
          <h4 className="text-2xl font-serif font-bold text-blue-gray-900 mb-2 text-center">
            Unlock Your Protocol
          </h4>
          <p className="text-blue-gray-500 text-sm text-center mb-6 max-w-xs">
            Your personalized AI optimization protocol with {recommendations.length} precision interventions
            is ready. Upgrade to Eirion Pro to access it.
          </p>

          <div className="space-y-3 w-full max-w-xs mb-6">
            {[
              "Full optimization protocol with delta scores",
              "Gemini AI personalized reasoning",
              "Monthly trajectory tracking & re-scoring",
            ].map((f) => (
              <div key={f} className="flex items-center gap-2 text-sm text-blue-gray-700">
                <Sparkles className="w-4 h-4 text-brand-green shrink-0" />
                {f}
              </div>
            ))}
          </div>

          <button
            onClick={handleUpgrade}
            disabled={isUpgrading}
            className="w-full max-w-xs flex items-center justify-center gap-2 px-6 py-4 bg-blue-gray-900 text-white font-bold rounded-2xl shadow-lg hover:bg-blue-gray-800 active:scale-95 transition-all disabled:opacity-70"
          >
            <Zap className="w-5 h-5" />
            {isUpgrading ? "Redirecting to Stripe..." : "Upgrade — $20/mo"}
          </button>

          <p className="text-xs text-blue-gray-400 mt-3">Cancel anytime. No hidden fees.</p>
        </div>
      </div>
    </div>
  );
}
