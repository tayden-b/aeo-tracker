"""
M1 — sampling + multi-provider collection → feature routing share.

For each feature, ask every available provider the prompt N times, extract each
answer into structured data, then aggregate into routing share. Sampling is the
whole point: a single answer is noise (we saw Vault vs AWS flip run-to-run), so
we repeat and average.

Usage:
    python collect.py                 # all features, N=5, all available providers
    python collect.py --n 4 --limit 2 # first 2 features, 4 samples each (cheap)
"""

from __future__ import annotations

import argparse

from extract import extract
from features import FEATURES
from metrics import routing_share
from providers import available_providers, get_answer


def collect_feature(feat: dict, providers: list[str], n: int) -> list:
    """Sample one feature across providers; return a list of Extraction objects."""
    extractions = []
    for provider in providers:
        for i in range(n):
            answer = get_answer(provider, feat["prompt"])
            extractions.append(extract(answer))
            print(f"    · {provider} sample {i + 1}/{n} done")
    return extractions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5, help="samples per provider")
    parser.add_argument("--limit", type=int, default=None, help="only first N features")
    args = parser.parse_args()

    providers = available_providers()
    if not providers:
        raise SystemExit("No provider API keys found. Set OPENAI_API_KEY in .env")
    print(f"Providers: {', '.join(providers)}  |  samples each: {args.n}\n")

    features = FEATURES[: args.limit] if args.limit else FEATURES
    for feat in features:
        print(f"[{feat['category']}] {feat['feature']}")
        extractions = collect_feature(feat, providers, args.n)
        shares = routing_share(extractions)
        print(f"  → feature ownership (n={len(extractions)}):")
        for product, m in shares.items():
            print(
                f"     {product:<22} routing {m['routing_share']:>5.0%}"
                f"  | mentions {m['mention_rate']:>5.0%}"
                f"  | avg pos {m['avg_position']}"
            )
        print()


if __name__ == "__main__":
    main()
