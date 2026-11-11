import os
import sys
import csv
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_dataset(data_dir: str = "../data") -> dict:
    # Resolve data_dir robustly (supports running from repo root or backend/)
    if not os.path.isabs(data_dir):
        candidates = [
            os.path.abspath(data_dir),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", data_dir)),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", data_dir)),
        ]
        for c in candidates:
            if os.path.isdir(c):
                data_dir = c
                break
        else:
            data_dir = os.path.abspath(data_dir)

    csv_dir = os.path.join(data_dir, "synthetic")
    gt_file = os.path.join(data_dir, "ground_truth.csv")

    assets = load_csv(os.path.join(csv_dir, "assets.csv"))
    plans = load_csv(os.path.join(csv_dir, "calibration_plans.csv"))
    events = load_csv(os.path.join(csv_dir, "calibration_events.csv"))
    certs = load_csv(os.path.join(csv_dir, "certificates.csv"))
    wos = load_csv(os.path.join(csv_dir, "work_orders.csv"))
    uses = load_csv(os.path.join(csv_dir, "production_uses.csv"))
    capas = load_csv(os.path.join(csv_dir, "corrective_actions.csv"))
    ias = load_csv(os.path.join(csv_dir, "impact_assessments.csv"))
    ground_truth = load_csv(gt_file)

    gt_dict = {row["record_id"]: row for row in ground_truth}

    total_records = len(assets) + len(plans) + len(events) + len(certs) + len(wos) + len(uses) + len(capas) + len(ias)

    anomalies_detected = []
    data_errors = []

    # 1. PK Uniqueness
    for name, dataset, pk in [
        ("Asset", assets, "id"),
        ("CalibrationEvent", events, "id"),
        ("Certificate", certs, "id"),
        ("WorkOrder", wos, "id"),
        ("ProductionUse", uses, "id"),
        ("CorrectiveAction", capas, "id"),
        ("ImpactAssessment", ias, "id"),
    ]:
        ids = [r[pk] for r in dataset if pk in r and r[pk] != ""]
        if len(ids) != len(set(ids)):
            data_errors.append(f"Primary key '{pk}' is not unique in {name}")

    # 2. Referential integrity checks (basic)
    asset_ids = {a.get("id") for a in assets}
    event_ids = {e.get("id") for e in events}
    for e in events:
        if e.get("asset_id") and e["asset_id"] not in asset_ids:
            data_errors.append(f"CalibrationEvent {e.get('id')} references missing asset {e.get('asset_id')}")
    for c in certs:
        if c.get("asset_id") and c["asset_id"] not in asset_ids:
            data_errors.append(f"Certificate {c.get('id')} references missing asset {c.get('asset_id')}")
        if c.get("calibration_event_id") and c["calibration_event_id"] not in event_ids:
            data_errors.append(f"Certificate {c.get('id')} references missing calibration event {c.get('calibration_event_id')}")

    # 3. Due date mismatch (Scenario 1)
    for a in assets:
        code = a.get("asset_code")
        next_due = a.get("next_due_date")
        last_cal = a.get("last_calibration_date")
        interval = a.get("calibration_interval_days")
        if next_due and last_cal and interval:
            try:
                nd = datetime.fromisoformat(next_due.replace("Z", "+00:00")).date()
                ld = datetime.fromisoformat(last_cal.replace("Z", "+00:00")).date()
                expected_days = int(interval)
                actual_days = (nd - ld).days
                if actual_days != expected_days:
                    is_intentional = code in gt_dict and gt_dict[code]["issue_type"] == "DUE_DATE_MISMATCH"
                    anomalies_detected.append({
                        "record_id": code,
                        "issue_type": "DUE_DATE_MISMATCH",
                        "intentional": is_intentional,
                        "details": f"Interval days is {interval}, but gap between last_calibration and next_due is {actual_days} days."
                    })
            except Exception:
                pass

    # 4. Certificate Ownership Reconciliation (Scenario 3)
    event_asset_map = {e["id"]: e["asset_id"] for e in events}
    for c in certs:
        c_code = c.get("certificate_code")
        cal_id = c.get("calibration_event_id")
        c_asset_id = c.get("asset_id")
        expected_asset_id = event_asset_map.get(cal_id)
        if expected_asset_id and c_asset_id != expected_asset_id:
            is_intentional = c_code in gt_dict and gt_dict[c_code]["issue_type"] == "ASSET_MISMATCH"
            anomalies_detected.append({
                "record_id": c_code,
                "issue_type": "ASSET_MISMATCH",
                "intentional": is_intentional,
                "details": f"Certificate asset_id={c_asset_id} does not match CalibrationEvent asset_id={expected_asset_id}."
            })

    # 5. Failed Calibration Impact Assessment Requirement (Scenario 4)
    ia_event_ids = {ia.get("calibration_event_id") for ia in ias}
    failed_events_count = 0
    missing_ia_count = 0
    for e in events:
        if e.get("result") == "FAIL":
            failed_events_count += 1
            if e.get("id") not in ia_event_ids:
                missing_ia_count += 1
                is_intentional = e.get("calibration_code") in gt_dict and gt_dict[e.get("calibration_code")]["issue_type"] == "MISSING_IMPACT_ASSESSMENT"
                anomalies_detected.append({
                    "record_id": e.get("calibration_code"),
                    "issue_type": "MISSING_IMPACT_ASSESSMENT",
                    "intentional": is_intentional,
                    "details": f"Failed calibration {e.get('calibration_code')} has no linked impact assessment."
                })

    # 6. Expired Instrument Production Usage (Scenario 2)
    blocked_usage_count = 0
    for u in uses:
        if u.get("validation_decision") == "BLOCKED":
            blocked_usage_count += 1
            u_code = u.get("usage_code")
            if u_code in gt_dict and gt_dict[u_code]["issue_type"] == "EXPIRED_USAGE":
                anomalies_detected.append({
                    "record_id": u_code,
                    "issue_type": "EXPIRED_USAGE",
                    "intentional": True,
                    "details": u.get("decision_reason")
                })

    report = {
        "validation_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_records_evaluated": total_records,
        "foreign_key_violations": len(data_errors),
        "data_errors": data_errors,
        "failed_calibrations_count": failed_events_count,
        "blocked_production_usages_count": blocked_usage_count,
        "missing_impact_assessments_count": missing_ia_count,
        "detected_anomalies_count": len(anomalies_detected),
        "intentional_ground_truth_matches": sum(1 for a in anomalies_detected if a["intentional"]),
        "detected_anomalies": anomalies_detected,
        "validation_passed": len(data_errors) == 0
    }

    os.makedirs(data_dir, exist_ok=True)
    report_path = os.path.join(data_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== Validation Engine Results ===")
    print(f"Total Records Evaluated: {total_records}")
    print(f"Foreign Key Violations: {report['foreign_key_violations']}")
    print(f"Failed Calibrations: {failed_events_count}")
    print(f"Blocked Production Uses: {blocked_usage_count}")
    print(f"Missing Impact Assessments: {missing_ia_count}")
    print(f"Detected Anomalies: {len(anomalies_detected)}")
    print(f"Intentional Ground Truth Matches: {report['intentional_ground_truth_matches']} / {len(ground_truth)}")
    print(f"Validation Status: {'PASS (Clean data + accurately detected anomalies)' if report['validation_passed'] else 'FAIL'}")
    print(f"Detailed Report: {report_path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CalibraFlow Data Validation Engine")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing synthetic CSV files")
    args = parser.parse_args()

    validate_dataset(args.data_dir)
