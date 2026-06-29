"""
M4 — the recommendation + alert layer (the "intelligence").

Reads the stored rollups and, for the products you care about winning (TARGETS),
finds the features where you're NOT the AI's default and drafts a short
product-marketing recommendation for each (an LLM turns the data into a brief —
the "recommendation agent"). Also emits simple change-alerts when a target's
routing share drops between runs.

    python recommend.py   ->   prints briefs + writes web/public/recommendations.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import db

load_dotenv()
client = OpenAI()
OUT = Path(__file__).parent / "web" / "public" / "recommendations.json"

# Products you want to win, mapped to the category they compete in.
TARGETS = {
    "HashiCorp Vault": "secrets-management",
    "Terraform": "iac",
}

DROP_ALERT_THRESHOLD = 0.20  # flag a >=20pt routing-share drop between runs


def _blended_by_feature(conn):
    """feature -> {date -> {product -> routing_share}}, plus category lookup."""
    rows = [dict(r) for r in db.fetch_rollups(conn) if r["provider"] == "blended"]
    data: dict = defaultdict(lambda: defaultdict(dict))
    category_of: dict[str, str] = {}
    for r in rows:
        data[r["feature"]][r["run_date"]][r["product"]] = r["routing_share"]
        category_of[r["feature"]] = r["category"]
    return data, category_of


def _brief(feature, target, target_share, leader, leader_share) -> str:
    """Use an LLM to draft a 2-3 sentence PMM recommendation from the data."""
    prompt = (
        f"You are a product marketer. For the developer capability '{feature}', "
        f"AI answer engines currently route to '{leader}' as the default "
        f"({leader_share:.0%} of the time). Our product '{target}' gets "
        f"{target_share:.0%}. In 2-3 sentences, write a concrete, non-fluffy "
        f"recommendation for how '{target}' could win more of this feature's AI "
        f"recommendations — focus on positioning/messaging and the kind of "
        f"content/sources that would shift the answer. No preamble."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def main() -> None:
    conn = db.connect()
    db.init_db(conn)
    data, category_of = _blended_by_feature(conn)
    dates = db.distinct_run_dates(conn)
    latest = dates[-1] if dates else None
    prev = dates[-2] if len(dates) > 1 else None
    if not latest:
        raise SystemExit("No data yet. Run run.py first.")

    recommendations, alerts = [], []

    for feature, by_date in data.items():
        category = category_of[feature]
        shares = by_date.get(latest, {})
        if not shares:
            continue
        leader = max(shares, key=shares.get)
        leader_share = shares[leader]

        for target, target_cat in TARGETS.items():
            if target_cat != category:
                continue  # only recommend where the target actually competes
            target_share = shares.get(target, 0.0)
            if target == leader:
                continue  # already winning this feature

            brief = _brief(feature, target, target_share, leader, leader_share)
            recommendations.append({
                "feature": feature, "category": category, "target": target,
                "target_share": target_share, "leader": leader,
                "leader_share": leader_share, "brief": brief,
            })
            print(f"\n[{feature}] {target} {target_share:.0%} vs leader {leader} {leader_share:.0%}")
            print(f"  → {brief}")

            # alert: routing-share drop vs previous run
            if prev:
                prev_share = by_date.get(prev, {}).get(target, 0.0)
                if prev_share - target_share >= DROP_ALERT_THRESHOLD:
                    msg = (f"{target} dropped {prev_share:.0%} → {target_share:.0%} "
                           f"on '{feature}' since {prev}")
                    alerts.append({"feature": feature, "target": target, "message": msg})
                    print(f"  ⚠ ALERT: {msg}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_date": latest,
        "recommendations": recommendations,
        "alerts": alerts,
    }, indent=2))
    print(f"\nWrote {len(recommendations)} recommendations, {len(alerts)} alerts -> {OUT}")


if __name__ == "__main__":
    main()
