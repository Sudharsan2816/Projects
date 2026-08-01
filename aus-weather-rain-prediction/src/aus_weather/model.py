"""Model training and evaluation utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import RANDOM_STATE


def detect_feature_types(x_train: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Detect numeric and categorical feature columns."""
    numeric_features = x_train.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = x_train.select_dtypes(exclude=["number"]).columns.tolist()
    return numeric_features, categorical_features


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """Build the preprocessing transformer."""
    numeric_transformer = Pipeline(steps=[("scaler", StandardScaler())])
    categorical_transformer = Pipeline(
        steps=[("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def build_random_forest_pipeline(preprocessor: ColumnTransformer) -> Pipeline:
    """Build a Random Forest classification pipeline."""
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(random_state=RANDOM_STATE)),
        ]
    )


def build_logistic_pipeline(preprocessor: ColumnTransformer) -> Pipeline:
    """Build a Logistic Regression classification pipeline."""
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(random_state=RANDOM_STATE, max_iter=1000),
            ),
        ]
    )


def fit_random_forest_grid(pipeline: Pipeline, x_train: pd.DataFrame, y_train: pd.Series) -> GridSearchCV:
    """Fit a compact Random Forest grid search."""
    param_grid = {
        "classifier__n_estimators": [50, 100],
        "classifier__max_depth": [None, 10, 20],
        "classifier__min_samples_split": [2, 5],
    }
    cv = TimeSeriesSplit(n_splits=5)
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="balanced_accuracy",
        verbose=1,
        n_jobs=1,
    )
    grid_search.fit(x_train, y_train)
    return grid_search


def fit_logistic_grid(pipeline: Pipeline, x_train: pd.DataFrame, y_train: pd.Series) -> GridSearchCV:
    """Fit a compact Logistic Regression grid search."""
    param_grid = {
        "classifier__solver": ["liblinear"],
        "classifier__penalty": ["l1", "l2"],
        "classifier__class_weight": [None, "balanced"],
    }
    cv = TimeSeriesSplit(n_splits=5)
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="balanced_accuracy",
        verbose=1,
        n_jobs=1,
    )
    grid_search.fit(x_train, y_train)
    return grid_search


def positive_class_probabilities(
    model: Pipeline | GridSearchCV, x: pd.DataFrame, positive_label: str = "Yes"
) -> np.ndarray:
    classes = list(model.classes_)
    return np.asarray(model.predict_proba(x)[:, classes.index(positive_label)], dtype=float)


def select_decision_threshold(
    y_true: pd.Series,
    probabilities: np.ndarray,
    *,
    beta: float = 2.0,
    minimum_precision: float = 0.50,
) -> dict[str, float]:
    """Choose a validation-only threshold that favors recall while bounding precision."""
    binary_true = (pd.Series(y_true).reset_index(drop=True) == "Yes").astype(int)
    precision, recall, thresholds = precision_recall_curve(binary_true, probabilities)
    candidates: list[dict[str, float]] = []
    for index, threshold in enumerate(thresholds):
        candidate_precision = float(precision[index])
        candidate_recall = float(recall[index])
        denominator = beta**2 * candidate_precision + candidate_recall
        f_beta = (
            (1 + beta**2) * candidate_precision * candidate_recall / denominator
            if denominator
            else 0.0
        )
        candidates.append(
            {
                "threshold": float(threshold),
                "precision": candidate_precision,
                "recall": candidate_recall,
                "f_beta": float(f_beta),
            }
        )
    eligible = [item for item in candidates if item["precision"] >= minimum_precision]
    pool = eligible or candidates
    if not pool:
        return {"threshold": 0.5, "precision": 0.0, "recall": 0.0, "f_beta": 0.0}
    return max(pool, key=lambda item: (item["f_beta"], item["recall"], -item["threshold"]))


def evaluate_model(
    model: Pipeline | GridSearchCV,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    threshold: float = 0.5,
) -> dict:
    """Evaluate probabilities and thresholded predictions on a held-out partition."""
    probabilities = positive_class_probabilities(model, x_test)
    binary_true = (pd.Series(y_test).reset_index(drop=True) == "Yes").astype(int)
    binary_pred = (probabilities >= threshold).astype(int)
    y_pred = pd.Series(np.where(binary_pred == 1, "Yes", "No"))
    return {
        "threshold": float(threshold),
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(binary_true, binary_pred),
        "precision_yes": precision_score(binary_true, binary_pred, zero_division=0),
        "recall_yes": recall_score(binary_true, binary_pred, zero_division=0),
        "f2_yes": fbeta_score(binary_true, binary_pred, beta=2, zero_division=0),
        "average_precision": average_precision_score(binary_true, probabilities),
        "roc_auc": roc_auc_score(binary_true, probabilities),
        "brier_score": brier_score_loss(binary_true, probabilities),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "classification_report_text": classification_report(y_test, y_pred),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=["No", "Yes"]).tolist(),
    }


def random_forest_feature_importance(
    grid_search: GridSearchCV,
    numeric_features: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    """Return sorted feature importance values from a fitted Random Forest grid."""
    best_pipeline = grid_search.best_estimator_
    onehot = (
        best_pipeline["preprocessor"]
        .named_transformers_["cat"]
        .named_steps["onehot"]
    )
    feature_names = numeric_features + list(onehot.get_feature_names_out(categorical_features))
    importances = best_pipeline["classifier"].feature_importances_
    return (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
