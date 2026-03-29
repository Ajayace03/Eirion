import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import Landing from "./pages/Landing.tsx";
import Login from "./pages/Login.tsx";
import Register from "./pages/Register.tsx";
import Wizard from "./pages/Wizard.tsx";
import Dashboard from "./pages/Dashboard.tsx";
import Demo from "./pages/Demo.tsx";
import ProfileSettings from "./pages/ProfileSettings.tsx";
import NotificationBell from "./components/notifications/NotificationBell.tsx";
import { useAuthStore } from "./store/authStore.ts";
import { useWizardStore } from "./store/wizardStore.ts";

// ─── Smart Home ───────────────────────────────────────────────────────────────
// Redirects authenticated users with a result straight to /dashboard.
// Unauthenticated users and users without a result see the Landing page.
function SmartHome() {
  const { isAuthenticated } = useAuthStore();
  const { analysisResult }  = useWizardStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && analysisResult) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, analysisResult, navigate]);

  return <Landing />;
}

// ─── Protected Route ─────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  // In dev mode, allow access without auth. In prod set VITE_REQUIRE_AUTH=true
  if (import.meta.env.VITE_REQUIRE_AUTH === "true" && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}

// ─── Header ──────────────────────────────────────────────────────────────────
function AppHeader() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const location = useLocation();
  // Don't show header on auth pages (they have their own design)
  if (location.pathname === "/login" || location.pathname === "/register") return null;

  return (
    <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-blue-gray-100">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="text-xl font-bold tracking-tight text-blue-gray-900 flex items-center gap-2">
          <span className="w-8 h-8 rounded-full bg-blue-gray-900 flex items-center justify-center text-white text-sm">
            E
          </span>
          EIRION
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated && <NotificationBell />}
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <span className="text-xs text-blue-gray-500 font-medium hidden sm:block">
                {user?.full_name?.split(" ")[0]}
              </span>
              <a
                href="/profile"
                className="w-8 h-8 rounded-full bg-blue-gray-900 flex items-center justify-center text-white text-xs font-bold hover:opacity-80 transition"
                title="Profile & Settings"
              >
                {user?.full_name?.charAt(0)?.toUpperCase() ?? "U"}
              </a>
              <button
                onClick={logout}
                className="text-xs font-bold text-blue-gray-500 hover:text-blue-gray-900 transition px-3 py-1.5 rounded-lg hover:bg-blue-gray-100"
              >
                Sign out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <a href="/login" className="text-xs font-bold text-blue-gray-600 hover:text-blue-gray-900 transition px-3 py-1.5">
                Sign in
              </a>
              <a href="/register" className="text-xs font-black text-white bg-blue-gray-900 hover:bg-blue-gray-700 transition px-4 py-1.5 rounded-xl">
                Get started
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
function App() {
  const { token, logout } = useAuthStore();

  // Auto-logout on token expiry (check every 5min)
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(() => {
      try {
        const parts = token.split(".");
        if (parts.length !== 3) return logout();
        const payload = JSON.parse(atob(parts[1]));
        if (payload.exp && Date.now() / 1000 > payload.exp) logout();
      } catch (_) { logout(); }
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [token, logout]);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-blue-gray-50 flex flex-col font-sans text-blue-gray-900">
        <AppHeader />
        <main className="flex-1 pt-16">
          <Routes>
            {/* Public */}
            <Route path="/" element={<SmartHome />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/demo" element={<Demo />} />
            {/* Protected */}
            <Route path="/onboarding" element={<ProtectedRoute><Wizard /></ProtectedRoute>} />
            <Route path="/dashboard"  element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/profile"    element={<ProtectedRoute><ProfileSettings /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
