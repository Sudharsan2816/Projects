"""CSV ingestion helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def validate_csv(path: str | Path) -> int:
    csv_path = Path(path)
    df = pd.read_csv(csv_path)
    return int(len(df))
