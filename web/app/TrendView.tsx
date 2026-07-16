"use client";

import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { isTracked, type Feature } from "./types";

const shortDate = (d: string) => d.slice(5); // MM-DD

// distinct hues so several feature lines stay legible on one chart
const LINE_COLORS = [
  "#7c3aed", // violet
  "#0ea5e9", // sky
  "#f59e0b", // amber
  "#ec4899", // pink
  "#10b981", // emerald
  "#6366f1", // indigo
  "#ef4444", // red
  "#14b8a6", // teal
];

type Series = { feature: string; product: string };

// For each feature, follow the routing share of the product we track to win
// (Vault or Terraform). Features with no tracked contender are left to the
// per-feature cards below.
function trackedSeries(features: Feature[]): Series[] {
  const out: Series[] = [];
  for (const f of features) {
    const product = Object.keys(f.trend ?? {}).find(isTracked);
    if (product && (f.trend[product]?.length ?? 0) > 0) {
      out.push({ feature: f.feature, product });
    }
  }
  return out;
}

export function TrendView({ features, dates }: { features: Feature[]; dates: string[] }) {
  const series = trackedSeries(features);
  // A trend needs at least two days and one tracked line to be worth showing.
  if (dates.length < 2 || series.length === 0) return null;

  const byFeature = new Map(features.map((f) => [f.feature, f]));

  const rows = dates.map((date) => {
    const row: Record<string, number | string> = { date: shortDate(date) };
    for (const s of series) {
      const trend = byFeature.get(s.feature)?.trend[s.product] ?? [];
      const hit = trend.find((t) => t.date === date);
      if (hit) row[s.feature] = Math.round(hit.routing_share * 100);
    }
    return row;
  });

  const skipped = features.length - series.length;

  return (
    <section>
      <h2 className="mb-1 text-xl font-bold">Ownership trend</h2>
      <p className="mb-6 text-sm text-slate-500">
        Routing share of the product we track to win (
        <span className="text-violet-600">Vault / Terraform</span>) for each
        feature, over time. A single snapshot is a demo — the movement is the
        point.
        {skipped > 0 && (
          <>
            {" "}
            {skipped} feature{skipped === 1 ? "" : "s"} without a tracked
            contender {skipped === 1 ? "is" : "are"} shown in the cards below.
          </>
        )}
      </p>
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={rows} margin={{ left: -12, right: 12, top: 4, bottom: 0 }}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              unit="%"
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(v, name) => [`${v}%`, name as string]}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {series.map((s, i) => (
              <Line
                key={s.feature}
                type="monotone"
                dataKey={s.feature}
                name={`${s.feature} (${s.product})`}
                stroke={LINE_COLORS[i % LINE_COLORS.length]}
                strokeWidth={2}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
