// DoseReminderSetup — compact card for setting reminders per regimen item
import { useState } from "react";
import { useNotificationStore } from "../../store/notificationStore";
import { useAuthStore } from "../../store/authStore";
import { useWizardStore } from "../../store/wizardStore";

const TIME_OPTIONS = ["07:00", "08:00", "09:00", "12:00", "13:00", "18:00", "20:00", "21:00", "22:00"];
const DAY_OPTIONS = ["daily", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function DoseReminderSetup() {
  const { regimen } = useWizardStore();
  const { schedule } = useNotificationStore();
  const { token } = useAuthStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [time, setTime] = useState("08:00");
  const [days, setDays] = useState<string[]>(["daily"]);
  const [success, setSuccess] = useState<string | null>(null);

  if (!regimen || regimen.length === 0) return null;

  const toggleDay = (day: string) => {
    if (day === "daily") {
      setDays(["daily"]);
      return;
    }
    const filtered = days.filter((d) => d !== "daily");
    setDays(filtered.includes(day) ? filtered.filter((d) => d !== day) : [...filtered, day]);
  };

  const handleSchedule = async () => {
    if (!selectedId) return;
    const item = regimen.find((r) => r.compound_id === selectedId);
    if (!item) return;
    await schedule(token, {
      compound_id: item.compound_id,
      display_name: item.compound_id.replace(/_/g, " "),
      time_of_day: time,
      days: days.length > 0 ? days : ["daily"],
      dose_label: item.dose_mg ? `${item.dose_mg}mg` : undefined,
    });
    setSuccess(item.compound_id.replace(/_/g, " "));
    setTimeout(() => setSuccess(null), 3000);
    setSelectedId(null);
  };

  return (
    <div className="bg-white rounded-2xl border border-blue-gray-100 shadow-sm p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">💊</span>
        <h3 className="text-sm font-black text-blue-gray-900">Dose Reminders</h3>
      </div>

      {success && (
        <div className="mb-3 bg-brand-green/10 border border-brand-green/20 rounded-xl px-4 py-2">
          <p className="text-xs text-brand-green font-bold">✓ Reminder set for {success}</p>
        </div>
      )}

      {/* Supplement selector */}
      <div className="mb-3">
        <label className="text-[11px] text-blue-gray-500 font-bold mb-1 block">Select supplement</label>
        <div className="grid grid-cols-2 gap-2">
          {regimen.map((item) => (
            <button
              key={item.compound_id}
              onClick={() => setSelectedId(item.compound_id === selectedId ? null : item.compound_id)}
              className={`text-left px-3 py-2 rounded-xl text-xs font-bold border transition truncate ${
                selectedId === item.compound_id
                  ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                  : "bg-blue-gray-50 border-blue-gray-100 text-blue-gray-700 hover:border-blue-gray-300"
              }`}
            >
              {item.compound_id.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {selectedId && (
        <>
          {/* Time picker */}
          <div className="mb-3">
            <label className="text-[11px] text-blue-gray-500 font-bold mb-1 block">Time</label>
            <div className="flex flex-wrap gap-1.5">
              {TIME_OPTIONS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTime(t)}
                  className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border transition ${
                    time === t
                      ? "bg-indigo-500 text-white border-indigo-500"
                      : "border-blue-gray-200 text-blue-gray-600 hover:border-indigo-300"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Day picker */}
          <div className="mb-4">
            <label className="text-[11px] text-blue-gray-500 font-bold mb-1 block">Days</label>
            <div className="flex flex-wrap gap-1.5">
              {DAY_OPTIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => toggleDay(d)}
                  className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border transition ${
                    days.includes(d)
                      ? "bg-indigo-500 text-white border-indigo-500"
                      : "border-blue-gray-200 text-blue-gray-600 hover:border-indigo-300"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleSchedule}
            className="w-full py-2.5 rounded-xl text-sm font-black text-white bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 transition shadow-sm"
          >
            Set Reminder ⏰
          </button>
        </>
      )}
    </div>
  );
}
