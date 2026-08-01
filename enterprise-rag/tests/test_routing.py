from app.routing.intent_classifier import classify_intent
from app.routing.query_router import route_query


def test_intent_classifier_logs():
    assert classify_intent("show outage logs") == "json"


def test_intent_classifier_csv():
    assert classify_intent("show incident report csv") == "csv"


def test_query_router_sql():
    route = route_query("fetch employee records")
    assert route["intent"] == "sql"
    assert "sql" in route["source_types"]
    assert route["required_permissions"] == ["employee_records"]


def test_query_router_narrows_compliance_permission():
    route = route_query("summarize compliance manual")

    assert route["intent"] == "pdf"
    assert route["required_permissions"] == ["compliance_docs"]
