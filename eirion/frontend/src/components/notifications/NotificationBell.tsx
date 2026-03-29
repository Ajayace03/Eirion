// NotificationBell — header bell with unread badge and dropdown
import { useEffect, useRef, useState } from "react";
import { useNotificationStore } from "../../store/notificationStore";
import { useAuthStore } from "../../store/authStore";

const TYPE_ICON: Record<string, string> = {
  dose_reminder: "💊",
  insight: "🧬",
  system: "🔔",
};

export default function NotificationBell() {
  const { notifications, unreadCount, open, fetch, markAllRead, setOpen } = useNotificationStore();
  const { token } = useAuthStore();
  const dropRef = useRef<HTMLDivElement>(null);
  const [permAsked, setPermAsked] = useState(false);

  // Request browser notification permission once
  useEffect(() => {
    if (!permAsked && "Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
      setPermAsked(true);
    }
  }, [permAsked]);

  // Poll notifications every 60s
  useEffect(() => {
    fetch(token);
    const id = setInterval(() => fetch(token), 60_000);
    return () => clearInterval(id);
  }, [token, fetch]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [setOpen]);

  return (
    <div className="relative" ref={dropRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative w-9 h-9 flex items-center justify-center rounded-xl bg-blue-gray-100 hover:bg-blue-gray-200 transition"
        aria-label="Notifications"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-gray-700">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] bg-brand-red text-white text-[10px] font-black rounded-full flex items-center justify-center px-1">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-12 w-80 bg-white rounded-2xl shadow-2xl border border-blue-gray-100 z-[100] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-blue-gray-100">
            <p className="text-sm font-black text-blue-gray-900">Notifications</p>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead(token)}
                className="text-[11px] font-bold text-indigo-500 hover:text-indigo-700 transition"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-blue-gray-50">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-2xl mb-2">🔔</p>
                <p className="text-sm text-blue-gray-500">All caught up!</p>
              </div>
            ) : (
              notifications.slice(0, 20).map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 px-4 py-3 transition ${n.is_read ? "opacity-60" : "bg-indigo-50/30"}`}
                >
                  <span className="text-lg shrink-0 mt-0.5">{TYPE_ICON[n.type] ?? "🔔"}</span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-bold text-blue-gray-900 ${!n.is_read ? "font-black" : ""}`}>
                      {n.title}
                    </p>
                    <p className="text-[11px] text-blue-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                    {n.scheduled_for && (
                      <p className="text-[10px] text-indigo-400 font-bold mt-1">⏰ {n.scheduled_for}</p>
                    )}
                  </div>
                  {!n.is_read && (
                    <div className="w-2 h-2 rounded-full bg-indigo-500 shrink-0 mt-1.5" />
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-blue-gray-100 bg-blue-gray-50/30">
            <p className="text-[10px] text-blue-gray-400 text-center">
              Set dose reminders via each supplement's card
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
