# Rainfall Prediction Model Card

## Intended use

Predict next-day rainfall risk for Melbourne, Melbourne Airport, and Watsonia as a portfolio demonstration. It is not an official weather forecast or a safety-critical system.

## Evaluation design

- Chronological training period: 2008-07-01 to 2013-11-15
- Validation period used only for threshold selection: 2013-11-16 to 2015-10-28
- Final test period: 2015-10-29 to 2017-06-25
- Hyperparameters use expanding-window `TimeSeriesSplit` and balanced accuracy.
- The decision threshold maximizes validation F2 subject to minimum 50% precision.

## Champion results

- Model: Logistic Regression
- Threshold: 0.502
- Rain precision: 0.554
- Rain recall: 0.721
- Rain F2: 0.680
- Balanced accuracy: 0.768
- Average precision: 0.664
- ROC AUC: 0.844
- Brier score: 0.152

## Monitoring

`artifacts/drift_reference.json` stores training distributions. Run `python monitor.py --input <csv>` to calculate PSI for incoming data. PSI >= 0.10 warns and PSI >= 0.20 flags drift.

## Limitations

Complete-case filtering may bias the sample, geography is limited, weather relationships can drift, and the selected threshold reflects an F2 preference for catching rain rather than minimizing all false alarms.
