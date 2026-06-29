# AEO Tracker

**AEO for *features* instead of brands.** It measures which product an AI answer
engine routes a developer to for each *capability* — *who "owns" a feature* in the
AI's mind — how that feature is positioned, and where to win the ones you're losing.

Seeded on the **secrets-management + Infrastructure-as-Code** landscape; the tracked
category is swappable.

## Why
A growing share of how developers pick tools now happens inside AI answers: ask
ChatGPT *"how do I rotate database credentials,"* and whatever it recommends shapes
the decision before any human is involved. SEO had a whole analytics layer; this new
channel barely has any. AEO Tracker is a measurement layer for it — at the level
buyers actually think (capabilities), not just brand mentions.

## How it works (the pipeline)
```
feature-intent prompt  ->  multi-provider answer  ->  structured extraction
   ("rotate DB creds")      (OpenAI/Anthropic/…)       (LLM-as-judge -> JSON)
        ->  sample N times  ->  aggregate to routing share  ->  store (SQLite)
        ->  daily rollups   ->  export JSON  ->  dashboard + recommendation agent
```
- **Sampling** — LLM answers are non-deterministic, so each prompt is asked N times and averaged. *Routing share* = the % of answers that name a product as the primary recommendation = "feature ownership."
- **Structured extraction** — a second LLM call with a forced schema (Pydantic) turns prose into `{products, role, position, sentiment, attributes, citations}`.
- **Multi-provider** — OpenAI, Anthropic, Perplexity, Gemini; each runs only if its API key is set.
- **Recommendation agent** — finds features where a tracked product isn't the default and drafts a product-marketing brief from the data.

## Stack
- **Backend:** Python — official provider SDKs + Pydantic (SDK-first, no heavy framework)
- **Storage:** SQLite locally (schema ports to Postgres/Supabase)
- **Frontend:** Next.js + Tailwind dashboard (`web/`), reads an exported JSON snapshot

## Quickstart
```bash
# backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # paste your OpenAI API key

python collect.py --n 5         # quick look: routing share, printed
python run.py --n 5             # full run -> SQLite -> rollups -> web/public/data.json
python recommend.py             # recommendation briefs + alerts -> recommendations.json

# dashboard
cd web && npm install && npm run dev   # http://localhost:3000
```
Add `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, or `GEMINI_API_KEY` to `.env` and those
engines join automatically (Perplexity also yields real source citations).

## Schedule it
Cron the runner so trends accumulate:
```
0 9 * * *  cd /path/to/aeo-tracker && ./.venv/bin/python run.py
```

## Layout
| Path | What |
|---|---|
| `providers.py` | multi-provider answer generation (key-gated) |
| `features.py` | the seed feature → prompt list |
| `extract.py` | structured extraction (LLM-as-judge) |
| `metrics.py` | routing-share aggregation + name normalization |
| `collect.py` | sampling collector (prints) |
| `run.py` | the daily heartbeat: collect → persist → rollup → export |
| `db.py` / `rollup.py` | SQLite + daily aggregates |
| `recommend.py` | recommendation + alert agent |
| `export.py` | rollups → `web/public/data.json` |
| `web/` | Next.js dashboard |
