"""Cost math and per-run tally accounting. No provider is called."""

import usage


def setup_function():
    usage.reset()


def test_cost_for_known_model():
    # gpt-4o-mini: $0.15 in / $0.60 out per 1M tokens.
    # 1000 in -> 0.00015, 500 out -> 0.0003, total 0.00045.
    assert usage.cost_for("gpt-4o-mini", 1000, 500) == 0.00045


def test_cost_for_unknown_model_is_none():
    assert usage.cost_for("some-future-model", 1000, 500) is None


def test_record_accumulates_across_calls():
    # Whole-million token counts keep the dollar figure exact at 4dp.
    usage.record("openai", "gpt-4o-mini", 1_000_000, 1_000_000)  # 0.15 + 0.60
    usage.record("openai", "gpt-4o-mini", 1_000_000, 0)          # + 0.15
    out = usage.summary()
    assert "openai: 2 calls, 2000000 in + 1000000 out tokens" in out
    assert "$0.9000" in out
    assert "total: $0.9000" in out


def test_unpriced_model_flags_estimate_but_still_counts_tokens():
    usage.record("mystery", "unlisted-model", 100, 100)
    out = usage.summary()
    assert "mystery: 1 calls, 100 in + 100 out tokens" in out
    assert "unpriced" in out
    assert "+" in out  # total marked as a lower bound


def test_summary_empty_when_nothing_recorded():
    assert usage.summary() == "Token usage: none recorded."
