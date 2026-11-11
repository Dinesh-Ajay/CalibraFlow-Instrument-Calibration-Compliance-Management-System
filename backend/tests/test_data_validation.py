import os
from scripts.validate_data import validate_dataset


def test_data_validation_engine_on_synthetic_data():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(repo_root, "data")
    report = validate_dataset(data_dir)
    assert report["validation_passed"] is True
    assert report["foreign_key_violations"] == 0
    assert report["intentional_ground_truth_matches"] == 4
    assert report["detected_anomalies_count"] >= 4
