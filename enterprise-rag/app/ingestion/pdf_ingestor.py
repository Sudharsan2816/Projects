"""PDF and text document ingestion."""

from __future__ import annotations

from pathlib import Path

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.retrieval.vector_store import vector_store


def infer_permission_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if "compliance" in lowered:
        return "compliance_docs"
    if "policy" in lowered:
        return "policies"
    if "hr" in lowered or "employee" in lowered:
        return "HR_documents"
    if "finance" in lowered:
        return "financial_reports"
    if "incident" in lowered:
        return "incident_reports"
    return "technical_docs"


def extract_pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def ingest_pdf(path: str | Path, permission: str | None = None) -> int:
    pdf_path = Path(path)
    text = extract_pdf_text(pdf_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_text(text)
    doc_permission = permission or infer_permission_from_filename(pdf_path.name)
    metadatas = [
        {
            "source": str(pdf_path),
            "source_type": "pdf",
            "permission": doc_permission,
            "chunk_id": idx,
            "content": chunk,
        }
        for idx, chunk in enumerate(chunks)
    ]
    return vector_store.add_texts(chunks, metadatas)


def ingest_text_file(path: str | Path, permission: str | None = None) -> int:
    text_path = Path(path)
    text = text_path.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_text(text)
    doc_permission = permission or infer_permission_from_filename(text_path.name)
    metadatas = [
        {
            "source": str(text_path),
            "source_type": "text",
            "permission": doc_permission,
            "chunk_id": idx,
            "content": chunk,
        }
        for idx, chunk in enumerate(chunks)
    ]
    return vector_store.add_texts(chunks, metadatas)
