"""
Multi-provider answer generation.

Each answer engine is used ONLY if its API key is present in the environment, so
the tool runs with whatever keys you have. Today that's OpenAI; add a key for any
other provider and it joins automatically — no code change.

Provider SDKs are imported lazily (inside each branch) so a missing/uninstalled
SDK for a provider you're not using never crashes the run.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from llm_util import call_with_retries

load_dotenv()

# name -> which env var holds its key, and the default model to use
PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {"env": "OPENAI_API_KEY", "model": "gpt-4o-mini"},
    "anthropic": {"env": "ANTHROPIC_API_KEY", "model": "claude-haiku-4-5-20251001"},
    "perplexity": {"env": "PERPLEXITY_API_KEY", "model": "sonar"},
    "gemini": {"env": "GEMINI_API_KEY", "model": "gemini-2.5-flash-lite"},
}


def available_providers() -> list[str]:
    """Return the providers we actually have keys for (in PROVIDERS order)."""
    return [name for name, cfg in PROVIDERS.items() if os.getenv(cfg["env"])]


def get_answer(provider: str, prompt: str) -> str:
    """Send `prompt` to one provider and return its text answer."""
    cfg = PROVIDERS[provider]
    model = cfg["model"]
    key = os.getenv(cfg["env"])
    if not key:
        raise RuntimeError(f"No API key for provider '{provider}' ({cfg['env']}).")

    # OpenAI and Perplexity share the OpenAI-compatible chat API (Perplexity just
    # uses a different base_url) — so one branch handles both.
    if provider in ("openai", "perplexity"):
        from openai import OpenAI

        base_url = "https://api.perplexity.ai" if provider == "perplexity" else None
        client = OpenAI(api_key=key, base_url=base_url)
        resp = call_with_retries(lambda: client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        ))
        return resp.choices[0].message.content

    if provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=key)
        resp = call_with_retries(lambda: client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ))
        return resp.content[0].text

    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=key)
        resp = call_with_retries(
            lambda: client.models.generate_content(model=model, contents=prompt)
        )
        return resp.text

    raise ValueError(f"Unknown provider: {provider}")
