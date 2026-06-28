"""
M0 · Step 2 — structured extraction (LLM-as-judge).

Takes a raw answer (free prose) and turns it into structured, countable data:
which products the answer routed to, their ranking, sentiment, and the
attributes used to describe each. This is the core applied-AI technique behind
the whole tool — using an LLM with a *forced schema* to extract reliable signal
from unstructured text. Aggregate this over many samples and you get "feature
ownership."
"""

from __future__ import annotations

from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from m0_raw import PROMPT, get_raw_answer  # reuse the raw-answer call

load_dotenv()
client = OpenAI()

EXTRACT_MODEL = "gpt-4o-mini"


# --- The schema: this is what "structured output" means. The model is FORCED to
# --- return JSON matching these classes, so the result is always parseable. ---

class ProductRouting(BaseModel):
    """One product the answer routed the user to, for this feature."""

    name: str = Field(description="Canonical product/tool name, e.g. 'HashiCorp Vault'.")
    role: Literal["primary", "alternative"] = Field(
        description="'primary' if recommended as the main/best answer; "
        "'alternative' if mentioned as a secondary option."
    )
    position: int = Field(description="1-based order the product appears in the answer.")
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall tone toward this product in the answer."
    )
    attributes: list[str] = Field(
        description="Short descriptive words/phrases the answer uses for this product "
        "(e.g. 'dynamic secrets', 'complex', 'AWS-native')."
    )


class Extraction(BaseModel):
    """Structured view of one raw answer to one feature-intent prompt."""

    products: list[ProductRouting]
    citations: list[str] = Field(
        description="Any source URLs cited in the answer. Empty list if none."
    )


EXTRACTION_SYSTEM = (
    "You are a precise information extractor for an AEO (Answer Engine Optimization) "
    "tool. You are given the raw text of an AI assistant's answer to a developer's "
    "feature-intent question (the user described a capability they need, without naming "
    "a product). Extract EVERY product/tool the answer presents as a way to solve the "
    "need. For each: whether it's the primary recommendation or an alternative, its "
    "1-based position in the answer, the sentiment toward it, and the descriptive "
    "attributes used about it. Capture any cited source URLs. Do NOT invent products or "
    "attributes not present in the text. Use each product's canonical name "
    "(e.g. 'Vault' -> 'HashiCorp Vault')."
)


def extract(answer_text: str) -> Extraction:
    """Run structured extraction on one raw answer; returns a validated Extraction."""
    completion = client.chat.completions.parse(
        model=EXTRACT_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": answer_text},
        ],
        response_format=Extraction,  # <-- forces the model to fill this schema
    )
    return completion.choices[0].message.parsed


if __name__ == "__main__":
    print(f"PROMPT:\n{PROMPT}\n" + "=" * 70)
    raw = get_raw_answer(PROMPT)
    print("RAW ANSWER (first 400 chars):\n" + raw[:400] + " ...\n" + "=" * 70)
    result = extract(raw)
    print("STRUCTURED EXTRACTION:\n")
    print(result.model_dump_json(indent=2))
