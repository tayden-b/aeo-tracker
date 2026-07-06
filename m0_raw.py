"""
M0 · Step 1 — the raw answer.

Goal of this script: make ONE call to ONE answer engine with a feature-intent
prompt (a developer describing a capability they need, without naming a product)
and print the raw text answer.

Why we start here: before we can turn answers into structured data, we need to
SEE what a raw answer looks like — which product(s) it routes to, how it frames
the feature, and how much it varies run-to-run. That observation becomes the
spec for the extraction step next.
"""

from dotenv import load_dotenv
from openai import OpenAI

# Load OPENAI_API_KEY from the .env file into the environment.
load_dotenv()

# The SDK automatically reads OPENAI_API_KEY from the environment.
client = OpenAI()

# A FEATURE-INTENT prompt: the user describes a CAPABILITY, not a product.
# This is the atomic unit of the whole tool — "which product does the AI route
# this capability to?"
PROMPT = (
    "I need to automatically rotate my database credentials on a schedule "
    "without downtime. What's the best tool for this and how does it work?"
)

MODEL = "gpt-4o-mini"  # cheap + fast; fine for learning the mechanics


def get_raw_answer(prompt: str, model: str = MODEL) -> str:
    """Send one prompt to one model and return the model's text answer."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    # The answer text is nested inside the response object:
    return response.choices[0].message.content


if __name__ == "__main__":
    print(f"PROMPT:\n{PROMPT}\n")
    print("=" * 70)
    answer = get_raw_answer(PROMPT)
    print(answer)
    print("=" * 70)
