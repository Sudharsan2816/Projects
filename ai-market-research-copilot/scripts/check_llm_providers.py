"""Check each configured LLM provider without printing credentials or model output."""

from __future__ import annotations

import argparse
import json

from backend.services.llm import check_provider, configured_providers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("active", "all", "nvidia", "gemini", "ollama"),
        default="active",
    )
    args = parser.parse_args()

    if args.provider == "active":
        providers = tuple(configured_providers())
    elif args.provider == "all":
        providers = ("nvidia", "gemini", "ollama")
    else:
        providers = (args.provider,)

    if not providers:
        print(json.dumps({"providers": [], "error": "no active provider is configured"}, indent=2))
        return 1

    results = [check_provider(provider) for provider in providers]
    print(json.dumps({"providers": results}, indent=2))
    return 1 if any(result["status"] == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
