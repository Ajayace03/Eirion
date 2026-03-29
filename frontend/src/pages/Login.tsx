import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function Login() {
  const { login, loading, error, isAuthenticated, user, clearError } = useAuthStore();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(user.onboarding_complete ? "/dashboard" : "/onboarding");
    }
  }, [isAuthenticated, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(email, password);
    } catch (_) {/* error shown in UI */ }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center bg-blue-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-gray-900 text-white font-black text-xl mb-4 shadow-sm">
            E
          </div>
          <h1 className="text-3xl font-serif font-bold text-blue-gray-900 tracking-tight">
            Welcome back
          </h1>
          <p className="text-blue-gray-500 mt-2">
            Sign in to access your longevity profile
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-3xl shadow-sm border border-blue-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-blue-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-blue-gray-50 border border-blue-gray-200 rounded-xl px-4 py-3 text-blue-gray-900 placeholder-blue-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
              />
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-bold text-blue-gray-700">
                  Password
                </label>
                <a href="#" className="text-sm font-medium text-brand-green hover:text-green-700 transition">
                  Forgot password?
                </a>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-blue-gray-50 border border-blue-gray-200 rounded-xl px-4 py-3 text-blue-gray-900 placeholder-blue-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
              />
            </div>

            {error && (
              <div className="bg-brand-red/10 border border-brand-red/20 rounded-xl px-4 py-3 text-sm text-brand-red font-bold">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3.5 px-4 bg-blue-gray-900 hover:bg-black text-white rounded-xl font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? "Signing in..." : "Sign In"}
              {!loading && <span>→</span>}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-blue-gray-100 text-center">
            <p className="text-sm text-blue-gray-600">
              Don't have an account?{" "}
              <Link to="/register" className="font-bold text-blue-gray-900 hover:text-brand-green transition">
                Create one now
              </Link>
            </p>
          </div>
        </div>
        
        {/* Footer info */}
        <p className="text-center text-xs text-blue-gray-400 mt-8">
          Secured by end-to-end encryption. HIPAA compliant infrastructure.
        </p>

      </div>
    </div>
  );
}
