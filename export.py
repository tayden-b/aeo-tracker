"""
Export rollups → a JSON snapshot the dashboard reads.

The clean seam between the Python backend (owns data) and the frontend (renders
this file). Produces: an overview KPI block, and per-feature leaderboards with
routing share, mention rate, avg position, sentiment, top positioning attributes,
per-engine breakdown, and a routing-share trend across dates.

    python export.py   ->   web/public/data.json
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import db
from metrics import normalize

OUT = Path(__file__).parent / "web" / "public" / "data.json"


def _attributes_for_latest(conn, latest: str) -> dict[tuple, list[str]]:
    """(feature, normalized product) -> top descriptive attributes on the latest date."""
    rows = conn.execute(
        "SELECT r.feature AS feature, rt.product AS product, rt.attributes AS attrs "
        "FROM routings rt JOIN runs r ON rt.run_id = r.id WHERE r.run_date = ?",
        (latest,),
    ).fetchall()
    counts: dict[tuple, Counter] = defaultdict(Counter)
    for row in rows:
        prod = normalize(row["product"])
        try:
            attrs = json.loads(row["attrs"] or "[]")
        except (json.JSONDecodeError, TypeError):
            attrs = []
        for a in attrs:
            a = (a or "").strip().lower()
            if a:
                counts[(row["feature"], prod)][a] += 1
    return {k: [a for a, _ in c.most_common(6)] for k, c in counts.items()}


def export() -> Path:
    conn = db.connect()
    db.init_db(conn)
    dates = db.distinct_run_dates(conn)
    latest = dates[-1] if dates else None
    rollups = [dict(r) for r in db.fetch_rollups(conn)]
    total_runs = conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"]
    attrs_map = _attributes_for_latest(conn, latest) if latest else {}

    feats: dict[tuple, dict] = {}
    for r in rollups:
        key = (r["category"], r["feature"])
        feats.setdefault(key, {"rows": []})["rows"].append(r)

    features = []
    for (category, feature), data in sorted(feats.items()):
        rows = data["rows"]

        blended_latest = [
            {
                "product": r["product"],
                "routing_share": r["routing_share"],
                "mention_rate": r["mention_rate"],
                "avg_position": r["avg_position"],
                "sentiment": {
                    "positive": r["sentiment_positive"],
                    "neutral": r["sentiment_neutral"],
                    "negative": r["sentiment_negative"],
                },
                "attributes": attrs_map.get((feature, r["product"]), []),
            }
            for r in rows
            if r["provider"] == "blended" and r["run_date"] == latest
        ]
        blended_latest.sort(key=lambda p: (p["routing_share"], p["mention_rate"]), reverse=True)
        leaderboard = [
            p for p in blended_latest
            if p["routing_share"] > 0 or p["mention_rate"] >= 0.5
        ][:8]
        shown = {p["product"] for p in leaderboard}

        # per-engine routing (latest), limited to shown products
        by_provider: dict[str, list] = defaultdict(list)
        for r in rows:
            if r["provider"] != "blended" and r["run_date"] == latest and r["product"] in shown:
                by_provider[r["provider"]].append(
                    {"product": r["product"], "routing_share": r["routing_share"]}
                )
        for p in by_provider.values():
            p.sort(key=lambda x: x["routing_share"], reverse=True)

        # routing-share trend across dates (blended), per shown product
        trend: dict[str, list] = defaultdict(list)
        for r in rows:
            if r["provider"] == "blended" and r["product"] in shown:
                trend[r["product"]].append(
                    {"date": r["run_date"], "routing_share": r["routing_share"]}
                )
        for series in trend.values():
            series.sort(key=lambda x: x["date"])

        features.append({
            "category": category,
            "feature": feature,
            "leader": leaderboard[0]["product"] if leaderboard else None,
            "leaderboard": leaderboard,
            "by_provider": dict(by_provider),
            "trend": dict(trend),
        })

    providers = sorted({r["provider"] for r in rollups if r["provider"] != "blended"})

    # overview: how many features each tracked product leads
    tracked = {"HashiCorp Vault", "Terraform"}
    leads = Counter(f["leader"] for f in features if f["leader"] in tracked)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_date": latest,
        "dates": dates,
        "providers": providers,
        "overview": {
            "features": len(features),
            "engines": len(providers),
            "engine_names": providers,
            "samples": total_runs,
            "dates": len(dates),
            "tracked_leads": dict(leads),
        },
        "features": features,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    return OUT


if __name__ == "__main__":
    print(f"Wrote {export()}")
