import fs from "fs";
import path from "path";

// --- types matching the Python export ---
type Sentiment = { positive: number; neutral: number; negative: number };
type Product = {
  product: string;
  routing_share: number;
  mention_rate: number;
  avg_position: number | null;
  sentiment: Sentiment;
};
type Feature = {
  category: string;
  feature: string;
  leaderboard: Product[];
};
type Data = {
  generated_at: string;
  latest_date: string;
  providers: string[];
  features: Feature[];
};
type Recommendation = {
  feature: string;
  target: string;
  target_share: number;
  leader: string;
  leader_share: number;
  brief: string;
};
type Recs = { recommendations: Recommendation[]; alerts: { message: string }[] };

function read<T>(file: string, fallback: T): T {
  try {
    return JSON.parse(
      fs.readFileSync(path.join(process.cwd(), "public", file), "utf8")
    ) as T;
  } catch {
    return fallback;
  }
}

const isTarget = (name: string) => /vault|terraform/i.test(name);

function Bar({ p, leader }: { p: Product; leader: boolean }) {
  const pct = Math.round(p.routing_share * 100);
  const target = isTarget(p.product);
  const color = target ? "bg-violet-600" : leader ? "bg-emerald-500" : "bg-sky-400";
  return (
    <div className="flex items-center gap-3 text-sm">
      <div
        className={`w-44 shrink-0 truncate ${
          target ? "font-semibold text-violet-700" : "text-slate-700"
        }`}
      >
        {p.product}
      </div>
      <div className="relative h-6 flex-1 rounded bg-slate-100">
        <div
          className={`h-6 rounded ${color}`}
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>
      <div className="w-12 shrink-0 text-right font-mono font-semibold tabular-nums">
        {pct}%
      </div>
    </div>
  );
}

export default function Home() {
  const data = read<Data>("data.json", {
    generated_at: "",
    latest_date: "—",
    providers: [],
    features: [],
  });
  const recs = read<Recs>("recommendations.json", {
    recommendations: [],
    alerts: [],
  });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto max-w-5xl px-6 py-10">
          <div className="text-sm font-medium uppercase tracking-widest text-violet-300">
            AEO Tracker
          </div>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Which product does AI route developers to — by feature?
          </h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            For each developer capability, we ask AI answer engines who they
            recommend, many times over, and measure{" "}
            <strong>feature ownership</strong>: the share of answers that name
            each product as the default.
          </p>
          <div className="mt-5 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-400">
            <span>
              Latest run:{" "}
              <span className="text-slate-200">{data.latest_date}</span>
            </span>
            <span>
              Engines:{" "}
              <span className="text-slate-200">
                {data.providers.join(", ") || "—"}
              </span>
            </span>
            <span>
              Features tracked:{" "}
              <span className="text-slate-200">{data.features.length}</span>
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-12 px-6 py-12">
        <section>
          <h2 className="mb-1 text-xl font-bold">Feature ownership</h2>
          <p className="mb-6 text-sm text-slate-500">
            Routing share = share of sampled answers naming each product as the
            primary recommendation. Violet = products we track to win.
          </p>
          <div className="grid gap-5 lg:grid-cols-2">
            {data.features.map((f) => (
              <div
                key={f.feature}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className="mb-1 flex items-center justify-between gap-2">
                  <h3 className="text-lg font-semibold capitalize">
                    {f.feature}
                  </h3>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                    {f.category}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  {f.leaderboard.map((p, i) => (
                    <Bar key={p.product} p={p} leader={i === 0} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {recs.recommendations.length > 0 && (
          <section>
            <h2 className="mb-1 text-xl font-bold">Recommendations</h2>
            <p className="mb-6 text-sm text-slate-500">
              Where a tracked product isn&apos;t the AI&apos;s default — and what
              could shift the answer. Generated from the data.
            </p>
            <div className="space-y-4">
              {recs.recommendations.map((r) => (
                <div
                  key={r.feature + r.target}
                  className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
                    <span className="font-semibold capitalize text-violet-700">
                      {r.target}
                    </span>
                    <span className="text-slate-500">
                      {Math.round(r.target_share * 100)}% on
                    </span>
                    <span className="font-medium capitalize">{r.feature}</span>
                    <span className="text-slate-400">
                      · leader {r.leader} ({Math.round(r.leader_share * 100)}%)
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-slate-700">
                    {r.brief}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-slate-200 py-8 text-center text-xs text-slate-400">
        AEO Tracker · feature-level answer-engine optimization · data generated{" "}
        {data.generated_at
          ? new Date(data.generated_at).toLocaleString()
          : "—"}
      </footer>
    </div>
  );
}
