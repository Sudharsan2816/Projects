"""Compare an incoming weather CSV with the committed training reference profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aus_weather.config import ARTIFACT_DIR
from aus_weather.data import load_raw_data, prepare_melbourne_data, split_features_target
from aus_weather.drift import compare_to_reference


def main(input_path: Path, output_path: Path) -> int:
    reference_path = ARTIFACT_DIR / "drift_reference.json"
    if not reference_path.exists():
        raise FileNotFoundError("Missing drift reference. Run `python train.py` first.")
    profile = json.loads(reference_path.read_text(encoding="utf-8"))
    prepared = prepare_melbourne_data(load_raw_data(str(input_path)), keep_date=True)
    features, _ = split_features_target(prepared)
    report = compare_to_reference(features, profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "max_psi": report["max_psi"]}))
    return 2 if report["status"] == "drift" else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=ARTIFACT_DIR / "drift_report_latest.json"
    )
    arguments = parser.parse_args()
    raise SystemExit(main(arguments.input, arguments.output))
