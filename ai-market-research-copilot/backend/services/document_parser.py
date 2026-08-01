from pathlib import Path
from typing import Any, Dict, List

import fitz  # PyMuPDF
import pandas as pd

from backend.core.logging import get_logger

logger = get_logger(__name__)


def parse_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """Extract text page-by-page from a PDF."""
    pages = []
    try:
        doc = fitz.open(str(file_path))
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "page": i + 1,
                    "text": text,
                    "source": file_path.name,
                })
        doc.close()
        logger.info(f"Parsed PDF '{file_path.name}': {len(pages)} pages")
    except Exception as e:
        logger.error(f"PDF parse error for {file_path.name}: {e}")
        raise
    return pages


def parse_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Convert CSV rows into text chunks suitable for embedding."""
    chunks = []
    try:
        df = pd.read_csv(str(file_path))
        # Convert to readable text blocks (50 rows per chunk)
        chunk_size = 50
        for i in range(0, len(df), chunk_size):
            slice_df = df.iloc[i : i + chunk_size]
            text = slice_df.to_string(index=False)
            chunks.append({
                "page": (i // chunk_size) + 1,
                "text": text,
                "source": file_path.name,
            })
        logger.info(f"Parsed CSV '{file_path.name}': {len(df)} rows → {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"CSV parse error for {file_path.name}: {e}")
        raise
    return chunks


def parse_txt(file_path: Path) -> List[Dict[str, Any]]:
    """Split a plain text file into ~1000-char sections."""
    chunks = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        section_size = 1000
        parts = [text[i : i + section_size] for i in range(0, len(text), section_size)]
        for idx, part in enumerate(parts):
            if part.strip():
                chunks.append({
                    "page": idx + 1,
                    "text": part.strip(),
                    "source": file_path.name,
                })
        logger.info(f"Parsed TXT '{file_path.name}': {len(chunks)} sections")
    except Exception as e:
        logger.error(f"TXT parse error for {file_path.name}: {e}")
        raise
    return chunks


def parse_document(file_path: Path) -> List[Dict[str, Any]]:
    """Dispatch to the right parser based on file extension."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".csv":
        return parse_csv(file_path)
    elif ext in (".txt", ".md"):
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
