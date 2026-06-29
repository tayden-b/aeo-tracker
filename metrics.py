"""
Turn a batch of extractions into feature-ownership metrics.

The headline metric is **routing share**: across N samples, what fraction named
each product as the *primary* recommendation. That's "who owns this feature in
the AI's mind." We also compute mention rate, average position, and a sentiment
tally for context.
"""

from __future__ import annotations

from collections import defaultdict

# Minimal alias map so the same product counts as one thing across phrasings.
# (At scale this would be data-driven; a dict is honest and enough for the seed set.)
ALIASES: dict[str, str] = {
    "vault": "HashiCorp Vault",
    "hashicorp vault": "HashiCorp Vault",
    "cyberark": "CyberArk",
    "cyberark conjur": "CyberArk",
    "conjur": "CyberArk",
    "aws secrets manager": "AWS Secrets Manager",
    "azure key vault": "Azure Key Vault",
    "google secret manager": "Google Secret Manager",
    "gcp secret manager": "Google Secret Manager",
    "terraform": "Terraform",
    "hashicorp terraform": "Terraform",
    "opentofu": "OpenTofu",
    "pulumi": "Pulumi",
    "spacelift": "Spacelift",
    "cloudformation": "AWS CloudFormation",
    "aws cloudformation": "AWS CloudFormation",
    "gitguardian": "GitGuardian",
    "infisical": "Infisical",
    "doppler": "Doppler",
    "trufflehog": "TruffleHog",
}


def normalize(name: str) -> str:
    """Canonicalize a product name via the alias map (falls back to title-ish)."""
    return ALIASES.get(name.strip().lower(), name.strip())


def routing_share(extractions: list) -> dict:
    """
    Compute feature-ownership metrics from a list of Extraction objects.

    Returns a dict keyed by canonical product name with:
      - routing_share: fraction of samples where this product was PRIMARY
      - mention_rate:  fraction of samples that mentioned it at all
      - avg_position:  average 1-based position when mentioned (lower = better)
      - sentiment:     {positive, neutral, negative} counts
    """
    n = len(extractions)
    primary = defaultdict(int)
    mentions = defaultdict(int)
    positions = defaultdict(list)
    sentiment = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})

    for ex in extractions:
        # Count every mention (rate, position, sentiment) ...
        for p in ex.products:
            name = normalize(p.name)
            mentions[name] += 1
            positions[name].append(p.position)
            sentiment[name][p.sentiment] += 1
        # ... but credit exactly ONE primary per sample, so routing_share is a
        # clean share that sums to ~100%. Prefer a product tagged "primary"
        # (lowest position wins ties); else fall back to the first-positioned one.
        prims = [p for p in ex.products if p.role == "primary"]
        candidates = prims or ex.products
        if candidates:
            top = min(candidates, key=lambda p: p.position)
            primary[normalize(top.name)] += 1

    out = {}
    for name in mentions:
        pos = positions[name]
        out[name] = {
            "routing_share": round(primary[name] / n, 3) if n else 0.0,
            "mention_rate": round(mentions[name] / n, 3) if n else 0.0,
            "avg_position": round(sum(pos) / len(pos), 2) if pos else None,
            "sentiment": dict(sentiment[name]),
        }
    # sort by routing share desc, then mention rate
    return dict(
        sorted(
            out.items(),
            key=lambda kv: (kv[1]["routing_share"], kv[1]["mention_rate"]),
            reverse=True,
        )
    )
