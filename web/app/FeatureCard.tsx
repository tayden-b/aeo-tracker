"use client";

import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { barColor, COLORS, isTracked, type Feature } from "./types";

const pct = (v: number) => `${Math.round(v * 100)}%`;
const shortDate = (d: string) => d.slice(5); // MM-DD

function Chips({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-[11px] font-medium text-slate-400">{label}</span>
      {items.map((a) => (
        <span
          key={a}
          className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600"
        >
          {a}
        </span>
      ))}
    </div>
  );
}

function SentimentBar({ s }: { s: { positive: number; neutral: number; negative: number } }) {
  const total = s.positive + s.neutral + s.negative || 1;
  const seg = (n: number, color: string) =>
    n > 0 ? <div style={{ width: `${(n / total) * 100}%`, background: color }} /> : null;
  return (
    <div className="flex h-2 w-full overflow-hidden rounded-full">
      {seg(s.positive, COLORS.pos)}
      {seg(s.neutral, COLORS.neu)}
      {seg(s.negative, COLORS.neg)}
    </div>
  );
}

export function FeatureCard({ feature }: { feature: Feature }) {
  const lb = feature.leaderboard;
  if (!lb.length) return null;
  const leader = lb[0];
  const tracked = lb.find((p) => isTracked(p.product));

  // routing bar data
  const barData = lb.map((p) => ({
    name: p.product,
    value: Math.round(p.routing_share * 100),
    isLeader: p.product === feature.leader,
  }));

  // trend data (top 3 products pivoted by date)
  const top = lb.slice(0, 3).map((p) => p.product);
  const dates = Array.from(
    new Set(top.flatMap((p) => (feature.trend[p] ?? []).map((t) => t.date))),
  ).sort();
  const trendData = dates.map((date) => {
    const row: Record<string, number | string> = { date: shortDate(date) };
    for (const p of top) {
      const hit = (feature.trend[p] ?? []).find((t) => t.date === date);
      if (hit) row[p] = Math.round(hit.routing_share * 100);
    }
    return row;
  });
  const hasTrend = dates.length > 1;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold capitalize text-slate-900">
            {feature.feature}
          </h3>
          <span className="text-[11px] uppercase tracking-wide text-slate-400">
            {feature.category}
          </span>
        </div>
        {feature.leader && (
          <span className="shrink-0 rounded-full bg-slate-900 px-3 py-1 text-[11px] font-medium text-white">
            owns it: {feature.leader}
          </span>
        )}
      </div>

      {/* routing share bars */}
      <ResponsiveContainer width="100%" height={barData.length * 34 + 8}>
        <BarChart layout="vertical" data={barData} margin={{ left: 0, right: 36, top: 2, bottom: 2 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="name"
            width={150}
            tick={{ fontSize: 12, fill: "#475569" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "#f1f5f9" }}
            formatter={(v) => [`${v}% routing share`, ""]}
            labelFormatter={() => ""}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false} label={{ position: "right", formatter: (v) => `${v ?? ""}%`, fontSize: 11, fill: "#64748b" }}>
            {barData.map((d) => (
              <Cell key={d.name} fill={barColor(d.name, d.isLeader)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* stat strip */}
      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-slate-50 py-2">
          <div className="text-[11px] text-slate-400">Leader mention</div>
          <div className="text-sm font-semibold text-slate-800">{pct(leader.mention_rate)}</div>
        </div>
        <div className="rounded-lg bg-slate-50 py-2">
          <div className="text-[11px] text-slate-400">Leader avg pos</div>
          <div className="text-sm font-semibold text-slate-800">{leader.avg_position ?? "—"}</div>
        </div>
        <div className="rounded-lg bg-slate-50 py-2">
          <div className="text-[11px] text-slate-400">Products seen</div>
          <div className="text-sm font-semibold text-slate-800">{lb.length}</div>
        </div>
      </div>

      {/* per-engine */}
      {Object.keys(feature.by_provider).length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.entries(feature.by_provider).map(([engine, list]) =>
            list[0] ? (
              <span
                key={engine}
                className="rounded-md border border-slate-200 px-2 py-1 text-[11px] text-slate-600"
              >
                <span className="font-mono uppercase text-slate-400">{engine}</span>{" "}
                → <span className="font-medium text-slate-800">{list[0].product}</span>{" "}
                {pct(list[0].routing_share)}
              </span>
            ) : null,
          )}
        </div>
      )}

      {/* sentiment + attributes for leader */}
      <div className="mt-4 space-y-2 border-t border-slate-100 pt-4">
        <div className="flex items-center gap-3">
          <span className="w-20 shrink-0 text-[11px] text-slate-400">Sentiment</span>
          <SentimentBar s={leader.sentiment} />
        </div>
        <Chips label="AI calls it" items={leader.attributes.slice(0, 5)} />
        {tracked && tracked.product !== leader.product && (
          <Chips label={`${tracked.product}:`} items={tracked.attributes.slice(0, 4)} />
        )}
      </div>

      {/* trend */}
      {hasTrend && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <div className="mb-1 text-[11px] text-slate-400">Routing share over time</div>
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={trendData} margin={{ left: -20, right: 8, top: 4, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }} />
              {top.map((p) => (
                <Line
                  key={p}
                  type="monotone"
                  dataKey={p}
                  stroke={barColor(p, p === feature.leader)}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
