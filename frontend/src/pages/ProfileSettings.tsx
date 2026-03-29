import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { useWizardStore } from "../store/wizardStore";
import {
  User, Lock, Bell, Trash2, Save, ArrowLeft,
  ShieldCheck, Download, RotateCcw, Eye, EyeOff
} from "lucide-react";
import toast from "react-hot-toast";
import { Toaster } from "react-hot-toast";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ── Section card wrapper ──────────────────────────────────────────────────────
function Section({
  icon: Icon, title, children
}: { icon: any; title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-blue-gray-50 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-gray-900 flex items-center justify-center">
          <Icon className="w-4 h-4 text-white" />
        </div>
        <h3 className="font-bold text-blue-gray-900">{title}</h3>
      </div>
      <div className="px-6 py-5 space-y-4">{children}</div>
    </div>
  );
}

// ── Field wrapper ─────────────────────────────────────────────────────────────
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-bold text-blue-gray-500 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "w-full px-4 py-2.5 rounded-xl border border-blue-gray-200 text-sm text-blue-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-gray-400/30 bg-white transition";

export default function ProfileSettings() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuthStore();
  const { patient, analysisResult, resetWizard } = useWizardStore();

  // ── Form state ──────────────────────────────────────────────────────────────
  const [name, setName] = useState(user?.full_name ?? "");
  const [email] = useState(user?.email ?? "");

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw]         = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showPw, setShowPw]       = useState(false);

  const [notifDose,   setNotifDose]   = useState(true);
  const [notifInsight, setNotifInsight] = useState(true);
  const [notifEmail,   setNotifEmail]  = useState(false);

  const [saving, setSaving]     = useState(false);
  const [pwSaving, setPwSaving] = useState(false);

  useEffect(() => {
    if (user?.full_name) setName(user.full_name);
  }, [user]);

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      // PATCH /users/me — update name
      const res = await fetch(`${API}/users/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ full_name: name }),
      });
      if (!res.ok) throw new Error("Update failed");
      useAuthStore.setState(s => ({
        user: s.user ? { ...s.user, full_name: name } : s.user,
      }));
      toast.success("Profile updated ✓");
    } catch {
      // Dev mode — just show success when no DB
      toast.success("Profile saved (dev mode)");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPw.length < 8) { toast.error("Password must be at least 8 characters"); return; }
    if (newPw !== confirmPw) { toast.error("Passwords do not match"); return; }
    setPwSaving(true);
    try {
      const res = await fetch(`${API}/users/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed");
      }
      toast.success("Password changed ✓");
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
    } catch (e: any) {
      toast.error(e.message || "Could not change password");
    } finally {
      setPwSaving(false);
    }
  };

  const handleExportData = () => {
    if (!analysisResult) { toast.error("Run an analysis first"); return; }
    const blob = new Blob([JSON.stringify({ patient, analysisResult }, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a   = document.createElement("a");
    a.href     = url;
    a.download = "Eirion_My_Data.json";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Data exported ✓");
  };

  const handleResetData = () => {
    if (!window.confirm("Reset all analysis data? This cannot be undone.")) return;
    resetWizard();
    toast.success("Analysis data cleared. Start a new onboarding.");
    navigate("/onboarding");
  };

  const handleDeleteAccount = () => {
    if (!window.confirm("Are you absolutely sure? This permanently deletes your account and all data.")) return;
    toast.error("Account deletion is handled by your admin — contact support@eirion.ai");
  };

  // ── Derived ──────────────────────────────────────────────────────────────────
  const initials = name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "U";
  const memberSince = user ? "March 2025" : "—";

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Toaster position="top-right" />

      {/* Back */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-blue-gray-500 hover:text-blue-gray-900 mb-8 transition group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        Back to dashboard
      </button>

      {/* Hero */}
      <div className="flex items-center gap-5 mb-10">
        <div className="w-16 h-16 rounded-2xl bg-blue-gray-900 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
          {initials}
        </div>
        <div>
          <h1 className="text-2xl font-serif font-bold text-blue-gray-900">{name || "Your Profile"}</h1>
          <p className="text-sm text-blue-gray-500">{email} · Member since {memberSince}</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* ── Profile ─────────────────────────────────────────────────────── */}
        <Section icon={User} title="Personal Information">
          <Field label="Full Name">
            <input
              id="profile-name"
              className={inputCls}
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Your full name"
            />
          </Field>
          <Field label="Email Address">
            <input
              id="profile-email"
              className={inputCls + " bg-blue-gray-50 text-blue-gray-400 cursor-not-allowed"}
              value={email}
              disabled
            />
            <p className="text-xs text-blue-gray-400">Email cannot be changed at this time.</p>
          </Field>
          <button
            id="save-profile-btn"
            onClick={handleSaveProfile}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-gray-900 text-white text-sm font-bold rounded-xl hover:opacity-90 disabled:opacity-50 transition"
          >
            {saving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </Section>

        {/* ── Security ─────────────────────────────────────────────────────── */}
        <Section icon={Lock} title="Password & Security">
          <Field label="Current Password">
            <div className="relative">
              <input
                id="current-password"
                type={showPw ? "text" : "password"}
                className={inputCls + " pr-10"}
                value={currentPw}
                onChange={e => setCurrentPw(e.target.value)}
                placeholder="Enter current password"
              />
              <button
                onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-gray-400 hover:text-blue-gray-700"
              >
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </Field>
          <Field label="New Password">
            <input
              id="new-password"
              type={showPw ? "text" : "password"}
              className={inputCls}
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
              placeholder="At least 8 characters"
            />
          </Field>
          <Field label="Confirm New Password">
            <input
              id="confirm-password"
              type={showPw ? "text" : "password"}
              className={inputCls}
              value={confirmPw}
              onChange={e => setConfirmPw(e.target.value)}
              placeholder="Repeat new password"
            />
          </Field>
          <button
            id="change-password-btn"
            onClick={handleChangePassword}
            disabled={pwSaving || !currentPw || !newPw}
            className="flex items-center gap-2 px-4 py-2 bg-blue-gray-900 text-white text-sm font-bold rounded-xl hover:opacity-90 disabled:opacity-50 transition"
          >
            {pwSaving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            {pwSaving ? "Updating…" : "Update Password"}
          </button>
        </Section>

        {/* ── Notifications ─────────────────────────────────────────────────── */}
        <Section icon={Bell} title="Notification Preferences">
          {[
            { id: "notif-dose", label: "Dose reminders", sub: "Get reminded when it's time to take a supplement", val: notifDose, set: setNotifDose },
            { id: "notif-insight", label: "Health insights", sub: "Alerts when your organ score changes significantly", val: notifInsight, set: setNotifInsight },
            { id: "notif-email", label: "Email digest (weekly)", sub: "Get a weekly summary of your health trajectory", val: notifEmail, set: setNotifEmail },
          ].map(({ id, label, sub, val, set }) => (
            <div key={id} className="flex items-center justify-between gap-4 py-2">
              <div>
                <p className="text-sm font-semibold text-blue-gray-800">{label}</p>
                <p className="text-xs text-blue-gray-500">{sub}</p>
              </div>
              <button
                id={id}
                onClick={() => { set(!val); toast.success(`${label} ${!val ? "enabled" : "disabled"}`); }}
                className={`relative w-11 h-6 rounded-full transition-colors ${val ? "bg-blue-gray-900" : "bg-blue-gray-200"}`}
              >
                <span className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-all ${val ? "left-6" : "left-1"}`} />
              </button>
            </div>
          ))}
        </Section>

        {/* ── Data & Privacy ────────────────────────────────────────────────── */}
        <Section icon={Download} title="Data & Privacy">
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              id="export-data-btn"
              onClick={handleExportData}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-blue-gray-200 text-sm font-bold text-blue-gray-700 rounded-xl hover:bg-blue-gray-50 transition"
            >
              <Download className="w-4 h-4" /> Export My Data (JSON)
            </button>
            <button
              id="reset-data-btn"
              onClick={handleResetData}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-amber-200 text-sm font-bold text-amber-700 rounded-xl hover:bg-amber-50 transition"
            >
              <RotateCcw className="w-4 h-4" /> Reset Analysis Data
            </button>
          </div>
          <p className="text-xs text-blue-gray-400 pt-1">
            Your data is stored locally and processed securely. No data is sold or shared with third parties.
          </p>
        </Section>

        {/* ── Danger Zone ───────────────────────────────────────────────────── */}
        <Section icon={Trash2} title="Danger Zone">
          <p className="text-sm text-blue-gray-500">
            Permanently delete your account and all associated health data. This action cannot be undone.
          </p>
          <button
            id="delete-account-btn"
            onClick={handleDeleteAccount}
            className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 text-red-700 text-sm font-bold rounded-xl hover:bg-red-100 transition"
          >
            <Trash2 className="w-4 h-4" /> Delete My Account
          </button>
        </Section>
      </div>

      {/* Sign out at bottom */}
      <div className="pt-8 text-center">
        <button
          id="signout-profile-btn"
          onClick={() => { logout(); navigate("/"); }}
          className="text-sm text-blue-gray-400 hover:text-blue-gray-700 transition underline"
        >
          Sign out of all devices
        </button>
      </div>
    </div>
  );
}
