"""Train and evaluate leakage-safe AUS weather rainfall models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import precision_recall_curve, roc_curve

from aus_weather.config import ARTIFACT_DIR
from aus_weather.data import (
    chronological_train_validation_test_split,
    load_raw_data,
    prepare_melbourne_data,
    split_features_target,
)
from aus_weather.drift import build_reference_profile, compare_to_reference
from aus_weather.model import (
    build_logistic_pipeline,
    build_preprocessor,
    build_random_forest_pipeline,
    detect_feature_types,
    evaluate_model,
    fit_logistic_grid,
    fit_random_forest_grid,
    positive_class_probabilities,
    random_forest_feature_importance,
    select_decision_threshold,
)


def save_confusion_matrix(
    matrix: list[list[int]], labels: list[str], output_path: Path, title: str
) -> None:
    plt.figure(figsize=(5, 4))
    sns.heatmap(
        pd.DataFrame(matrix, index=labels, columns=labels),
        annot=True,
        fmt="d",
        cmap="Blues",
    )
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def save_feature_importance_plot(
    importance_df: pd.DataFrame, output_path: Path, top_n: int = 20
) -> None:
    top_features = importance_df.head(top_n)
    plt.figure(figsize=(10, 7))
    sns.barplot(data=top_features, x="importance", y="feature", color="#24746f")
    plt.title(f"Top {top_n} Features for Rainfall Prediction")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def save_probability_curves(
    y_true: pd.Series,
    probabilities: np.ndarray,
    output_path: Path,
    title: str,
) -> None:
    binary_true = (pd.Series(y_true).reset_index(drop=True) == "Yes").astype(int)
    precision, recall, _ = precision_recall_curve(binary_true, probabilities)
    false_positive_rate, true_positive_rate, _ = roc_curve(binary_true, probabilities)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(recall, precision, color="#24746f", linewidth=2)
    axes[0].set(title="Precision-recall curve", xlabel="Recall", ylabel="Precision")
    axes[0].grid(alpha=0.25)
    axes[1].plot(false_positive_rate, true_positive_rate, color="#c0504d", linewidth=2)
    axes[1].plot([0, 1], [0, 1], linestyle="--", color="#777777")
    axes[1].set(title="ROC curve", xlabel="False-positive rate", ylabel="True-positive rate")
    axes[1].grid(alpha=0.25)
    figure.suptitle(title)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def save_threshold_plot(
    y_true: pd.Series,
    probabilities: np.ndarray,
    selected_threshold: float,
    output_path: Path,
) -> None:
    binary_true = (pd.Series(y_true).reset_index(drop=True) == "Yes").astype(int)
    precision, recall, thresholds = precision_recall_curve(binary_true, probabilities)
    plt.figure(figsize=(8, 5))
    plt.plot(thresholds, precision[:-1], label="Precision", color="#24746f")
    plt.plot(thresholds, recall[:-1], label="Recall", color="#c0504d")
    plt.axvline(selected_threshold, color="#222222", linestyle="--", label="Selected threshold")
    plt.xlabel("Decision threshold")
    plt.ylabel("Score")
    plt.title("Validation threshold tradeoff")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def render_model_card(metrics: dict[str, Any]) -> str:
    champion = metrics["champion"]
    test = metrics[champion]["test"]
    split = metrics["temporal_split"]
    return "\n".join(
        [
            "# Rainfall Prediction Model Card",
            "",
            "## Intended use",
            "",
            "Predict next-day rainfall risk for Melbourne, Melbourne Airport, and Watsonia as a portfolio demonstration. It is not an official weather forecast or a safety-critical system.",
            "",
            "## Evaluation design",
            "",
            f"- Chronological training period: {split['train']['start']} to {split['train']['end']}",
            f"- Validation period used only for threshold selection: {split['validation']['start']} to {split['validation']['end']}",
            f"- Final test period: {split['test']['start']} to {split['test']['end']}",
            "- Hyperparameters use expanding-window `TimeSeriesSplit` and balanced accuracy.",
            "- The decision threshold maximizes validation F2 subject to minimum 50% precision.",
            "",
            "## Champion results",
            "",
            f"- Model: {champion.replace('_', ' ').title()}",
            f"- Threshold: {test['threshold']:.3f}",
            f"- Rain precision: {test['precision_yes']:.3f}",
            f"- Rain recall: {test['recall_yes']:.3f}",
            f"- Rain F2: {test['f2_yes']:.3f}",
            f"- Balanced accuracy: {test['balanced_accuracy']:.3f}",
            f"- Average precision: {test['average_precision']:.3f}",
            f"- ROC AUC: {test['roc_auc']:.3f}",
            f"- Brier score: {test['brier_score']:.3f}",
            "",
            "## Monitoring",
            "",
            "`artifacts/drift_reference.json` stores training distributions. Run `python monitor.py --input <csv>` to calculate PSI for incoming data. PSI >= 0.10 warns and PSI >= 0.20 flags drift.",
            "",
            "## Limitations",
            "",
            "Complete-case filtering may bias the sample, geography is limited, weather relationships can drift, and the selected threshold reflects an F2 preference for catching rain rather than minimizing all false alarms.",
            "",
        ]
    )


def _split_metadata(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(frame)),
        "start": frame["Date"].min().date().isoformat(),
        "end": frame["Date"].max().date().isoformat(),
        "rain_rate": float((frame["RainToday"] == "Yes").mean()),
    }


def main(source: str | None = None) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = load_raw_data(source) if source else load_raw_data()
    dated = prepare_melbourne_data(raw_df, keep_date=True)
    train_df, validation_df, test_df = chronological_train_validation_test_split(dated)
    x_train, y_train = split_features_target(train_df)
    x_validation, y_validation = split_features_target(validation_df)
    x_test, y_test = split_features_target(test_df)

    numeric_features, categorical_features = detect_feature_types(x_train)
    rf_grid = fit_random_forest_grid(
        build_random_forest_pipeline(build_preprocessor(numeric_features, categorical_features)),
        x_train,
        y_train,
    )
    logistic_grid = fit_logistic_grid(
        build_logistic_pipeline(build_preprocessor(numeric_features, categorical_features)),
        x_train,
        y_train,
    )

    model_results: dict[str, Any] = {}
    validation_probabilities: dict[str, np.ndarray] = {}
    test_probabilities: dict[str, np.ndarray] = {}
    models = {"random_forest": rf_grid, "logistic_regression": logistic_grid}
    for name, model in models.items():
        validation_probability = positive_class_probabilities(model, x_validation)
        threshold_selection = select_decision_threshold(y_validation, validation_probability)
        threshold = threshold_selection["threshold"]
        validation_metrics = evaluate_model(model, x_validation, y_validation, threshold=threshold)
        test_metrics = evaluate_model(model, x_test, y_test, threshold=threshold)
        validation_probabilities[name] = validation_probability
        test_probabilities[name] = positive_class_probabilities(model, x_test)
        model_results[name] = {
            "best_params": model.best_params_,
            "best_cv_balanced_accuracy": model.best_score_,
            "threshold_selection": threshold_selection,
            "validation": validation_metrics,
            "test": test_metrics,
        }

    champion = max(
        model_results,
        key=lambda name: model_results[name]["validation"]["average_precision"],
    )
    champion_model = models[champion]
    champion_threshold = model_results[champion]["threshold_selection"]["threshold"]
    joblib.dump(
        {"model": champion_model, "threshold": champion_threshold, "model_name": champion},
        ARTIFACT_DIR / "rain_model_bundle.joblib",
    )

    rf_importance = random_forest_feature_importance(
        rf_grid, numeric_features, categorical_features
    )
    rf_importance.to_csv(ARTIFACT_DIR / "random_forest_feature_importance.csv", index=False)
    save_feature_importance_plot(
        rf_importance, ARTIFACT_DIR / "random_forest_feature_importance.png"
    )

    for name in models:
        metrics = model_results[name]["test"]
        display_name = name.replace("_", " ").title()
        save_confusion_matrix(
            metrics["confusion_matrix"],
            ["No", "Yes"],
            ARTIFACT_DIR / f"{name}_confusion_matrix.png",
            f"{display_name} confusion matrix",
        )
        save_probability_curves(
            y_test,
            test_probabilities[name],
            ARTIFACT_DIR / f"{name}_probability_curves.png",
            f"{display_name} held-out test curves",
        )

    save_threshold_plot(
        y_validation,
        validation_probabilities[champion],
        champion_threshold,
        ARTIFACT_DIR / "champion_threshold_tradeoff.png",
    )

    reference_profile = build_reference_profile(x_train, numeric_features, categorical_features)
    drift_report = compare_to_reference(x_test, reference_profile)
    (ARTIFACT_DIR / "drift_reference.json").write_text(
        json.dumps(_json_ready(reference_profile), indent=2), encoding="utf-8"
    )
    (ARTIFACT_DIR / "drift_report.json").write_text(
        json.dumps(_json_ready(drift_report), indent=2), encoding="utf-8"
    )

    metrics = {
        "evaluation_strategy": {
            "split": "chronological 60/20/20",
            "cross_validation": "expanding-window TimeSeriesSplit(n_splits=5)",
            "hyperparameter_metric": "balanced_accuracy",
            "threshold_metric": "validation F2 with minimum precision 0.50",
        },
        "dataset_rows": int(len(dated)),
        "target_counts": {str(key): int(value) for key, value in dated["RainToday"].value_counts().items()},
        "temporal_split": {
            "train": _split_metadata(train_df),
            "validation": _split_metadata(validation_df),
            "test": _split_metadata(test_df),
        },
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "champion": champion,
        **model_results,
        "test_drift": drift_report,
    }
    ready_metrics = _json_ready(metrics)
    (ARTIFACT_DIR / "metrics.json").write_text(
        json.dumps(ready_metrics, indent=2), encoding="utf-8"
    )
    (ARTIFACT_DIR / "MODEL_CARD.md").write_text(render_model_card(ready_metrics), encoding="utf-8")

    champion_test = ready_metrics[champion]["test"]
    print("Training complete.")
    print(f"Champion: {champion}")
    print(f"Decision threshold: {champion_threshold:.3f}")
    print(f"Rain precision: {champion_test['precision_yes']:.3f}")
    print(f"Rain recall: {champion_test['recall_yes']:.3f}")
    print(f"Average precision: {champion_test['average_precision']:.3f}")
    print(f"Artifacts saved to: {ARTIFACT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="Optional local CSV path; defaults to the documented URL")
    arguments = parser.parse_args()
    main(arguments.data)
