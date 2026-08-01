"""Reference-profile creation and lightweight data-drift checks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

EPSILON = 1e-6


def _normalized_counts(values: pd.Series, categories: list[str]) -> np.ndarray:
    counts = values.astype(str).value_counts(normalize=True)
    return np.asarray([float(counts.get(category, 0.0)) for category in categories])


def population_stability_index(expected: np.ndarray, actual: np.ndarray) -> float:
    expected_safe = np.clip(expected.astype(float), EPSILON, None)
    actual_safe = np.clip(actual.astype(float), EPSILON, None)
    return float(np.sum((actual_safe - expected_safe) * np.log(actual_safe / expected_safe)))


def build_reference_profile(
    frame: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict[str, Any]:
    numeric: dict[str, Any] = {}
    for feature in numeric_features:
        values = pd.to_numeric(frame[feature], errors="coerce").dropna()
        edges = sorted(set(float(value) for value in values.quantile([0.1, 0.25, 0.5, 0.75, 0.9])))
        boundaries = [-np.inf, *edges, np.inf]
        counts, _ = np.histogram(values, bins=boundaries)
        proportions = counts / counts.sum() if counts.sum() else np.zeros(len(counts))
        numeric[feature] = {
            "cut_points": edges,
            "proportions": proportions.tolist(),
            "mean": float(values.mean()),
            "std": float(values.std(ddof=0)),
        }

    categorical: dict[str, Any] = {}
    for feature in categorical_features:
        values = frame[feature].astype(str)
        categories = sorted(values.unique().tolist())
        categorical[feature] = {
            "categories": categories,
            "proportions": _normalized_counts(values, categories).tolist(),
        }
    return {
        "rows": int(len(frame)),
        "numeric": numeric,
        "categorical": categorical,
    }


def compare_to_reference(frame: pd.DataFrame, profile: dict[str, Any]) -> dict[str, Any]:
    feature_results: dict[str, Any] = {}
    for feature, reference in profile["numeric"].items():
        values = pd.to_numeric(frame[feature], errors="coerce").dropna()
        boundaries = [-np.inf, *reference["cut_points"], np.inf]
        counts, _ = np.histogram(values, bins=boundaries)
        actual = counts / counts.sum() if counts.sum() else np.zeros(len(counts))
        psi = population_stability_index(np.asarray(reference["proportions"]), actual)
        feature_results[feature] = {"type": "numeric", "psi": psi}

    for feature, reference in profile["categorical"].items():
        values = frame[feature].astype(str)
        categories = sorted(set(reference["categories"]) | set(values.unique().tolist()))
        expected_map = dict(zip(reference["categories"], reference["proportions"], strict=True))
        expected = np.asarray([expected_map.get(category, 0.0) for category in categories])
        actual = _normalized_counts(values, categories)
        psi = population_stability_index(expected, actual)
        feature_results[feature] = {"type": "categorical", "psi": psi}

    max_psi = max((item["psi"] for item in feature_results.values()), default=0.0)
    drifted = sorted(
        feature for feature, result in feature_results.items() if result["psi"] >= 0.20
    )
    warning = sorted(
        feature
        for feature, result in feature_results.items()
        if 0.10 <= result["psi"] < 0.20
    )
    return {
        "rows": int(len(frame)),
        "status": "drift" if drifted else "warning" if warning else "stable",
        "max_psi": float(max_psi),
        "drifted_features": drifted,
        "warning_features": warning,
        "features": feature_results,
        "thresholds": {"warning": 0.10, "drift": 0.20},
    }
