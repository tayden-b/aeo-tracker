"""
The seed feature landscape.

A *feature* is a capability (a job-to-be-done). Each has a buyer-intent prompt
that describes the NEED without naming a product — so we can measure which
product the AI routes to. The category is swappable; this seed covers
secrets-management + Infrastructure-as-Code, where the author has domain depth.
"""

from __future__ import annotations

FEATURES: list[dict[str, str]] = [
    # --- Secrets management ---
    {
        "category": "secrets-management",
        "feature": "automated secret rotation",
        "prompt": (
            "I need to automatically rotate my database credentials on a schedule "
            "without downtime. What's the best tool for this and how does it work?"
        ),
    },
    {
        "category": "secrets-management",
        "feature": "dynamic secrets",
        "prompt": (
            "What's the best way to issue short-lived, on-demand database "
            "credentials to my applications instead of long-lived static passwords?"
        ),
    },
    {
        "category": "secrets-management",
        "feature": "secret scanning",
        "prompt": (
            "What's the best tool to scan my codebase and git history for leaked "
            "secrets, passwords, and API keys?"
        ),
    },
    # --- Infrastructure as Code ---
    {
        "category": "iac",
        "feature": "remote state management",
        "prompt": (
            "What's the best way to manage infrastructure-as-code state remotely "
            "for a team, with state locking to prevent conflicts?"
        ),
    },
    {
        "category": "iac",
        "feature": "drift detection",
        "prompt": (
            "What's the best tool to detect configuration drift between my "
            "infrastructure-as-code and what's actually deployed in the cloud?"
        ),
    },
    {
        "category": "iac",
        "feature": "policy as code",
        "prompt": (
            "What's the best tool to enforce policy-as-code guardrails on my "
            "infrastructure before it gets provisioned?"
        ),
    },
]
