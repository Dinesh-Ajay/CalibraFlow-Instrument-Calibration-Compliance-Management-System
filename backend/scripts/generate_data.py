import os
import sys
import argparse
import random
import csv
import json
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker
from app.utils.id_generator import (
    generate_asset_code,
    generate_calibration_code,
    generate_certificate_code,
    generate_work_order_code,
    generate_usage_code,
    generate_supplier_code,
    generate_plan_code,
    generate_alert_code,
    generate_audit_code,
    generate_corrective_action_code,
    generate_impact_assessment_code,
    generate_extension_code,
)


def run_generator(seed: int = 20261022, scale: str = "starter", output_dir: str = "../data"):
    print(f"=== CalibraFlow Synthetic Data Generator ===")
    print(f"Seed: {seed} | Scale: {scale} | Output Directory: {output_dir}")

    rnd = random.Random(seed)
    Faker.seed(seed)
    fake = Faker()

    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "synthetic")
    os.makedirs(csv_dir, exist_ok=True)

    if scale == "starter":
        num_assets = 20
        num_cal_events = 50
        num_uses = 100
        num_suppliers = 5
    elif scale == "medium":
        num_assets = 100
        num_cal_events = 250
        num_uses = 500
        num_suppliers = 10
    else:  # full
        num_assets = 2000
        num_cal_events = 5000
        num_uses = 100000
        num_suppliers = 20

    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    current_sim_time = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)

    ground_truth_records = []

    # 1. INSTRUMENT TYPES
    print("[1/13] Generating Instrument Types...")
    instrument_types = [
        {"id": 1, "type_code": "PRESSURE", "type_name": "Pressure Gauge / Transmitter", "measurement_unit": "bar", "default_calibration_interval_days": 90, "default_tolerance": 2.0},
        {"id": 2, "type_code": "TEMPERATURE", "type_name": "Temperature Sensor / RTD", "measurement_unit": "°C", "default_calibration_interval_days": 180, "default_tolerance": 1.5},
        {"id": 3, "type_code": "WEIGHT", "type_name": "Industrial Scale / Load Cell", "measurement_unit": "kg", "default_calibration_interval_days": 90, "default_tolerance": 0.5},
        {"id": 4, "type_code": "FLOW", "type_name": "Flow Meter", "measurement_unit": "L/min", "default_calibration_interval_days": 180, "default_tolerance": 2.5},
        {"id": 5, "type_code": "VOLTAGE", "type_name": "Digital Multimeter / Voltmeter", "measurement_unit": "V", "default_calibration_interval_days": 365, "default_tolerance": 1.0},
        {"id": 6, "type_code": "CURRENT", "type_name": "Current Clamp / Ammeter", "measurement_unit": "A", "default_calibration_interval_days": 365, "default_tolerance": 1.0},
        {"id": 7, "type_code": "HUMIDITY", "type_name": "Hygrometer Sensor", "measurement_unit": "%RH", "default_calibration_interval_days": 180, "default_tolerance": 3.0},
    ]

    # 2. SUPPLIERS
    print("[2/13] Generating Calibration Suppliers...")
    suppliers = []
    for i in range(1, num_suppliers + 1):
        s_code = generate_supplier_code(i)
        suppliers.append({
            "id": i,
            "supplier_code": s_code,
            "supplier_name": f"{fake.company()} Calibration Services",
            "contact_email": f"service@{s_code.lower()}.com",
            "contact_phone": f"+1-800-{rnd.randint(100, 999)}-{rnd.randint(1000, 9999)}",
            "address": fake.address().replace("\n", ", "),
            "accreditation_reference": f"ISO-17025-ACC-{2024 + (i % 3)}-{i:03d}",
            "status": "ACTIVE",
            "created_at": base_time.isoformat()
        })

    # 3. ASSETS & 4. CALIBRATION PLANS
    print(f"[3/13 & 4/13] Generating {num_assets} Assets and Calibration Plans...")
    production_lines = ["Line 1 - Bottling", "Line 2 - Packaging", "Line 3 - Synthesis", "Line 4 - Quality Lab", "Line 5 - Assembly"]
    locations = ["Building A - Sector 1", "Building A - Sector 2", "Building B - Cleanroom", "Building C - Heavy Fab", "Testing Bay 4"]
    manufacturers = ["Yokogawa", "Endress+Hauser", "WIKA", "Fluke", "Mettler Toledo", "Emerson", "ABB"]

    assets = []
    calibration_plans = []

    for i in range(1, num_assets + 1):
        asset_code = generate_asset_code(i)
        itype = rnd.choice(instrument_types)
        install_date = base_time + timedelta(days=rnd.randint(1, 60))
        commission_date = install_date + timedelta(days=rnd.randint(2, 10))

        interval_days = itype["default_calibration_interval_days"]
        tolerance = itype["default_tolerance"]

        # Anomaly Scenario 1 Injection (Calibration Due Date Inconsistency):
        # We will inject Scenario 1 specifically in Asset 5 (or if scale starter, Asset 5)
        is_scenario_1 = (i == 5)

        # Baseline dates
        last_cal_date = commission_date + timedelta(days=rnd.randint(10, 80))
        if is_scenario_1:
            # Deliberate inconsistency: due date does NOT match last_cal + interval
            next_due_date = last_cal_date + timedelta(days=interval_days + 45)
            ground_truth_records.append({
                "record_id": asset_code,
                "entity_type": "Asset",
                "issue_type": "DUE_DATE_MISMATCH",
                "expected_decision": "FLAG",
                "expected_status": "INCONSISTENT",
                "expected_action": "RECALCULATE_DUE_DATE",
                "explanation": f"Calculated next due date ({next_due_date.date()}) does not match plan formula last_calibration_date + {interval_days} days ({ (last_cal_date + timedelta(days=interval_days)).date() })."
            })
        else:
            next_due_date = last_cal_date + timedelta(days=interval_days)

        # Some assets overdue, some upcoming, some compliant
        if i % 7 == 0:
            # Make definitely overdue
            next_due_date = current_sim_time - timedelta(days=rnd.randint(5, 30))
            cal_status = "OVERDUE"
        elif i % 5 == 0:
            # Upcoming
            next_due_date = current_sim_time + timedelta(days=rnd.randint(2, 12))
            cal_status = "UPCOMING"
        elif i == 8:
            # FAILED calibration state
            cal_status = "FAILED"
        else:
            cal_status = "COMPLIANT"

        op_status = "RESTRICTED" if cal_status == "FAILED" else "ACTIVE"

        assets.append({
            "id": i,
            "asset_code": asset_code,
            "asset_name": f"{itype['type_name']} - {fake.word().capitalize()}",
            "instrument_type_id": itype["id"],
            "serial_number": f"SN-{rnd.randint(100000, 999999)}",
            "manufacturer": rnd.choice(manufacturers),
            "model_number": f"MOD-{rnd.randint(10, 99)}X",
            "plant_location": rnd.choice(locations),
            "production_line": rnd.choice(production_lines),
            "installation_date": install_date.isoformat(),
            "commissioning_date": commission_date.isoformat(),
            "calibration_interval_days": interval_days,
            "last_calibration_date": last_cal_date.isoformat(),
            "next_due_date": next_due_date.isoformat(),
            "operational_status": op_status,
            "calibration_status": cal_status,
            "requires_calibration": True,
            "requires_certificate": True,
            "created_at": install_date.isoformat(),
            "updated_at": current_sim_time.isoformat()
        })

        plan_code = generate_plan_code(i)
        calibration_plans.append({
            "id": i,
            "plan_code": plan_code,
            "asset_id": i,
            "instrument_type_id": itype["id"],
            "calibration_interval_days": interval_days,
            "tolerance": tolerance,
            "effective_from": install_date.isoformat(),
            "effective_until": None,
            "due_date_calculation_method": "CALENDAR_DAYS",
            "grace_period_days": 0,
            "certificate_required": True,
            "emergency_extension_allowed": True,
            "status": "ACTIVE",
            "created_at": install_date.isoformat(),
            "updated_at": install_date.isoformat()
        })

    # 5. CALIBRATION EVENTS & 6. CERTIFICATES
    print(f"[5/13 & 6/13] Generating {num_cal_events} Calibration Events and Certificates...")
    calibration_events = []
    certificates = []
    corrective_actions = []
    impact_assessments = []

    cert_counter = 1
    capa_counter = 1
    ia_counter = 1

    for i in range(1, num_cal_events + 1):
        asset_idx = (i - 1) % len(assets)
        target_asset = assets[asset_idx]
        cal_code = generate_calibration_code(target_asset["asset_code"], i, 2026)
        cal_plan = calibration_plans[asset_idx]

        cal_date = base_time + timedelta(days=rnd.randint(60, 280))
        ref_val = round(rnd.uniform(10.0, 100.0), 2)
        tol = cal_plan["tolerance"]

        # Anomaly Scenario 4: Failed calibration without impact assessment
        is_scenario_4 = (i == 4)

        # Decide pass/fail
        if is_scenario_4 or (i % 12 == 0):
            # Failed calibration: error > tol
            result = "FAIL"
            meas_val = round(ref_val * (1.0 + (tol + rnd.uniform(0.5, 3.0)) / 100.0), 2)
            error_val = round(abs(meas_val - ref_val) / ref_val * 100.0, 4)
            calc_next_due = target_asset["next_due_date"]
        else:
            result = "PASS"
            meas_val = round(ref_val * (1.0 + rnd.uniform(-tol * 0.7, tol * 0.7) / 100.0), 2)
            error_val = round(abs(meas_val - ref_val) / ref_val * 100.0, 4)
            calc_next_due = (cal_date + timedelta(days=cal_plan["calibration_interval_days"])).isoformat()

        cal_event = {
            "id": i,
            "calibration_code": cal_code,
            "asset_id": target_asset["id"],
            "calibration_plan_id": cal_plan["id"],
            "supplier_id": rnd.randint(1, len(suppliers)),
            "work_order_id": None,
            "calibration_date": cal_date.isoformat(),
            "previous_due_date": target_asset["last_calibration_date"],
            "calculated_next_due_date": calc_next_due,
            "measured_value": meas_val,
            "reference_value": ref_val,
            "measurement_error": error_val,
            "tolerance": tol,
            "result": result,
            "calibration_status": "COMPLETED",
            "performed_by": fake.name(),
            "reviewed_by": "Quality Reviewer",
            "certificate_required": True,
            "notes": f"Scheduled periodic verification. Tolerance: {tol}%",
            "created_at": cal_date.isoformat()
        }
        calibration_events.append(cal_event)

        # Manage certificates for passed calibrations
        if result == "PASS":
            cert_code = generate_certificate_code(cal_code)

            # Anomaly Scenario 3: Certificate Refers to Another Asset
            is_scenario_3 = (i == 3)
            if is_scenario_3:
                # Deliberate mismatch: certificate points to Asset ID 2 while calibration event is for Asset ID target_asset["id"]
                mismatched_asset_id = 2 if target_asset["id"] != 2 else 1
                certificates.append({
                    "id": cert_counter,
                    "certificate_code": cert_code,
                    "calibration_event_id": i,
                    "asset_id": mismatched_asset_id,
                    "supplier_id": cal_event["supplier_id"],
                    "certificate_number": f"CERT-ISO-{2026}-{cert_counter:05d}",
                    "file_path": None,
                    "issue_date": cal_date.isoformat(),
                    "expiry_date": (cal_date + timedelta(days=cal_plan["calibration_interval_days"])).isoformat(),
                    "verification_status": "INVALID",
                    "verified_by": None,
                    "verified_at": None,
                    "created_at": cal_date.isoformat()
                })
                ground_truth_records.append({
                    "record_id": cert_code,
                    "entity_type": "Certificate",
                    "issue_type": "ASSET_MISMATCH",
                    "expected_decision": "INVALID",
                    "expected_status": "INVALID",
                    "expected_action": "REJECT_AND_ALERT",
                    "explanation": f"Certificate asset_id ({mismatched_asset_id}) does not match calibration event asset_id ({target_asset['id']})."
                })
            else:
                certificates.append({
                    "id": cert_counter,
                    "certificate_code": cert_code,
                    "calibration_event_id": i,
                    "asset_id": target_asset["id"],
                    "supplier_id": cal_event["supplier_id"],
                    "certificate_number": f"CERT-ISO-{2026}-{cert_counter:05d}",
                    "file_path": None,
                    "issue_date": cal_date.isoformat(),
                    "expiry_date": (cal_date + timedelta(days=cal_plan["calibration_interval_days"])).isoformat(),
                    "verification_status": "VERIFIED" if rnd.random() > 0.15 else "PENDING",
                    "verified_by": "Quality Lead" if rnd.random() > 0.15 else None,
                    "verified_at": (cal_date + timedelta(days=1)).isoformat() if rnd.random() > 0.15 else None,
                    "created_at": cal_date.isoformat()
                })
            cert_counter += 1

        elif result == "FAIL":
            # For fail: create CAPA
            capa_code = generate_corrective_action_code(capa_counter)
            corrective_actions.append({
                "id": capa_counter,
                "corrective_action_code": capa_code,
                "calibration_event_id": i,
                "asset_id": target_asset["id"],
                "description": f"Measurement error {error_val}% exceeded tolerance {tol}%. Instrument quarantined.",
                "assigned_to": 1,
                "root_cause": "Component drift over operating temperature range.",
                "action_taken": "Replaced sensor module and scheduled recalibration.",
                "status": "OPEN" if is_scenario_4 or rnd.random() > 0.5 else "RESOLVED",
                "opened_at": cal_date.isoformat(),
                "closed_at": (cal_date + timedelta(days=5)).isoformat() if not is_scenario_4 and rnd.random() <= 0.5 else None
            })
            capa_counter += 1

            if is_scenario_4:
                # Omit impact assessment deliberately for Scenario 4!
                ground_truth_records.append({
                    "record_id": cal_code,
                    "entity_type": "CalibrationEvent",
                    "issue_type": "MISSING_IMPACT_ASSESSMENT",
                    "expected_decision": "NON_COMPLIANT",
                    "expected_status": "FLAGGED",
                    "expected_action": "CREATE_IMPACT_ASSESSMENT",
                    "explanation": f"Failed calibration event {cal_code} has no linked impact assessment record."
                })
            else:
                # Create Impact Assessment
                ia_code = generate_impact_assessment_code(ia_counter)
                impact_assessments.append({
                    "id": ia_counter,
                    "assessment_code": ia_code,
                    "calibration_event_id": i,
                    "asset_id": target_asset["id"],
                    "affected_production_start": (cal_date - timedelta(days=30)).isoformat(),
                    "affected_production_end": cal_date.isoformat(),
                    "affected_usage_count": rnd.randint(5, 35),
                    "risk_level": "HIGH" if error_val > tol * 1.5 else "MEDIUM",
                    "assessment_notes": "Assessed product batches manufactured within tolerance window; QA risk disposition acceptable.",
                    "assessed_by": 1,
                    "status": "COMPLETED" if rnd.random() > 0.4 else "PENDING",
                    "created_at": cal_date.isoformat()
                })
                ia_counter += 1

    # 7. WORK ORDERS
    print("[7/13] Generating Work Orders...")
    work_orders = []
    wo_types = ["CALIBRATION", "MAINTENANCE", "CORRECTIVE"]
    wo_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    wo_statuses = ["COMPLETED", "IN_PROGRESS", "ASSIGNED", "OPEN"]

    num_wos = min(max(num_assets * 2, 30), 1000)
    for i in range(1, num_wos + 1):
        target_asset = assets[rnd.randint(0, len(assets) - 1)]
        wo_code = generate_work_order_code(i, 2026)
        wo_status = rnd.choice(wo_statuses)
        sched_date = base_time + timedelta(days=rnd.randint(10, 310))
        downtime = rnd.randint(30, 240) if wo_status == "COMPLETED" else 0

        work_orders.append({
            "id": i,
            "work_order_code": wo_code,
            "asset_id": target_asset["id"],
            "calibration_plan_id": target_asset["id"],
            "assigned_to": 1,
            "priority": rnd.choice(wo_priorities),
            "work_order_type": rnd.choice(wo_types),
            "description": f"Scheduled service & calibration routine for {target_asset['asset_code']}",
            "scheduled_date": sched_date.isoformat(),
            "start_time": sched_date.isoformat() if wo_status in ["IN_PROGRESS", "COMPLETED"] else None,
            "completion_time": (sched_date + timedelta(minutes=downtime)).isoformat() if wo_status == "COMPLETED" else None,
            "downtime_minutes": downtime,
            "status": wo_status,
            "created_at": (sched_date - timedelta(days=2)).isoformat(),
            "updated_at": sched_date.isoformat()
        })

    # 8. EMERGENCY EXTENSIONS
    print("[8/13] Generating Emergency Extensions...")
    emergency_extensions = [
        {
            "id": 1,
            "extension_code": generate_extension_code(1),
            "asset_id": 7,  # Will be used in Scenario 5 demo
            "original_due_date": (current_sim_time - timedelta(days=3)).isoformat(),
            "extended_due_date": (current_sim_time + timedelta(days=15)).isoformat(),
            "reason": "Critical production run for urgent export batch; supplier calibration delayed by blizzard.",
            "requested_by": 1,
            "approved_by": 1,
            "approval_status": "APPROVED",
            "approved_at": (current_sim_time - timedelta(days=2)).isoformat(),
            "created_at": (current_sim_time - timedelta(days=2)).isoformat()
        },
        {
            "id": 2,
            "extension_code": generate_extension_code(2),
            "asset_id": 10,
            "original_due_date": (current_sim_time - timedelta(days=1)).isoformat(),
            "extended_due_date": (current_sim_time + timedelta(days=7)).isoformat(),
            "reason": "Awaiting replacement probe delivery.",
            "requested_by": 1,
            "approved_by": None,
            "approval_status": "PENDING",
            "approved_at": None,
            "created_at": (current_sim_time - timedelta(hours=12)).isoformat()
        }
    ]

    # 9. PRODUCTION USES
    print(f"[9/13] Generating {num_uses} Production Usage Attempts...")
    production_uses = []
    alerts = []
    alert_counter = 1

    for i in range(1, num_uses + 1):
        target_asset = assets[rnd.randint(0, len(assets) - 1)]
        u_time = base_time + timedelta(days=rnd.randint(30, 310), hours=rnd.randint(0, 23), minutes=rnd.randint(0, 59))
        due_dt = datetime.fromisoformat(target_asset["next_due_date"])

        # Anomaly Scenario 2: Expired Instrument Used Without Exception
        is_scenario_2 = (i == 2)

        if is_scenario_2:
            # Explicitly force usage timestamp AFTER calibration validity period without extension
            target_asset = assets[6]  # pick asset 7
            expired_usage_time = datetime.fromisoformat(target_asset["next_due_date"]) + timedelta(days=12)
            u_code = generate_usage_code(target_asset["asset_code"], expired_usage_time, seq=i)

            production_uses.append({
                "id": i,
                "usage_code": u_code,
                "asset_id": target_asset["id"],
                "production_line": target_asset["production_line"],
                "operator_id": 1,
                "usage_timestamp": expired_usage_time.isoformat(),
                "usage_end_timestamp": (expired_usage_time + timedelta(hours=2)).isoformat(),
                "usage_status": "BLOCKED",
                "validation_decision": "BLOCKED",
                "decision_reason": f"Calibration expired on {due_dt.date()}. No approved emergency extension exists.",
                "calibration_event_id": None,
                "exception_id": None,
                "created_at": expired_usage_time.isoformat()
            })

            ground_truth_records.append({
                "record_id": u_code,
                "entity_type": "ProductionUse",
                "issue_type": "EXPIRED_USAGE",
                "expected_decision": "BLOCKED",
                "expected_status": "BLOCKED",
                "expected_action": "BLOCK_AND_ALERT",
                "explanation": f"Production usage recorded on {expired_usage_time.date()} after calibration due date {due_dt.date()} without approved extension."
            })

            # Create PROHIBITED_USAGE Alert
            alerts.append({
                "id": alert_counter,
                "alert_code": generate_alert_code(alert_counter),
                "asset_id": target_asset["id"],
                "related_calibration_id": None,
                "related_work_order_id": None,
                "alert_type": "PROHIBITED_USAGE",
                "severity": "HIGH",
                "message": f"UNAUTHORIZED USAGE: Operator attempted to use {target_asset['asset_code']} while calibration overdue.",
                "status": "OPEN",
                "generated_at": expired_usage_time.isoformat(),
                "acknowledged_by": None,
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_counter += 1

        else:
            # Normal usage evaluation
            if target_asset["operational_status"] == "RESTRICTED" or target_asset["calibration_status"] == "FAILED":
                decision = "BLOCKED"
                reason = "Asset is in RESTRICTED status due to failed calibration."
            elif u_time > due_dt:
                if target_asset["id"] == 7 and emergency_extensions[0]["approval_status"] == "APPROVED":
                    decision = "ALLOWED_WITH_EXCEPTION"
                    reason = f"Approved emergency extension EXT-000001 active until {emergency_extensions[0]['extended_due_date'][:10]}."
                else:
                    decision = "BLOCKED"
                    reason = f"Instrument calibration expired on {due_dt.date()}."
            else:
                decision = "ALLOWED"
                reason = "Instrument is within valid calibration period and compliant."

            u_code = generate_usage_code(target_asset["asset_code"], u_time, seq=i)
            production_uses.append({
                "id": i,
                "usage_code": u_code,
                "asset_id": target_asset["id"],
                "production_line": target_asset["production_line"],
                "operator_id": 1,
                "usage_timestamp": u_time.isoformat(),
                "usage_end_timestamp": (u_time + timedelta(hours=3)).isoformat(),
                "usage_status": "RECORDED" if decision != "BLOCKED" else "INTERRUPTED",
                "validation_decision": decision,
                "decision_reason": reason,
                "calibration_event_id": None,
                "exception_id": 1 if decision == "ALLOWED_WITH_EXCEPTION" else None,
                "created_at": u_time.isoformat()
            })

            if decision == "BLOCKED" and rnd.random() < 0.2:
                alerts.append({
                    "id": alert_counter,
                    "alert_code": generate_alert_code(alert_counter),
                    "asset_id": target_asset["id"],
                    "related_calibration_id": None,
                    "related_work_order_id": None,
                    "alert_type": "PROHIBITED_USAGE",
                    "severity": "HIGH",
                    "message": f"Attempted use of restricted instrument {target_asset['asset_code']} on line {target_asset['production_line']}.",
                    "status": "OPEN",
                    "generated_at": u_time.isoformat(),
                    "acknowledged_by": None,
                    "acknowledged_at": None,
                    "resolved_at": None
                })
                alert_counter += 1

    # 10. SYSTEM ALERTS
    print("[10/13] Generating System Alerts...")
    # Add upcoming and overdue alerts for assets
    for a in assets:
        if a["calibration_status"] == "OVERDUE":
            alerts.append({
                "id": alert_counter,
                "alert_code": generate_alert_code(alert_counter),
                "asset_id": a["id"],
                "related_calibration_id": None,
                "related_work_order_id": None,
                "alert_type": "OVERDUE_CALIBRATION",
                "severity": "HIGH",
                "message": f"Instrument {a['asset_code']} calibration is overdue since {a['next_due_date'][:10]}.",
                "status": "OPEN",
                "generated_at": current_sim_time.isoformat(),
                "acknowledged_by": None,
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_counter += 1
        elif a["calibration_status"] == "UPCOMING":
            alerts.append({
                "id": alert_counter,
                "alert_code": generate_alert_code(alert_counter),
                "asset_id": a["id"],
                "related_calibration_id": None,
                "related_work_order_id": None,
                "alert_type": "UPCOMING_CALIBRATION",
                "severity": "MEDIUM",
                "message": f"Instrument {a['asset_code']} calibration due on {a['next_due_date'][:10]}.",
                "status": "OPEN",
                "generated_at": current_sim_time.isoformat(),
                "acknowledged_by": None,
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_counter += 1

    # 11. AUDIT RECORDS
    print("[11/13] Generating Audit Records...")
    audit_records = []
    aud_counter = 1
    for a in assets:
        audit_records.append({
            "id": aud_counter,
            "record_code": generate_audit_code(aud_counter),
            "actor_id": 1,
            "entity_type": "Asset",
            "entity_id": a["asset_code"],
            "action": "CREATE",
            "previous_value": None,
            "new_value": json.dumps({"asset_code": a["asset_code"], "status": a["operational_status"]}),
            "reason": "Initial asset registration",
            "timestamp": a["installation_date"],
            "request_id": f"REQ-{aud_counter:06d}"
        })
        aud_counter += 1

    # Write CSV Files
    print("[12/13] Writing Synthetic CSV Files...")
    tables = [
        ("instrument_types.csv", instrument_types),
        ("suppliers.csv", suppliers),
        ("assets.csv", assets),
        ("calibration_plans.csv", calibration_plans),
        ("calibration_events.csv", calibration_events),
        ("certificates.csv", certificates),
        ("work_orders.csv", work_orders),
        ("emergency_extensions.csv", emergency_extensions),
        ("production_uses.csv", production_uses),
        ("alerts.csv", alerts),
        ("corrective_actions.csv", corrective_actions),
        ("impact_assessments.csv", impact_assessments),
        ("audit_records.csv", audit_records)
    ]

    for fname, data_list in tables:
        path = os.path.join(csv_dir, fname)
        if not data_list:
            continue
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data_list[0].keys()))
            writer.writeheader()
            writer.writerows(data_list)
        print(f"  [OK] {fname}: {len(data_list)} rows")

    # Write Ground Truth
    print("[13/13] Writing Ground Truth Dataset (Separated)...")
    gt_path = os.path.join(output_dir, "ground_truth.csv")
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["record_id", "entity_type", "issue_type", "expected_decision", "expected_status", "expected_action", "explanation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ground_truth_records)
    print(f"  [OK] ground_truth.csv: {len(ground_truth_records)} labelled anomalies documented.")

    summary = {
        "seed": seed,
        "scale": scale,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "instrument_types": len(instrument_types),
            "suppliers": len(suppliers),
            "assets": len(assets),
            "calibration_plans": len(calibration_plans),
            "calibration_events": len(calibration_events),
            "certificates": len(certificates),
            "work_orders": len(work_orders),
            "emergency_extensions": len(emergency_extensions),
            "production_uses": len(production_uses),
            "alerts": len(alerts),
            "corrective_actions": len(corrective_actions),
            "impact_assessments": len(impact_assessments),
            "audit_records": len(audit_records),
            "ground_truth_anomalies": len(ground_truth_records)
        }
    }
    summary_path = os.path.join(output_dir, "generation_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nGeneration completed successfully!")
    print(f"Summary written to: {summary_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CalibraFlow Synthetic Data Generator")
    parser.add_argument("--seed", type=int, default=20261022, help="Random seed (default: 20261022)")
    parser.add_argument("--scale", type=str, choices=["starter", "medium", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--output-dir", type=str, default="../data", help="Output directory for generated files")
    args = parser.parse_args()

    run_generator(seed=args.seed, scale=args.scale, output_dir=args.output_dir)
