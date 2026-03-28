import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function ProgressChart() {
  const [data, setData] = useState<{ date: string; score: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch("http://localhost:8000/history/my-progress", {
          headers: { Authorization: "Bearer bypass-string" },
        });
        const json = await res.json();
        if (json.history) {
          const formatted = json.history.map((record: any) => {
            const date = new Date(record.created_at);
            return {
              date: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
              score: record.score,
            };
          });
          setData(formatted);
        }
      } catch (e) {
        console.error("Failed to fetch history", e);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  if (loading) {
    return <div className="h-[300px] w-full mt-4 flex items-center justify-center text-blue-gray-400">Loading historical data...</div>;
  }

  if (data.length === 0) {
    return <div className="h-[300px] w-full mt-4 flex items-center justify-center text-blue-gray-400 border-2 border-dashed border-blue-gray-100 rounded-xl">No historical data available.</div>;
  }

  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis 
            dataKey="date" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: "#64748b", fontSize: 12 }} 
            dy={10}
          />
          <YAxis 
            domain={[40, 100]} 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: "#64748b", fontSize: 12 }} 
          />
          <Tooltip 
            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
            formatter={(value: any) => [value, "Liver Index"]}
          />
          <Area 
            type="monotone" 
            dataKey="score" 
            stroke="#10b981" 
            strokeWidth={3}
            fillOpacity={1} 
            fill="url(#colorScore)" 
            dot={{ r: 5, strokeWidth: 2, fill: "#fff", stroke: "#10b981" }}
            activeDot={{ r: 7, strokeWidth: 0, fill: "#10b981" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
