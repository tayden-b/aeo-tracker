export type Sentiment = { positive: number; neutral: number; negative: number };

export type Product = {
  product: string;
  routing_share: number;
  mention_rate: number;
  avg_position: number | null;
  sentiment: Sentiment;
  attributes: string[];
};

export type TrendPoint = { date: string; routing_share: number };

export type Feature = {
  category: string;
  feature: string;
  leader: string | null;
  leaderboard: Product[];
  by_provider: Record<string, { product: string; routing_share: number }[]>;
  trend: Record<string, TrendPoint[]>;
};

export type Overview = {
  features: number;
  engines: number;
  engine_names: string[];
  samples: number;
  dates: number;
  tracked_leads: Record<string, number>;
};

export type Data = {
  generated_at: string;
  latest_date: string;
  dates: string[];
  providers: string[];
  overview: Overview;
  features: Feature[];
};

export type Recommendation = {
  feature: string;
  target: string;
  target_share: number;
  leader: string;
  leader_share: number;
  brief: string;
};

export type Recs = { recommendations: Recommendation[]; alerts: { message: string }[] };

export const TRACKED = new Set(["HashiCorp Vault", "Terraform"]);
export const isTracked = (name: string) => TRACKED.has(name);

// consistent palette across charts
export const COLORS = {
  tracked: "#7c3aed", // violet — products we track to win
  leader: "#10b981", // emerald — current leader
  other: "#38bdf8", // sky — everyone else
  pos: "#10b981",
  neu: "#cbd5e1",
  neg: "#f43f5e",
};
export function barColor(name: string, isLeader: boolean) {
  if (isTracked(name)) return COLORS.tracked;
  return isLeader ? COLORS.leader : COLORS.other;
}
