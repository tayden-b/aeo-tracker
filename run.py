"""
M2 — the collection runner (the daily heartbeat).

One run = sample every feature across every available provider N times, extract
each answer, and persist runs + routings + citations to SQLite, then build that
day's rollups. Cron this once a day and trends accumulate on their own:

    0 9 * * *  cd /path/to/aeo-tracker && ./.venv/bin/python run.py

Usage:
    python run.py                  # full run, N=5
    python run.py --n 4 --limit 2  # cheap: first 2 features, 4 samples each
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import db
from export import export
from extract import extract
from features import FEATURES
from providers import PROVIDERS, available_providers, get_answer
from rollup import build_rollups


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--date", type=str, default=None,
                        help="stamp this run_date (YYYY-MM-DD); default = today. "
                             "Used to backfill real data across dates for trends.")
    parser.add_argument("--providers", type=str, default=None,
                        help="comma-separated subset of engines, e.g. 'openai' or "
                             "'openai,gemini'. Default = all engines with keys.")
    args = parser.parse_args()

    providers = available_providers()
    if args.providers:
        wanted = {p.strip() for p in args.providers.split(",")}
        providers = [p for p in providers if p in wanted]
    if not providers:
        raise SystemExit("No provider API keys found. Set OPENAI_API_KEY in .env")

    conn = db.connect()
    db.init_db(conn)

    now = datetime.now(timezone.utc)
    ts = now.isoformat()
    run_date = args.date or now.date().isoformat()
    features = FEATURES[: args.limit] if args.limit else FEATURES

    print(f"Collection run {run_date} | providers: {', '.join(providers)} | N={args.n}")
    total = 0
    for feat in features:
        print(f"  [{feat['category']}] {feat['feature']}")
        for provider in providers:
            model = PROVIDERS[provider]["model"]
            stored = 0
            for i in range(args.n):
                # resilient: a failed sample (rate limit / 503) is skipped, not fatal,
                # so one flaky engine never kills the whole run.
                try:
                    answer = get_answer(provider, feat["prompt"])
                    ex = extract(answer)
                    run_id = db.insert_run(
                        conn, ts=ts, run_date=run_date, provider=provider, model=model,
                        category=feat["category"], feature=feat["feature"],
                        prompt=feat["prompt"], raw_answer=answer,
                    )
                    for p in ex.products:
                        db.insert_routing(
                            conn, run_id, p.name, p.role, p.position, p.sentiment,
                            json.dumps(p.attributes),
                        )
                    for url in ex.citations:
                        db.insert_citation(conn, run_id, url)
                    stored += 1
                    total += 1
                except Exception as e:  # noqa: BLE001
                    print(f"      ! {provider} sample {i + 1} skipped: {str(e)[:90]}")
            conn.commit()
            print(f"    · {provider}: {stored}/{args.n} samples stored")

    print(f"\nStored {total} runs for {run_date}. Building rollups...")
    n_roll = build_rollups(conn, run_date)
    print(f"Wrote {n_roll} rollup rows.")
    conn.close()

    out = export()
    print(f"Exported dashboard data -> {out}")
    print("(Run `python recommend.py` to refresh recommendations + alerts.)")


if __name__ == "__main__":
    main()
