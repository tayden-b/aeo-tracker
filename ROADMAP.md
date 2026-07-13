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

- [x] Scheduled collection: `.github/workflows/collect.yml` runs `run.py --n 3`
      (and `recommend.py`) on a daily 09:00 UTC cron plus manual dispatch, then
      commits the refreshed `web/public/data.json` and `recommendations.json`.
      The DB is gitignored, so history is carried between runs via the actions
      cache (restore → run → save); a >7-day gap can evict it and reset the
      trend window, which the Postgres item in "Later" makes durable.
      Needs `OPENAI_API_KEY` (and optionally `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`)
      as repo secrets. (2026-07-12)
- [x] Unit tests for the aggregation logic in `metrics.py` and `rollup.py`.
      `tests/test_rollup.py` drives `build_rollups` against an in-memory SQLite
      DB (per-provider vs blended grouping, idempotent rebuild, sentiment
      tally); `tests/test_metrics.py` pins the primary-tag-beats-position and
      empty-sample edge cases. No provider is called. (2026-07-09)
- [x] CI: GitHub Actions workflow that lints (ruff) and runs a smoke test on
      push, proving the pipeline imports and the metrics math runs on fixture
      data without hitting any provider. (2026-07-06)
