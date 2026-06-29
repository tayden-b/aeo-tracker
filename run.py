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
from datetime import datetime, timezone

import db
from extract import extract
from features import FEATURES
from providers import PROVIDERS, available_providers, get_answer
from rollup import build_rollups


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    providers = available_providers()
    if not providers:
        raise SystemExit("No provider API keys found. Set OPENAI_API_KEY in .env")

    conn = db.connect()
    db.init_db(conn)

    now = datetime.now(timezone.utc)
    ts, run_date = now.isoformat(), now.date().isoformat()
    features = FEATURES[: args.limit] if args.limit else FEATURES

    print(f"Collection run {run_date} | providers: {', '.join(providers)} | N={args.n}")
    total = 0
    for feat in features:
        print(f"  [{feat['category']}] {feat['feature']}")
        for provider in providers:
            model = PROVIDERS[provider]["model"]
            for i in range(args.n):
                answer = get_answer(provider, feat["prompt"])
                ex = extract(answer)
                run_id = db.insert_run(
                    conn, ts=ts, run_date=run_date, provider=provider, model=model,
                    category=feat["category"], feature=feat["feature"],
                    prompt=feat["prompt"], raw_answer=answer,
                )
                for p in ex.products:
                    db.insert_routing(conn, run_id, p.name, p.role, p.position, p.sentiment)
                for url in ex.citations:
                    db.insert_citation(conn, run_id, url)
                total += 1
            conn.commit()
            print(f"    · {provider}: {args.n} samples stored")

    print(f"\nStored {total} runs for {run_date}. Building rollups...")
    n_roll = build_rollups(conn, run_date)
    print(f"Wrote {n_roll} rollup rows.")
    conn.close()


if __name__ == "__main__":
    main()
