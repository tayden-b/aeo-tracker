"""
Export rollups → a JSON snapshot the dashboard reads.

This is the clean seam between the Python backend and the frontend: the backend
owns data, the dashboard just renders this file. (Static-friendly: the Next.js
app can read it at build time and deploy to Vercel with no live DB.)

    python export.py   ->   web/public/data.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import db

OUT = Path(__file__).parent / "web" / "public" / "data.json"


def export() -> Path:
    conn = db.connect()
    db.init_db(conn)
    dates = db.distinct_run_dates(conn)
    latest = dates[-1] if dates else None
    rollups = [dict(r) for r in db.fetch_rollups(conn)]

    # group rollups by feature
    feats: dict[tuple, dict] = {}
    for r in rollups:
        key = (r["category"], r["feature"])
        feats.setdefault(key, {"category": r["category"], "feature": r["feature"],
                               "rows": []})
        feats[key]["rows"].append(r)

    features = []
    for (category, feature), data in sorted(feats.items()):
        rows = data["rows"]
        # blended + latest date = the headline leaderboard
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
            }
            for r in rows
            if r["provider"] == "blended" and r["run_date"] == latest
        ]
        blended_latest.sort(key=lambda p: p["routing_share"], reverse=True)

        # per-provider leaderboards (latest date)
        by_provider: dict[str, list] = defaultdict(list)
        for r in rows:
            if r["provider"] != "blended" and r["run_date"] == latest:
                by_provider[r["provider"]].append(
                    {"product": r["product"], "routing_share": r["routing_share"]}
                )
        for p in by_provider.values():
            p.sort(key=lambda x: x["routing_share"], reverse=True)

        # routing-share trend over dates (blended), per product
        trend: dict[str, list] = defaultdict(list)
        for r in rows:
            if r["provider"] == "blended":
                trend[r["product"]].append(
                    {"date": r["run_date"], "routing_share": r["routing_share"]}
                )
        for series in trend.values():
            series.sort(key=lambda x: x["date"])

        features.append({
            "category": category,
            "feature": feature,
            "leaderboard": blended_latest,
            "by_provider": dict(by_provider),
            "trend": dict(trend),
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_date": latest,
        "dates": dates,
        "providers": sorted({r["provider"] for r in rollups if r["provider"] != "blended"}),
        "features": features,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    return OUT


if __name__ == "__main__":
    path = export()
    print(f"Wrote {path}")
