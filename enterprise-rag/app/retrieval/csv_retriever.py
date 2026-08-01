"""CSV retriever using pandas filtering."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config import DATA_DIR


def retrieve_csv_context(query: str, allowed_permissions: set[str], limit: int = 8) -> list[dict]:
    if "incident_reports" not in allowed_permissions:
        return []
    contexts: list[dict] = []
    terms = [term for term in query.lower().split() if len(term) > 2]
    for path in Path(DATA_DIR / "csv").glob("*.csv"):
        df = pd.read_csv(path)
        if df.empty:
            continue
        searchable = df.astype(str).agg(" ".join, axis=1).str.lower()
        mask = searchable.apply(lambda value: any(term in value for term in terms))
        matches = df[mask].head(limit)
        if matches.empty and any(token in query.lower() for token in ["incident", "outage", "csv"]):
            matches = df.head(limit)
        for _, row in matches.iterrows():
            contexts.append(
                {
                    "source": str(path),
                    "source_type": "csv",
                    "permission": "incident_reports",
                    "content": row.to_json(),
                }
            )
    return contexts[:limit]
