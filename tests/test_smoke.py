"""Smoke test: the pipeline imports and the metrics math runs on fixtures.

No provider is ever called here. Dummy API keys are set before any import so
modules that construct an SDK client at import time (recommend.py, m0_raw.py)
load without a real key — the client is never used.
"""

import os
from types import SimpleNamespace

# Must be set before importing modules that build a client at import time.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")
os.environ.setdefault("GEMINI_API_KEY", "test-placeholder")
os.environ.setdefault("GOOGLE_API_KEY", "test-placeholder")


def test_pipeline_modules_import():
    """Every module in the daily pipeline imports cleanly."""
    import collect  # noqa: F401
    import db  # noqa: F401
    import export  # noqa: F401
    import extract  # noqa: F401
    import features  # noqa: F401
    import metrics  # noqa: F401
    import providers  # noqa: F401
    import rollup  # noqa: F401
    import run  # noqa: F401


def _product(name, role, position, sentiment):
    return SimpleNamespace(name=name, role=role, position=position, sentiment=sentiment)


def _fixture_extractions():
    """Four canned samples about secrets management, mixed phrasings/aliases."""
    return [
        SimpleNamespace(products=[
            _product("Vault", "primary", 1, "positive"),
            _product("AWS Secrets Manager", "alternative", 2, "neutral"),
        ]),
        SimpleNamespace(products=[
            _product("hashicorp vault", "primary", 1, "positive"),
            _product("CyberArk", "alternative", 2, "neutral"),
        ]),
        SimpleNamespace(products=[
            _product("CyberArk", "primary", 1, "neutral"),
            _product("Vault", "alternative", 2, "positive"),
        ]),
        SimpleNamespace(products=[
            _product("aws secrets manager", "primary", 1, "positive"),
        ]),
    ]


def test_normalize_collapses_aliases():
    from metrics import normalize

    assert normalize("vault") == "HashiCorp Vault"
    assert normalize("hashicorp vault") == "HashiCorp Vault"
    assert normalize("aws secrets manager") == "AWS Secrets Manager"


def test_routing_share_math():
    from metrics import routing_share

    result = routing_share(_fixture_extractions())

    # Aliases collapsed to canonical names.
    assert "HashiCorp Vault" in result
    assert "AWS Secrets Manager" in result

    # Vault was primary in 2 of 4 samples.
    assert result["HashiCorp Vault"]["routing_share"] == 0.5
    # Mentioned in 3 of 4 (twice as Vault, once as an alias).
    assert result["HashiCorp Vault"]["mention_rate"] == 0.75
    # Positions [1, 1, 2] -> 1.33.
    assert result["HashiCorp Vault"]["avg_position"] == 1.33

    # One primary is credited per sample, so shares sum to ~1.
    total = sum(m["routing_share"] for m in result.values())
    assert abs(total - 1.0) < 1e-6

    # Sorted by routing share descending -> Vault leads.
    assert next(iter(result)) == "HashiCorp Vault"


def test_routing_share_falls_back_to_first_position():
    """With no product tagged primary, the lowest position gets the credit."""
    from metrics import routing_share

    exts = [SimpleNamespace(products=[
        _product("Pulumi", "alternative", 2, "neutral"),
        _product("Terraform", "alternative", 1, "positive"),
    ])]
    result = routing_share(exts)
    assert result["Terraform"]["routing_share"] == 1.0
    assert result["Pulumi"]["routing_share"] == 0.0


def test_routing_share_handles_empty_input():
    from metrics import routing_share

    assert routing_share([]) == {}
