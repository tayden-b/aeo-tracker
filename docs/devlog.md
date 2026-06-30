# Dev log

Running log of decisions and traps — what I chose, what broke, what I'd still fix.

## M0 — the feature-routing primitive

### Step 1 — scaffold + raw answer
- **Decision:** start with the *raw* answer before any structured extraction, so the
  extraction schema is designed from real observed output, not guesses.
- **Decision:** unit of analysis is a **feature-intent prompt** (describe a capability,
  don't name a product) — the whole tool is "which product does the AI route this to?"
- **Decision:** SDK-first (official `openai` SDK + later Pydantic), no heavy framework —
  more transparent, more to learn, better to explain.
- **Stack:** Python venv, `openai` 2.44, `python-dotenv`. Model `gpt-4o-mini` (cheap/fast).
- **Trap to watch:** answers vary run-to-run (non-determinism) → this is why M1 adds sampling.
- **First result (3 runs, same prompt/model):** primary recommendation flipped — Vault was #1 in run 1, but AWS Secrets Manager was #1 in runs 2 & 3. A single run would have given a wrong "Vault owns this" conclusion. Confirms sampling is non-negotiable.
- **Observed:** answers list multiple products with an implicit ranking (primary vs. alternative) → extraction must capture position. No citations (gpt-4o-mini isn't browsing — training-recall pathway); real citations come with Perplexity in M1.

### Step 2 — structured extraction (LLM-as-judge)
- **Decision:** Pydantic + `client.chat.completions.parse(response_format=...)` for forced structured output — always-parseable, validated, self-documenting via field descriptions. No manual JSON/regex.
- **Schema:** `Extraction` = `list[ProductRouting]` + `citations[]`; `ProductRouting` = name, role (primary|alternative), position, sentiment, attributes[].
- **Decision:** a *separate* extractor call (system prompt = "extract, don't invent") rather than asking the answering model to self-structure — keeps the two jobs clean (the LLM-as-judge pattern).
- **Result:** clean prose→JSON on the credential-rotation prompt; correctly captured role/position/sentiment/attributes; citations empty (no browsing), as expected.
- **Trap noted:** attributes come out verbose/sentence-like ("securely stores database credentials") — want tighter, normalized phrasing later for the positioning map. Product-name normalization (Vault vs HashiCorp Vault) handled by the prompt for now; may need an alias map at scale.

## M1 — sampling + multi-provider → routing share
- **Decision:** providers are key-gated (`providers.py`): OpenAI / Anthropic / Perplexity / Gemini, but only those with a key run. OpenAI + Perplexity share the OpenAI-compatible API (different base_url). SDKs lazy-imported so missing ones never crash.
- **Decision:** `routing_share` = exactly ONE primary per sample (top-ranked recommendation) → sums to ~100% = clean "feature ownership." Kept mention_rate / avg_position / sentiment for context. Added an alias map (`metrics.py`) to normalize product names.
- **Trap fixed:** extractor over-captured generic infra (PostgreSQL, RDS, Ansible) as products → tightened the extraction system prompt to only count tools offered as the *solution*.
- **Result (OpenAI, N=5):** "automated secret rotation" → AWS Secrets Manager 60% / Vault 40%; "dynamic secrets" → Vault 100%. Ownership genuinely varies by feature.

## M2 — persistence + rollups + runner
- **Decision:** SQLite (`db.py`), zero-setup local DB; schema is plain SQL so it ports to Postgres/Supabase later. Tables: runs, routings, citations, rollups.
- **Decision:** `run.py` = the daily heartbeat (cron-able): sample → extract → persist → build rollups. `rollup.py` aggregates per (provider, feature) plus a 'blended' all-providers view, reusing `metrics.routing_share`.
- **Decision:** `*.db` gitignored (binary churn); the dashboard reads a JSON export instead.
- **Result:** 12 runs → 86 rollup rows; blended leaderboards correct (rotation AWS/Vault 50/50; dynamic secrets AWS 75/Vault 25; scanning GitGuardian/GitLeaks lead).
- **Trap noted:** extractor still leaks some non-tools (pgbouncer, IAM roles) and casing dupes (GitLeaks/Gitleaks) at low mention rates → added more aliases; dashboard will filter to meaningful products (mention_rate ≥ 0.5 or routing > 0, top N).

## M3 — dashboard
- **Decision:** clean seam — Python `export.py` writes `web/public/data.json`; the dashboard just renders it. Static-friendly (no live DB), deploys to Vercel.
- **Decision:** Next.js 16 + Tailwind v4 (`web/`). Dashboard is a Server Component that reads the JSON at build time with `fs` (no client fetch, prerenders static).
- **Decision:** filter one-off extraction noise in the export (keep products with routing > 0 or mention ≥ 0.5, top 8); highlight tracked products (Vault/Terraform) in violet.
- **Wiring:** `run.py` now exports `data.json` at the end of each run, so the dashboard stays fresh.
- **Result:** `next build` passes; `/` prerenders as static. Feature-ownership bars + recommendations render from real data.

## M4 — recommendation + alert layer
- **Decision:** `recommend.py` reads rollups, finds features where a TARGET product (Vault→secrets, Terraform→IaC) isn't the AI's default, and an LLM drafts a 2–3 sentence PMM brief per gap (the "recommendation agent"). Writes `web/public/recommendations.json`.
- **Alerts:** flags a ≥20pt routing-share drop for a target between runs (needs ≥2 run dates to fire).
- **Result:** generated real briefs for Vault on rotation/dynamic-secrets/scanning; 0 alerts (single run date so far).
- **Trap noted:** target↔category relevance is coarse (Vault gets recommended for "secret scanning," which isn't really its job). Fine as an "absent from this feature" signal; would refine with a per-target feature allowlist.

## Dashboard v2 — detailed + modern (multi-engine, trends, attributes)
- **Added Gemini** as a second answer engine (`providers.py`, key-gated). Models: `gemini-2.5-flash-lite` (2.0-flash retired).
- **Extraction backend:** tried Gemini free tier for extraction to save OpenAI $ — but its free tier rate-limits/503s too hard for bulk volume (a 4-call test took 64s). Reverted extraction to OpenAI `gpt-4o-mini` (fast, reliable, ~$0.05 for a full backfill). Gemini kept as an answer engine only.
- **Persisted attributes** (`routings.attributes` JSON) so the dashboard can show positioning words.
- **Backfilled 6 dates** (Jun 24–29) of real data for trend lines — historical dates on OpenAI (fast), latest date attempted with both engines. `run.py --date` + `--providers` flags added.
- **Resilience:** `run.py` now skips a failed sample (rate limit / 503) instead of crashing the whole run; `llm_util` backs off on 429/503/overload.
- **Gemini cross-engine: still pending** — Gemini hit repeated 503 "high demand" during the backfill, so the current dataset is OpenAI-only (engines=1, so the cross-engine matrix hides). Re-attempt when Gemini is less loaded; the dashboard lights up the matrix automatically when a 2nd engine appears.
- **Export v2** (`export.py`): overview KPIs (features/engines/samples/dates, tracked leads), per-feature leaderboard + sentiment + avg position + top attributes + per-engine breakdown + routing-share trend across dates.
- **Dashboard v2** (`web/`, Recharts): KPI header, rich per-feature cards (routing bar chart, per-engine chips, sentiment bar, attribute chips, trend line), cross-engine matrix (when >1 engine), recommendations. `next build` passes static.

## Status
M0–M4 complete + dashboard v2 (detailed, 6 dates of trend data). Public repo live, deploys to Vercel. Remaining: land Gemini (cross-engine) when its API is less loaded; Perplexity for citations; a POV writeup.
