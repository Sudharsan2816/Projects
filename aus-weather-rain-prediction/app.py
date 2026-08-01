"""Streamlit app for Melbourne-area rainfall prediction."""

from __future__ import annotations

import json

import joblib
import pandas as pd
import streamlit as st

from aus_weather.config import ARTIFACT_DIR
from aus_weather.data import date_to_season

MODEL_PATH = ARTIFACT_DIR / "rain_model_bundle.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
IMPORTANCE_PATH = ARTIFACT_DIR / "random_forest_feature_importance.csv"
DRIFT_PATH = ARTIFACT_DIR / "drift_report.json"


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics() -> dict:
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@st.cache_data
def load_importance() -> pd.DataFrame:
    return pd.read_csv(IMPORTANCE_PATH)


@st.cache_data
def load_drift_report() -> dict | None:
    if not DRIFT_PATH.exists():
        return None
    return json.loads(DRIFT_PATH.read_text(encoding="utf-8"))


def build_input_row() -> pd.DataFrame:
    st.sidebar.header("Weather Inputs")
    location = st.sidebar.selectbox("Location", ["Melbourne", "MelbourneAirport", "Watsonia"])
    date = st.sidebar.date_input("Date")

    values = {
        "Location": location,
        "MinTemp": st.sidebar.number_input("Min temperature", value=12.0, step=0.5),
        "MaxTemp": st.sidebar.number_input("Max temperature", value=22.0, step=0.5),
        "Rainfall": st.sidebar.number_input("Rainfall", value=0.0, min_value=0.0, step=0.2),
        "Evaporation": st.sidebar.number_input("Evaporation", value=4.5, min_value=0.0, step=0.5),
        "Sunshine": st.sidebar.number_input("Sunshine hours", value=7.0, min_value=0.0, step=0.5),
        "WindGustDir": st.sidebar.selectbox("Wind gust direction", ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "WindGustSpeed": st.sidebar.number_input("Wind gust speed", value=35.0, min_value=0.0, step=1.0),
        "WindDir9am": st.sidebar.selectbox("Wind direction 9am", ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "WindDir3pm": st.sidebar.selectbox("Wind direction 3pm", ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "WindSpeed9am": st.sidebar.number_input("Wind speed 9am", value=13.0, min_value=0.0, step=1.0),
        "WindSpeed3pm": st.sidebar.number_input("Wind speed 3pm", value=17.0, min_value=0.0, step=1.0),
        "Humidity9am": st.sidebar.number_input("Humidity 9am", value=70.0, min_value=0.0, max_value=100.0, step=1.0),
        "Humidity3pm": st.sidebar.number_input("Humidity 3pm", value=50.0, min_value=0.0, max_value=100.0, step=1.0),
        "Pressure9am": st.sidebar.number_input("Pressure 9am", value=1017.0, step=0.5),
        "Pressure3pm": st.sidebar.number_input("Pressure 3pm", value=1014.0, step=0.5),
        "Cloud9am": st.sidebar.number_input("Cloud 9am", value=4.0, min_value=0.0, max_value=9.0, step=1.0),
        "Cloud3pm": st.sidebar.number_input("Cloud 3pm", value=4.0, min_value=0.0, max_value=9.0, step=1.0),
        "Temp9am": st.sidebar.number_input("Temperature 9am", value=16.0, step=0.5),
        "Temp3pm": st.sidebar.number_input("Temperature 3pm", value=21.0, step=0.5),
        "RainYesterday": st.sidebar.selectbox("Rained yesterday", ["No", "Yes"]),
        "Season": date_to_season(pd.Timestamp(date)),
    }
    return pd.DataFrame([values])


def main() -> None:
    st.set_page_config(page_title="AUS Weather Rainfall Prediction", layout="wide")
    st.title("AUS Weather Rainfall Prediction")
    st.caption("Melbourne, Melbourne Airport, and Watsonia rainfall classifier")

    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        st.error("Model artifacts are missing. Run `python train.py` before launching the app.")
        st.stop()

    bundle = load_model()
    model = bundle["model"]
    threshold = float(bundle["threshold"])
    champion_name = str(bundle["model_name"])
    metrics = load_metrics()
    input_df = build_input_row()

    probability = model.predict_proba(input_df)[0]
    classes = list(model.classes_)
    rain_probability = float(probability[classes.index("Yes")])
    prediction = "Yes" if rain_probability >= threshold else "No"
    champion_metrics = metrics[champion_name]["test"]

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Prediction", prediction)
    col_b.metric("Rain probability", f"{rain_probability:.1%}")
    col_c.metric("Decision threshold", f"{threshold:.1%}")
    col_d.metric("Held-out rain recall", f"{champion_metrics['recall_yes']:.1%}")

    st.caption(
        "The threshold was selected on a chronological validation period using F2, "
        "then evaluated once on the later held-out test period."
    )

    st.subheader("Input Record")
    st.dataframe(input_df, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Model Comparison")
        comparison = pd.DataFrame(
            [
                {
                    "model": "Random Forest",
                    "rain_precision": metrics["random_forest"]["test"]["precision_yes"],
                    "rain_recall": metrics["random_forest"]["test"]["recall_yes"],
                    "average_precision": metrics["random_forest"]["test"]["average_precision"],
                    "balanced_accuracy": metrics["random_forest"]["test"]["balanced_accuracy"],
                },
                {
                    "model": "Logistic Regression",
                    "rain_precision": metrics["logistic_regression"]["test"]["precision_yes"],
                    "rain_recall": metrics["logistic_regression"]["test"]["recall_yes"],
                    "average_precision": metrics["logistic_regression"]["test"]["average_precision"],
                    "balanced_accuracy": metrics["logistic_regression"]["test"]["balanced_accuracy"],
                },
            ]
        )
        st.dataframe(comparison, use_container_width=True)

    with right:
        st.subheader("Top Feature Importances")
        importance = load_importance().head(15)
        st.bar_chart(importance.set_index("feature")["importance"])

    drift = load_drift_report()
    if drift:
        st.subheader("Temporal Drift Check")
        drift_a, drift_b, drift_c = st.columns(3)
        drift_a.metric("Status", drift["status"].upper())
        drift_b.metric("Maximum PSI", f"{drift['max_psi']:.3f}")
        drift_c.metric("Flagged features", len(drift["drifted_features"]))
        if drift["drifted_features"]:
            st.write(", ".join(drift["drifted_features"]))


if __name__ == "__main__":
    main()
