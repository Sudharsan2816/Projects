"""Data loading and preparation utilities."""

from __future__ import annotations

import pandas as pd

from .config import DATA_URL, MELBOURNE_LOCATIONS


def date_to_season(date: pd.Timestamp) -> str:
    """Map an Australian calendar date to a season."""
    month = date.month
    if month in (12, 1, 2):
        return "Summer"
    if month in (3, 4, 5):
        return "Autumn"
    if month in (6, 7, 8):
        return "Winter"
    return "Spring"


def load_raw_data(source: str = DATA_URL) -> pd.DataFrame:
    """Load the raw Australian weather dataset."""
    return pd.read_csv(source)


def prepare_melbourne_data(df: pd.DataFrame, *, keep_date: bool = False) -> pd.DataFrame:
    """Prepare the Melbourne-area rainfall modeling dataset."""
    prepared = df.dropna().copy()
    prepared = prepared.rename(
        columns={
            "RainToday": "RainYesterday",
            "RainTomorrow": "RainToday",
        }
    )
    prepared = prepared[prepared["Location"].isin(MELBOURNE_LOCATIONS)].copy()
    prepared["Date"] = pd.to_datetime(prepared["Date"])
    prepared["Season"] = prepared["Date"].apply(date_to_season)
    prepared = prepared.sort_values("Date").reset_index(drop=True)
    if not keep_date:
        prepared = prepared.drop(columns=["Date"])
    return prepared


def chronological_train_validation_test_split(
    df: pd.DataFrame,
    *,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split ordered observations without allowing future records into training."""
    if "Date" not in df.columns:
        raise ValueError("Date column is required for chronological splitting")
    if train_fraction <= 0 or validation_fraction <= 0:
        raise ValueError("Split fractions must be positive")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must leave a test partition")

    ordered = df.sort_values("Date").reset_index(drop=True)
    train_end = int(len(ordered) * train_fraction)
    validation_end = int(len(ordered) * (train_fraction + validation_fraction))
    if train_end == 0 or validation_end <= train_end or validation_end >= len(ordered):
        raise ValueError("Dataset is too small for the requested temporal split")
    return (
        ordered.iloc[:train_end].copy(),
        ordered.iloc[train_end:validation_end].copy(),
        ordered.iloc[validation_end:].copy(),
    )


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split the prepared dataframe into features and target."""
    x = df.drop(columns=["RainToday", "Date"], errors="ignore")
    y = df["RainToday"]
    return x, y
