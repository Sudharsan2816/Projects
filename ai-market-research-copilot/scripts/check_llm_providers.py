"""Check each configured LLM provider without printing credentials or model output."""

from __future__ import annotations

import argparse
import json

from backend.services.llm import check_provider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("all", "nvidia", "gemini", "ollama"),
        default="all",
    )
    args = parser.parse_args()

    providers = ("nvidia", "gemini", "ollama") if args.provider == "all" else (args.provider,)
    results = [check_provider(provider) for provider in providers]
    print(json.dumps({"providers": results}, indent=2))
    return 1 if any(result["status"] == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
