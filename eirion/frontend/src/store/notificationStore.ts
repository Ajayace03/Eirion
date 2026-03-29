// Notification store — fetches from /notifications API and manages bell state

import { create } from "zustand";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface AppNotification {
  id: string;
  type: "dose_reminder" | "system" | "insight";
  title: string;
  body: string;
  compound_id?: string;
  is_read: boolean;
  created_at: string;
  scheduled_for?: string;
}

interface NotificationState {
  notifications: AppNotification[];
  unreadCount: number;
  open: boolean;
  fetch: (token: string | null) => Promise<void>;
  schedule: (token: string | null, payload: SchedulePayload) => Promise<void>;
  markAllRead: (token: string | null) => Promise<void>;
  setOpen: (open: boolean) => void;
}

interface SchedulePayload {
  compound_id: string;
  display_name: string;
  time_of_day: string;
  days: string[];
  dose_label?: string;
}

export const useNotificationStore = create<NotificationState>()((set, get) => ({
  notifications: [],
  unreadCount: 0,
  open: false,

  fetch: async (token) => {
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API}/notifications`, { headers });
      if (!res.ok) return;
      const data: AppNotification[] = await res.json();
      set({ notifications: data, unreadCount: data.filter((n) => !n.is_read).length });
    } catch (_) {/* offline */ }
  },

  schedule: async (token, payload) => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API}/notifications/schedule`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const notif: AppNotification = await res.json();
      set((s) => ({
        notifications: [notif, ...s.notifications],
        unreadCount: s.unreadCount + 1,
      }));
      // Browser push notification
      if (Notification.permission === "granted") {
        new Notification(`⏰ ${notif.title}`, { body: notif.body, icon: "/icon.png" });
      }
    }
  },

  markAllRead: async (token) => {
    const ids = get().notifications.filter((n) => !n.is_read).map((n) => n.id);
    if (!ids.length) return;
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    await fetch(`${API}/notifications/mark-read`, {
      method: "POST",
      headers,
      body: JSON.stringify({ notification_ids: ids }),
    });
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    }));
  },

  setOpen: (open) => set({ open }),
}));
