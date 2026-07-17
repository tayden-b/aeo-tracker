"""Per-run token + cost accounting.

Every provider returns token usage on each response; we tally it here so a
scheduled run reports what it spent instead of silently burning money. Prices
are approximate list prices (USD per 1M tokens) and easy to update — an unknown
model still logs its tokens, just without a dollar estimate.
"""

from __future__ import annotations

from dataclasses import dataclass

# model -> (input $/1M tokens, output $/1M tokens). Approximate public list
# prices as of mid-2025; adjust when they change.
PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "sonar": (1.00, 1.00),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}


@dataclass
class _Tally:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    priced: bool = True  # False once any call used a model with no price entry


_tallies: dict[str, _Tally] = {}


def cost_for(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Dollar cost for one call, or None if the model isn't in the price table."""
    price = PRICES.get(model)
    if price is None:
        return None
    inp, out = price
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


def record(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Add one call's usage to the running tally for its provider."""
    t = _tallies.setdefault(provider, _Tally())
    t.calls += 1
    t.prompt_tokens += prompt_tokens
    t.completion_tokens += completion_tokens
    cost = cost_for(model, prompt_tokens, completion_tokens)
    if cost is None:
        t.priced = False
    else:
        t.cost_usd += cost


def reset() -> None:
    """Clear all tallies (call at the start of a run)."""
    _tallies.clear()


def summary() -> str:
    """A human-readable per-provider usage + cost report for the run."""
    if not _tallies:
        return "Token usage: none recorded."
    lines = ["Token usage this run:"]
    total_cost = 0.0
    all_priced = True
    for provider, t in _tallies.items():
        total_cost += t.cost_usd
        all_priced = all_priced and t.priced
        cost = f"${t.cost_usd:.4f}" if t.priced else f"~${t.cost_usd:.4f}+ (some models unpriced)"
        lines.append(
            f"  {provider}: {t.calls} calls, "
            f"{t.prompt_tokens} in + {t.completion_tokens} out tokens, {cost}"
        )
    total = f"${total_cost:.4f}" if all_priced else f"~${total_cost:.4f}+"
    lines.append(f"  total: {total}")
    return "\n".join(lines)
