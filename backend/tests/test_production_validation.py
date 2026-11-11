from datetime import datetime, timezone, timedelta


def test_production_usage_allowed_when_compliant(client, engineer_token, operator_token):
    # Register compliant asset with future due date
    future_due = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
    last_cal = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    res = client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_name": "Valid Compliant Gauge",
            "instrument_type_id": 1,
            "serial_number": "SN-COMPLIANT-001",
            "manufacturer": "WIKA",
            "model_number": "PG23",
            "plant_location": "Building B",
            "production_line": "Line 1 - Bottling",
            "calibration_interval_days": 90,
            "requires_calibration": True,
            "requires_certificate": False,
            "last_calibration_date": last_cal
        }
    )
    asset_id = res.json()["id"]

    # Validate usage
    val_res = client.post(
        "/api/v1/production/validate-usage",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "asset_id": asset_id,
            "production_line": "Line 1 - Bottling"
        }
    )
    assert val_res.status_code == 200
    assert val_res.json()["decision"] == "ALLOWED"
    assert val_res.json()["is_allowed"] is True

    # Record production usage
    use_res = client.post(
        "/api/v1/production/usage",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "asset_id": asset_id,
            "production_line": "Line 1 - Bottling"
        }
    )
    assert use_res.status_code == 201
    assert use_res.json()["validation_decision"] == "ALLOWED"


def test_production_usage_blocked_when_overdue(client, engineer_token, operator_token):
    # Register overdue asset
    old_last_cal = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    res = client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_name": "Overdue Gauge",
            "instrument_type_id": 1,
            "serial_number": "SN-OVERDUE-001",
            "manufacturer": "WIKA",
            "model_number": "PG23",
            "plant_location": "Building B",
            "production_line": "Line 2 - Packaging",
            "calibration_interval_days": 90,
            "requires_calibration": True,
            "requires_certificate": False,
            "last_calibration_date": old_last_cal
        }
    )
    asset_id = res.json()["id"]

    # Attempt to record production usage: must be BLOCKED
    use_res = client.post(
        "/api/v1/production/usage",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "asset_id": asset_id,
            "production_line": "Line 2 - Packaging"
        }
    )
    assert use_res.status_code == 201
    assert use_res.json()["validation_decision"] == "BLOCKED"
    assert "expired" in use_res.json()["decision_reason"].lower()

    # Verify usage was persisted and alert generated
    alerts_res = client.get(f"/api/v1/alerts?asset_id={asset_id}", headers={"Authorization": f"Bearer {operator_token}"})
    assert alerts_res.status_code == 200
    alert_types = [a["alert_type"] for a in alerts_res.json()]
    assert "PROHIBITED_USAGE" in alert_types


def test_production_usage_allowed_with_emergency_extension(client, engineer_token, quality_token, operator_token):
    # Register overdue asset
    old_last_cal = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    res = client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_name": "Extension Candidate Gauge",
            "instrument_type_id": 1,
            "serial_number": "SN-EXT-001",
            "manufacturer": "WIKA",
            "model_number": "PG23",
            "plant_location": "Building B",
            "production_line": "Line 3 - Synthesis",
            "calibration_interval_days": 90,
            "requires_calibration": True,
            "requires_certificate": False,
            "last_calibration_date": old_last_cal
        }
    )
    asset_id = res.json()["id"]

    # Request emergency extension
    ext_due = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    ext_res = client.post(
        "/api/v1/emergency-extensions",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_id": asset_id,
            "extended_due_date": ext_due,
            "reason": "Emergency production order pending calibrator arrival"
        }
    )
    assert ext_res.status_code == 201
    ext_id = ext_res.json()["id"]

    # Approve emergency extension by Quality Engineer
    appr_res = client.patch(
        f"/api/v1/emergency-extensions/{ext_id}/approve",
        headers={"Authorization": f"Bearer {quality_token}"},
        json={"approved": True, "notes": "Approved for 14 days under QA observation"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "APPROVED"

    # Now attempt production usage: must be ALLOWED_WITH_EXCEPTION
    val_res = client.post(
        "/api/v1/production/validate-usage",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "asset_id": asset_id,
            "production_line": "Line 3 - Synthesis"
        }
    )
    assert val_res.status_code == 200
    assert val_res.json()["decision"] == "ALLOWED_WITH_EXCEPTION"
    assert val_res.json()["is_allowed"] is True
