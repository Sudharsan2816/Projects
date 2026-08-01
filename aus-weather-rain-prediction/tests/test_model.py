import numpy as np
import pandas as pd

from aus_weather.model import evaluate_model, select_decision_threshold


class ProbabilityModel:
    classes_ = np.asarray(["No", "Yes"])

    def __init__(self, probabilities):
        self.probabilities = np.asarray(probabilities, dtype=float)

    def predict_proba(self, _frame):
        return np.column_stack([1 - self.probabilities, self.probabilities])


def test_threshold_selection_favors_recall_with_precision_floor():
    target = pd.Series(["No", "No", "Yes", "Yes", "Yes"])
    probabilities = np.asarray([0.10, 0.45, 0.40, 0.60, 0.90])

    selected = select_decision_threshold(target, probabilities, minimum_precision=0.50)

    assert 0.0 <= selected["threshold"] <= 1.0
    assert selected["precision"] >= 0.50
    assert selected["recall"] >= 2 / 3


def test_evaluate_model_reports_imbalanced_metrics():
    target = pd.Series(["No", "No", "Yes", "Yes"])
    model = ProbabilityModel([0.10, 0.60, 0.55, 0.90])
    metrics = evaluate_model(model, pd.DataFrame({"x": range(4)}), target, threshold=0.50)

    assert metrics["precision_yes"] == 2 / 3
    assert metrics["recall_yes"] == 1.0
    assert metrics["average_precision"] > 0.8
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]
