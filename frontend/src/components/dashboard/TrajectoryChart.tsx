import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, ComposedChart, Line,
} from "recharts";
import { TrajectoryPoint } from "../../types";

interface Props {
  data: TrajectoryPoint[];
}

export default function TrajectoryChart({ data }: Props) {
  const chartData = data.map((d) => ({
    ...d,
    xAxisLabel: d.year === 0 ? "Now" : `Year ${d.year}`,
    // ±5 confidence interval band around the current path
    ci_upper: +(d.liver_index + 5).toFixed(1),
    ci_lower: +(d.liver_index - 5).toFixed(1),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const current = payload.find((p: any) => p.dataKey === "liver_index");
      const optimized = payload.find((p: any) => p.dataKey === "optimized_liver_index");
      return (
        <div className="bg-white p-4 border border-blue-gray-100 shadow-xl rounded-xl text-sm min-w-[180px]">
          <p className="font-bold text-blue-gray-900 mb-3 border-b border-blue-gray-100 pb-2">{label}</p>
          <div className="space-y-2">
            {current && (
              <p className="flex justify-between gap-4">
                <span className="text-blue-gray-500">Current Path</span>
                <span className="font-bold text-amber-500">{Number(current.value).toFixed(1)}</span>
              </p>
            )}
            {optimized && optimized.value && (
              <p className="flex justify-between gap-4">
                <span className="text-blue-gray-500">Optimized</span>
                <span className="font-bold text-emerald-500">{Number(optimized.value).toFixed(1)}</span>
              </p>
            )}
            {current && (
              <p className="flex justify-between gap-4 border-t border-blue-gray-50 pt-2">
                <span className="text-blue-gray-400 text-xs">Confidence ±5</span>
                <span className="text-blue-gray-400 text-xs">
                  {(Number(current.value) - 5).toFixed(0)}–{(Number(current.value) + 5).toFixed(0)}
                </span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = () => (
    <div className="flex items-center gap-6 justify-end pr-2 pb-2 text-xs text-blue-gray-500 font-medium">
      <div className="flex items-center gap-1.5">
        <div className="w-8 h-0.5 bg-amber-400 rounded" />
        Current Path
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-8 h-0.5 bg-emerald-500 rounded border-dashed" style={{ borderTop: "2px dashed #10b981", background: "none" }} />
        Optimized
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-8 h-3 rounded opacity-40" style={{ background: "rgba(251,191,36,0.25)" }} />
        ±5 Confidence
      </div>
    </div>
  );

  return (
    <div className="w-full">
      <CustomLegend />
      <div className="h-[320px] w-full mt-1">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis
              dataKey="xAxisLabel"
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
            <Tooltip content={<CustomTooltip />} />

            {/* Reference bands */}
            <ReferenceLine y={85} stroke="#10b981" strokeDasharray="3 3" opacity={0.4}
              label={{ position: "insideTopLeft", value: "Optimal (85+)", fill: "#10b981", fontSize: 10 }} />
            <ReferenceLine y={70} stroke="#f59e0b" strokeDasharray="3 3" opacity={0.4}
              label={{ position: "insideTopLeft", value: "Warning (70–84)", fill: "#f59e0b", fontSize: 10 }} />

            {/* ±5 confidence interval shaded band */}
            <Area
              type="monotone"
              dataKey="ci_upper"
              stroke="none"
              fill="#fbbf24"
              fillOpacity={0.12}
              legendType="none"
              tooltipType="none"
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="ci_lower"
              stroke="none"
              fill="#fbbf24"
              fillOpacity={0}
              legendType="none"
              tooltipType="none"
              activeDot={false}
            />

            {/* Current trajectory */}
            <Line
              type="monotone"
              dataKey="liver_index"
              stroke="#f59e0b"
              strokeWidth={3}
              dot={{ r: 5, strokeWidth: 2, fill: "#fff", stroke: "#f59e0b" }}
              activeDot={{ r: 7, strokeWidth: 0, fill: "#f59e0b" }}
              name="Current Path"
            />

            {/* Optimized trajectory — dashed green */}
            <Line
              type="monotone"
              dataKey="optimized_liver_index"
              stroke="#10b981"
              strokeWidth={3}
              strokeDasharray="6 4"
              dot={{ r: 5, strokeWidth: 2, fill: "#fff", stroke: "#10b981" }}
              activeDot={{ r: 7, strokeWidth: 0, fill: "#10b981" }}
              name="Optimized Plan"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
