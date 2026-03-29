// Zustand auth store — persists JWT token and user profile to localStorage

import { create } from "zustand";
import { persist } from "zustand/middleware";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  onboarding_complete: boolean;
  created_at: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
  markOnboardingComplete: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      login: async (email, password) => {
        set({ loading: true, error: null });
        try {
          const res = await fetch(`${API}/users/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Login failed" }));
            throw new Error(err.detail ?? "Login failed");
          }
          const data = await res.json();
          set({ token: data.token, user: data.user, isAuthenticated: true, loading: false });
        } catch (e: unknown) {
          set({ loading: false, error: e instanceof Error ? e.message : "Login failed" });
          throw e;
        }
      },

      register: async (email, password, full_name) => {
        set({ loading: true, error: null });
        try {
          const res = await fetch(`${API}/users/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, full_name }),
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Registration failed" }));
            throw new Error(err.detail ?? "Registration failed");
          }
          const data = await res.json();
          set({ token: data.token, user: data.user, isAuthenticated: true, loading: false });
        } catch (e: unknown) {
          set({ loading: false, error: e instanceof Error ? e.message : "Registration failed" });
          throw e;
        }
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false, error: null });
      },

      markOnboardingComplete: async () => {
        const token = get().token;
        if (!token) return;
        try {
          await fetch(`${API}/users/onboarding-complete`, {
            method: "PATCH",
            headers: { Authorization: `Bearer ${token}` },
          });
          set((s) => ({ user: s.user ? { ...s.user, onboarding_complete: true } : s.user }));
        } catch (_) {/* silent */ }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "eirion-auth",
      partialize: (s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated }),
    }
  )
);
