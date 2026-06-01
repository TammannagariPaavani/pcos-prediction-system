import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export default function SHAPChart({ features = [] }) {
  return (
    <div className="metric-card h-[360px]">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Explainability</p>
        <h3 className="mt-2 text-2xl">Top Contributing Factors</h3>
      </div>
      <div className="pointer-events-none h-[85%]">
        <ResponsiveContainer width="100%" height="100%">
        <BarChart data={features} layout="vertical" margin={{ top: 10, right: 10, left: 20, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#D9E4E8" />
          <XAxis type="number" />
          <YAxis dataKey="feature" type="category" width={140} />
          <Tooltip formatter={(value) => Number(value).toFixed(3)} />
          <Bar dataKey="impact" fill="#E86A33" radius={[0, 12, 12, 0]} />
        </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
