"""Rollup aggregation tests against an in-memory SQLite DB.

No provider is called. We seed runs + routings by hand, run build_rollups, and
assert on the rollup rows: per-provider groups, the pooled 'blended' group, and
that a rebuild is idempotent (no duplicated or stale rows).
"""

import sqlite3

import db
import rollup

DATE = "2026-07-09"
CATEGORY = "secrets-management"
FEATURE = "secret storage"


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    db.init_db(conn)
    return conn


def _add_sample(conn, provider, products):
    """Insert one run and its routings. products: (name, role, position, sentiment)."""
    run_id = db.insert_run(
        conn, ts=f"{DATE}T00:00:00", run_date=DATE, provider=provider,
        model="test", category=CATEGORY, feature=FEATURE, prompt="q", raw_answer="a",
    )
    for name, role, position, sentiment in products:
        db.insert_routing(conn, run_id, name, role, position, sentiment)


def _seed(conn):
    """Two providers, four samples total — mirrors the metrics fixture."""
    _add_sample(conn, "openai", [
        ("Vault", "primary", 1, "positive"),
        ("AWS Secrets Manager", "alternative", 2, "neutral"),
    ])
    _add_sample(conn, "openai", [("hashicorp vault", "primary", 1, "positive")])
    _add_sample(conn, "anthropic", [
        ("CyberArk", "primary", 1, "neutral"),
        ("Vault", "alternative", 2, "positive"),
    ])
    _add_sample(conn, "anthropic", [("aws secrets manager", "primary", 1, "positive")])


def _index(conn):
    """Map (provider, product) -> rollup row for easy assertions."""
    return {(r["provider"], r["product"]): r for r in db.fetch_rollups(conn, DATE)}


def test_build_rollups_writes_per_provider_and_blended():
    conn = _conn()
    _seed(conn)
    rollup.build_rollups(conn, DATE)
    providers = {r["provider"] for r in db.fetch_rollups(conn, DATE)}
    assert providers == {"openai", "anthropic", "blended"}


def test_blended_pools_all_providers():
    conn = _conn()
    _seed(conn)
    rollup.build_rollups(conn, DATE)
    rows = _index(conn)

    # Blended sees all four samples; Vault (incl. its alias) is primary in 2.
    assert rows[("blended", "HashiCorp Vault")]["n_samples"] == 4
    assert rows[("blended", "HashiCorp Vault")]["routing_share"] == 0.5
    assert rows[("blended", "CyberArk")]["routing_share"] == 0.25
    assert rows[("blended", "AWS Secrets Manager")]["routing_share"] == 0.25

    # One primary credited per sample, so blended shares sum to ~1.
    blended = [v for k, v in rows.items() if k[0] == "blended"]
    assert abs(sum(r["routing_share"] for r in blended) - 1.0) < 1e-6


def test_per_provider_groups_are_scoped():
    conn = _conn()
    _seed(conn)
    rollup.build_rollups(conn, DATE)
    rows = _index(conn)

    # openai's two samples both name Vault primary -> full share, two samples.
    assert rows[("openai", "HashiCorp Vault")]["n_samples"] == 2
    assert rows[("openai", "HashiCorp Vault")]["routing_share"] == 1.0
    # CyberArk never appears in an openai sample.
    assert ("openai", "CyberArk") not in rows


def test_rebuild_is_idempotent():
    conn = _conn()
    _seed(conn)
    rollup.build_rollups(conn, DATE)
    first = db.fetch_rollups(conn, DATE)
    # A second pass over the same date must replace, not accumulate.
    rollup.build_rollups(conn, DATE)
    second = db.fetch_rollups(conn, DATE)
    assert len(first) == len(second)


def test_sentiment_tally_carried_through():
    conn = _conn()
    _seed(conn)
    rollup.build_rollups(conn, DATE)
    vault = _index(conn)[("blended", "HashiCorp Vault")]
    # Vault mentioned three times: two positive (primary), one positive (alt).
    assert vault["sentiment_positive"] == 3
    assert vault["sentiment_neutral"] == 0
    assert vault["sentiment_negative"] == 0
