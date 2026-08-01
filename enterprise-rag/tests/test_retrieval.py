from app.config import DATA_DIR
from app.ingestion.csv_ingestor import validate_csv
from app.ingestion.json_ingestor import validate_json
from app.ingestion.pdf_ingestor import ingest_pdf
from app.models import EnterpriseSessionLocal
from app.retrieval.csv_retriever import retrieve_csv_context
from app.retrieval.json_retriever import retrieve_json_context
from app.retrieval.sql_retriever import retrieve_sql_context
from app.seed_data import seed_demo_files


def test_pdf_ingestion_indexes_chunks():
    seed_demo_files()
    chunks = ingest_pdf(DATA_DIR / "pdfs" / "technical_architecture.pdf")
    assert chunks > 0


def test_csv_retrieval():
    seed_demo_files()
    assert validate_csv(DATA_DIR / "csv" / "incident_reports.csv") > 0
    contexts = retrieve_csv_context("incident outage", {"incident_reports"})
    assert contexts


def test_json_retrieval():
    seed_demo_files()
    assert validate_json(DATA_DIR / "json_logs" / "operational_logs.json") > 0
    contexts = retrieve_json_context("outage logs", {"operational_logs"})
    assert contexts


def test_sql_retrieval():
    db = EnterpriseSessionLocal()
    try:
        contexts = retrieve_sql_context("finance revenue", db, {"finance_db"})
        assert isinstance(contexts, list)
    finally:
        db.close()
