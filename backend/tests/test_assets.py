from datetime import datetime, timezone, timedelta


def test_asset_creation_and_due_date_calculation(client, engineer_token):
    last_cal = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    res = client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_name": "Main Boiler Pressure Sensor",
            "instrument_type_id": 1,
            "serial_number": "SN-TEST-001",
            "manufacturer": "Yokogawa",
            "model_number": "EJA530E",
            "plant_location": "Building A - Sector 1",
            "production_line": "Line 1 - Bottling",
            "calibration_interval_days": 90,
            "requires_calibration": True,
            "requires_certificate": True,
            "last_calibration_date": last_cal
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["asset_code"].startswith("AST-")
    assert data["calibration_status"] == "COMPLIANT"
    assert data["next_due_date"] is not None

    # Verify due date is exactly last_cal + 90 days
    last_dt = datetime.fromisoformat(data["last_calibration_date"])
    next_dt = datetime.fromisoformat(data["next_due_date"])
    assert (next_dt - last_dt).days == 90


def test_asset_retrieval(client, operator_token):
    res = client.get(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0
