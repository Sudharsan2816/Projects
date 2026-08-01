# RBAC Evaluation Report

Generated: 2026-08-01T06:45:40.363394+00:00

Pass rate: **7/7 (100%)**

| Case | Role | Intent | Decision | Result |
|---|---|---|---|---|
| engineer-operational-logs | Engineer | json | allowed | PASS |
| engineer-employee-denied | Engineer | sql | access_denied | PASS |
| hr-employee-allowed | HR | sql | allowed | PASS |
| finance-revenue-allowed | Finance | sql | allowed | PASS |
| operations-incident-allowed | Operations | csv | allowed | PASS |
| finance-compliance-denied | Finance | pdf | access_denied | PASS |
| admin-hybrid-allowed | Admin | hybrid | allowed | PASS |

The suite verifies intent routing, allowed-vs-denied authorization decisions, and expected authorized permission paths before retrieval. It does not treat an empty retriever result as an authorization success.
