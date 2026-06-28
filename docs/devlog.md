# Dev log

Running log of decisions and traps — what I chose, what broke, what I'd still fix.
(Doubles as raw material for the Marketing Engineering cert "build" depth-path.)

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
