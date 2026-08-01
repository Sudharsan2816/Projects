import json
from pathlib import Path

from app.evaluation.rbac_eval import evaluate_case, run_suite

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_allowed_and_denied_eval_cases():
    allowed = evaluate_case(
        {
            "id": "finance",
            "role": "Finance",
            "query": "show finance revenue",
            "expected_intent": "sql",
            "expected_decision": "allowed",
            "expected_authorized_permissions": ["finance_db"],
        }
    )
    denied = evaluate_case(
        {
            "id": "engineer-hr",
            "role": "Engineer",
            "query": "show employee salary records",
            "expected_intent": "sql",
            "expected_decision": "access_denied",
        }
    )

    assert allowed["passed"] is True
    assert denied["passed"] is True


def test_committed_rbac_suite_passes():
    fixture_path = PROJECT_ROOT / "evals" / "rbac_cases.json"
    assert json.loads(fixture_path.read_text(encoding="utf-8"))

    results = run_suite(fixture_path)

    assert results["cases"] >= 7
    assert results["failed"] == 0
