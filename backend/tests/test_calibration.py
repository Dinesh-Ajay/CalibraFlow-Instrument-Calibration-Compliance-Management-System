from datetime import datetime, timezone, timedelta
from app.services.calibration_service import compute_measurement_error


def test_measurement_error_formula():
    # Percentage error formula
    err_pct, mode = compute_measurement_error(102.0, 100.0)
    assert round(err_pct, 2) == 2.0
    assert mode == "PERCENTAGE"

    # Zero reference value absolute error formula
    err_zero, mode_zero = compute_measurement_error(0.05, 0.0)
    assert round(err_zero, 2) == 0.05
    assert mode_zero == "ABSOLUTE"


def test_successful_calibration_execution(client, engineer_token):
    # Get created asset
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id = assets_res.json()[0]["id"]

    res = client.post(
        "/api/v1/calibration/events",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_id": asset_id,
            "measured_value": 100.8,
            "reference_value": 100.0,
            "tolerance": 2.0,
            "performed_by": "Senior Metrologist",
            "certificate_required": True,
            "notes": "Annual precision calibration"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "PASS"
    assert round(data["measurement_error"], 2) == 0.8
    assert data["calibration_code"].startswith("CAL-")


def test_failed_calibration_execution(client, engineer_token):
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id = assets_res.json()[0]["id"]

    # Measured error = (105.0 - 100.0) / 100 * 100 = 5.0% > 2.0% tolerance
    res = client.post(
        "/api/v1/calibration/events",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_id": asset_id,
            "measured_value": 105.0,
            "reference_value": 100.0,
            "tolerance": 2.0,
            "performed_by": "Maintenance Tech",
            "certificate_required": True,
            "notes": "Failed verification test"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "FAIL"

    # Verify asset is restricted
    asset_check = client.get(f"/api/v1/assets/{asset_id}", headers={"Authorization": f"Bearer {engineer_token}"})
    assert asset_check.json()["operational_status"] == "RESTRICTED"
    assert asset_check.json()["calibration_status"] == "FAILED"
