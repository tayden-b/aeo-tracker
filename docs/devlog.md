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
