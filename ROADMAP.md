# Roadmap

Where this project is headed and what to pick up next. Work the top unchecked
item first. When something ships, check it off and move it to Done with the date.
Keep items small enough to land as one focused PR.

## Goal

Turn this from a run-it-yourself pipeline into a continuously running,
publicly viewable tracker. The end state: a hosted dashboard with weeks of
trend data showing feature-ownership shifts across answer engines, updating
itself daily without me touching it. Trend lines over time are the whole
value — a single snapshot is a demo, a time series is a product.

## Next up

- [ ] Unit tests for the aggregation logic in `metrics.py` and `rollup.py`
      (routing share math, high-water counting) using canned extraction JSON.
      This is the code that must be right for the numbers to mean anything.
- [ ] Scheduled collection: a GitHub Actions cron job that runs `run.py`
      daily with a small `--n`, commits the updated `web/public/data.json`
      snapshot back to the repo. This is what makes trends accumulate.
- [ ] Trend view in the dashboard: routing share per feature over time
      (line chart), not just the latest snapshot.
- [ ] Deploy the dashboard to Vercel reading the committed snapshot; put the
      live link at the top of the README.
- [ ] Provider hardening in `providers.py`: retries with backoff, timeout
      handling, and per-run cost/token logging so a scheduled run can't
      silently burn money.

## Later

- [ ] Prove the "category is swappable" claim: move the tracked
      features/products into a config file and document adding a second
      category (e.g. CI/CD tools or observability).
- [ ] Alerts when a feature's ownership flips (product A overtakes product B).
- [ ] Citation analysis for providers that return sources (Perplexity):
      which domains actually drive the answers.
- [ ] SQLite → Postgres/Supabase when the snapshot-in-repo approach gets
      too heavy.
- [ ] Short demo GIF in the README once the trend view exists.

## Done

- [x] CI: GitHub Actions workflow that lints (ruff) and runs a smoke test on
      push, proving the pipeline imports and the metrics math runs on fixture
      data without hitting any provider. (2026-07-06)
