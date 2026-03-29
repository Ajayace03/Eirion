import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function Register() {
  const { register, loading, error, isAuthenticated, clearError } = useAuthStore();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (isAuthenticated) navigate("/onboarding");
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError("");
    if (password !== confirm) {
      setLocalError("Passwords don't match");
      return;
    }
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }
    try {
      await register(email, password, fullName);
    } catch (_) {/* error shown via store */ }
  };

  const displayError = localError || error;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center bg-blue-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-brand-green text-white font-black text-xl mb-4 shadow-sm">
            E
          </div>
          <h1 className="text-3xl font-serif font-bold text-blue-gray-900 tracking-tight">
            Create account
          </h1>
          <p className="text-blue-gray-500 mt-2">
            Start your personalized longevity journey
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-3xl shadow-sm border border-blue-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-blue-gray-700 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="Priya Sharma"
                className="w-full bg-blue-gray-50 border border-blue-gray-200 rounded-xl px-4 py-3 text-blue-gray-900 placeholder-blue-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-blue-gray-700 mb-1.5">
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
              <label className="block text-sm font-bold text-blue-gray-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Min 8 characters"
                className="w-full bg-blue-gray-50 border border-blue-gray-200 rounded-xl px-4 py-3 text-blue-gray-900 placeholder-blue-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-blue-gray-700 mb-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                placeholder="Repeat password"
                className="w-full bg-blue-gray-50 border border-blue-gray-200 rounded-xl px-4 py-3 text-blue-gray-900 placeholder-blue-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-green/50 focus:border-brand-green transition-all"
              />
            </div>

            {displayError && (
              <div className="bg-brand-red/10 border border-brand-red/20 rounded-xl px-4 py-3 text-sm text-brand-red font-bold">
                {displayError}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-3.5 px-4 bg-blue-gray-900 hover:bg-black text-white rounded-xl font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? "Creating account..." : "Create Account"}
              {!loading && <span>→</span>}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-blue-gray-100 text-center">
            <p className="text-sm text-blue-gray-600">
              Already have an account?{" "}
              <Link to="/login" className="font-bold text-blue-gray-900 hover:text-brand-green transition">
                Sign in
              </Link>
            </p>
          </div>
        </div>
        
        {/* Footer info */}
        <p className="text-center text-xs text-blue-gray-400 mt-8 pb-8">
          By signing up you agree to Eirion's privacy-first data policy.
        </p>

      </div>
    </div>
  );
}
