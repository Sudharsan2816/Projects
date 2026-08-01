import pandas as pd
import pytest

from aus_weather.data import (
    chronological_train_validation_test_split,
    date_to_season,
    prepare_melbourne_data,
    split_features_target,
)


def test_australian_seasons():
    assert date_to_season(pd.Timestamp("2026-01-15")) == "Summer"
    assert date_to_season(pd.Timestamp("2026-07-15")) == "Winter"


def test_prepare_and_temporal_split_prevent_future_leakage():
    rows = []
    for index in range(20):
        rows.append(
            {
                "Date": f"2020-01-{index + 1:02d}",
                "Location": "Melbourne",
                "RainToday": "No",
                "RainTomorrow": "Yes" if index % 3 == 0 else "No",
                "MinTemp": float(index),
            }
        )
    prepared = prepare_melbourne_data(pd.DataFrame(rows), keep_date=True)
    train, validation, test = chronological_train_validation_test_split(prepared)

    assert train["Date"].max() < validation["Date"].min()
    assert validation["Date"].max() < test["Date"].min()
    features, target = split_features_target(train)
    assert "Date" not in features
    assert target.name == "RainToday"


def test_temporal_split_requires_dates():
    with pytest.raises(ValueError, match="Date column"):
        chronological_train_validation_test_split(pd.DataFrame({"x": range(10)}))
