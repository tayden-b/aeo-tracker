import fs from "fs";
import path from "path";
import { FeatureCard } from "./FeatureCard";
import { TrendView } from "./TrendView";
import { isTracked, type Data, type Recs } from "./types";

function read<T>(file: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public", file), "utf8")) as T;
  } catch {
    return fallback;
  }
}

const EMPTY: Data = {
  generated_at: "",
  latest_date: "—",
  dates: [],
  providers: [],
  overview: { features: 0, engines: 0, engine_names: [], samples: 0, dates: 0, tracked_leads: {} },
  features: [],
};

function Kpi({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export default function Home() {
  const data = read<Data>("data.json", EMPTY);
  const recs = read<Recs>("recommendations.json", { recommendations: [], alerts: [] });
  const o = data.overview ?? EMPTY.overview;
  const trackedLeads = Object.entries(o.tracked_leads ?? {});

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* header */}
      <header className="bg-gradient-to-br from-slate-900 to-slate-800 text-white">
        <div className="mx-auto max-w-6xl px-6 py-10">
          <div className="text-sm font-medium uppercase tracking-widest text-violet-300">
            AEO Tracker
          </div>
          <h1 className="mt-2 max-w-3xl text-3xl font-bold sm:text-4xl">
            Which product does AI route developers to — by feature?
          </h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            For each developer capability, we ask AI answer engines who they recommend,
            many times over, and measure <strong>feature ownership</strong> — the share of
            answers naming each product as the default — across engines and over time.
          </p>
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Kpi label="Features tracked" value={o.features} />
            <Kpi label="AI engines" value={o.engine_names.join(" · ") || "—"} />
            <Kpi label="Samples collected" value={o.samples} />
            <Kpi label="Days of data" value={o.dates} />
          </div>
          {trackedLeads.length > 0 && (
            <p className="mt-4 text-sm text-slate-400">
              {trackedLeads.map(([p, n]) => `${p} leads ${n} feature${n === 1 ? "" : "s"}`).join(" · ")}
            </p>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-12 px-6 py-12">
        {/* ownership trend over time */}
        <TrendView features={data.features} dates={data.dates} />

        {/* feature ownership */}
        <section>
          <h2 className="mb-1 text-xl font-bold">Feature ownership</h2>
          <p className="mb-6 text-sm text-slate-500">
            Routing share = share of sampled answers naming each product as the primary
            recommendation. <span className="text-violet-600">Violet</span> = products we
            track to win.
          </p>
          <div className="grid items-start gap-5 lg:grid-cols-2">
            {data.features.map((f) => (
              <FeatureCard key={f.feature} feature={f} />
            ))}
          </div>
        </section>

        {/* cross-engine matrix */}
        {data.providers.length > 1 && (
          <section>
            <h2 className="mb-1 text-xl font-bold">Cross-engine leaderboard</h2>
            <p className="mb-6 text-sm text-slate-500">
              Who each engine routes to first — they don&apos;t always agree.
            </p>
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wide text-slate-400">
                    <th className="px-4 py-3 font-medium">Feature</th>
                    {data.providers.map((p) => (
                      <th key={p} className="px-4 py-3 font-medium">{p}</th>
                    ))}
                    <th className="px-4 py-3 font-medium">Blended</th>
                  </tr>
                </thead>
                <tbody>
                  {data.features.map((f) => (
                    <tr key={f.feature} className="border-b border-slate-100 last:border-0">
                      <td className="px-4 py-3 font-medium capitalize text-slate-700">{f.feature}</td>
                      {data.providers.map((p) => {
                        const top = f.by_provider[p]?.[0];
                        return (
                          <td key={p} className="px-4 py-3 text-slate-600">
                            {top ? (
                              <span className={isTracked(top.product) ? "font-semibold text-violet-700" : ""}>
                                {top.product}{" "}
                                <span className="text-slate-400">{Math.round(top.routing_share * 100)}%</span>
                              </span>
                            ) : "—"}
                          </td>
                        );
                      })}
                      <td className="px-4 py-3">
                        <span className={f.leader && isTracked(f.leader) ? "font-semibold text-violet-700" : "text-slate-700"}>
                          {f.leader ?? "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* recommendations */}
        {recs.recommendations.length > 0 && (
          <section>
            <h2 className="mb-1 text-xl font-bold">Recommendations</h2>
            <p className="mb-6 text-sm text-slate-500">
              Where a tracked product isn&apos;t the AI&apos;s default — and what could shift the answer.
            </p>
            <div className="grid gap-4 lg:grid-cols-2">
              {recs.recommendations.map((r) => (
                <div key={r.feature + r.target} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
                    <span className="font-semibold capitalize text-violet-700">{r.target}</span>
                    <span className="text-slate-500">{Math.round(r.target_share * 100)}% on</span>
                    <span className="font-medium capitalize">{r.feature}</span>
                  </div>
                  <div className="mt-0.5 text-[12px] text-slate-400">
                    leader {r.leader} ({Math.round(r.leader_share * 100)}%)
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-slate-700">{r.brief}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-slate-200 py-8 text-center text-xs text-slate-400">
        AEO Tracker · feature-level answer-engine optimization · {data.providers.join(", ")} ·
        data generated {data.generated_at ? new Date(data.generated_at).toLocaleString() : "—"}
      </footer>
    </div>
  );
}
