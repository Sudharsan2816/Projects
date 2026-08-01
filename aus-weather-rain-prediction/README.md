# AUS Weather Rainfall Prediction

Leakage-aware machine-learning project for predicting next-day rain in Melbourne, Melbourne Airport, and Watsonia. The project emphasizes minority-class recall, probability quality, threshold tradeoffs, temporal validation, and data-drift monitoring rather than accuracy alone.

## Evaluation design

- Observations are sorted by date and split chronologically into 60% training, 20% validation, and 20% final test periods.
- Hyperparameter search uses expanding-window `TimeSeriesSplit` and balanced accuracy.
- The operating threshold is selected only on validation data by maximizing F2 subject to at least 50% precision.
- The untouched later test period reports rain precision/recall/F2, balanced accuracy, average precision, ROC AUC, Brier score, classification report, and confusion matrix.
- Training feature distributions are saved for PSI-based monitoring.

The latest results and limitations are in [`artifacts/MODEL_CARD.md`](artifacts/MODEL_CARD.md).

## Project structure

```text
app.py                         Streamlit inference and evaluation UI
train.py                       Temporal training, threshold selection, and reports
monitor.py                     PSI drift check for an incoming CSV
src/aus_weather/               Data, modeling, and drift package
tests/                         Unit tests for time splitting, metrics, and drift
artifacts/                     Model bundle, metrics, plots, and model card
Dockerfile                     Deployable Streamlit image
```

## Setup and verification

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
ruff check src tests train.py monitor.py app.py
```

## Train

```powershell
$env:PYTHONPATH = "src"
python train.py
```

The default command downloads the documented Australian weather CSV. A local copy can be supplied for reproducibility:

```powershell
python train.py --data .\data\weatherAUS-2.csv
```

## Run the app

```powershell
$env:PYTHONPATH = "src"
streamlit run app.py
```

Or run the deployable container:

```powershell
docker compose up --build
```

Open `http://localhost:8501`.

## Monitor drift

```powershell
$env:PYTHONPATH = "src"
python monitor.py --input .\data\incoming_weather.csv
```

The command compares incoming distributions with `artifacts/drift_reference.json`. PSI from `0.10` to `0.20` is a warning; PSI at or above `0.20` is flagged as drift and exits with status `2` for automation.

## Limitations

- Complete-case filtering can bias the population toward stations and periods with fewer missing readings.
- The model covers only three Melbourne-area locations and is not an official forecast.
- Threshold selection prioritizes catching rain, so false-positive forecasts are an accepted tradeoff.
- Production use requires scheduled outcome collection, calibration monitoring, retraining policy, and a broader geographic dataset.
