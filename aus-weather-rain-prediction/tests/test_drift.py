import pandas as pd

from aus_weather.drift import build_reference_profile, compare_to_reference


def test_reference_distribution_is_stable_against_itself():
    frame = pd.DataFrame(
        {
            "temperature": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "season": ["Winter"] * 5 + ["Spring"] * 5,
        }
    )
    profile = build_reference_profile(frame, ["temperature"], ["season"])
    report = compare_to_reference(frame, profile)

    assert report["status"] == "stable"
    assert report["max_psi"] < 0.01


def test_large_distribution_shift_is_flagged():
    reference = pd.DataFrame(
        {"temperature": range(10), "season": ["Winter"] * 10}
    )
    current = pd.DataFrame(
        {"temperature": range(100, 110), "season": ["Summer"] * 10}
    )
    profile = build_reference_profile(reference, ["temperature"], ["season"])
    report = compare_to_reference(current, profile)

    assert report["status"] == "drift"
    assert set(report["drifted_features"]) == {"temperature", "season"}
