"""Executable RBAC routing evaluation over committed role/query fixtures."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.routing.query_router import route_query
from app.security.rbac import allowed_permissions

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = PROJECT_ROOT / "evals" / "rbac_cases.json"
DEFAULT_RESULTS = PROJECT_ROOT / "evals" / "rbac_eval_results.json"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "RBAC_EVALUATION.md"


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    route = route_query(case["query"])
    permissions = allowed_permissions(case["role"])
    authorized = sorted(set(route["required_permissions"]) & permissions)
    denied = sorted(set(route["required_permissions"]) - permissions)
    decision = "access_denied" if not authorized else "allowed"
    passed = (
        route["intent"] == case["expected_intent"]
        and decision == case["expected_decision"]
        and set(case.get("expected_authorized_permissions", [])) <= set(authorized)
    )
    return {
        "id": case["id"],
        "role": case["role"],
        "query": case["query"],
        "intent": route["intent"],
        "decision": decision,
        "authorized_permissions": authorized,
        "denied_permissions": denied,
        "passed": passed,
    }


def run_suite(path: Path) -> dict[str, Any]:
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    cases = [evaluate_case(case) for case in fixtures]
    passed = sum(1 for case in cases if case["passed"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cases": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "pass_rate": passed / len(cases) if cases else 0.0,
        "results": cases,
    }


def render_markdown(results: dict[str, Any]) -> str:
    rows = [
        f"| {case['id']} | {case['role']} | {case['intent']} | {case['decision']} | {'PASS' if case['passed'] else 'FAIL'} |"
        for case in results["results"]
    ]
    return "\n".join(
        [
            "# RBAC Evaluation Report",
            "",
            f"Generated: {results['generated_at']}",
            "",
            f"Pass rate: **{results['passed']}/{results['cases']} ({results['pass_rate']:.0%})**",
            "",
            "| Case | Role | Intent | Decision | Result |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "The suite verifies intent routing, allowed-vs-denied authorization decisions, and expected authorized permission paths before retrieval. It does not treat an empty retriever result as an authorization success.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = run_suite(args.fixtures)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(results), encoding="utf-8")
    return 1 if args.check and results["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
