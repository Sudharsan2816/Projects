"""Management CLI for repeatable schema initialization and demo seeding."""

from __future__ import annotations

import argparse
import json

from app.seed import initialize_schema, seed_demo_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Enterprise RAG database management")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init-db", help="Create missing database tables without deleting data")
    subcommands.add_parser("seed-demo", help="Idempotently initialize and seed the demo dataset")
    args = parser.parse_args()

    if args.command == "init-db":
        initialize_schema()
        print(json.dumps({"status": "ok", "command": "init-db"}))
    else:
        result = seed_demo_dataset()
        print(json.dumps({"status": "ok", "command": "seed-demo", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
