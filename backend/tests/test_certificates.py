from datetime import datetime, timezone, timedelta


def test_certificate_upload_and_verification(client, engineer_token, quality_token):
    # Retrieve asset and calibration events
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id = assets_res.json()[0]["id"]

    events_res = client.get(f"/api/v1/calibration/events?asset_id={asset_id}", headers={"Authorization": f"Bearer {engineer_token}"})
    cal_event_id = events_res.json()[0]["id"]

    issue_date = datetime.now(timezone.utc).isoformat()
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()

    # Upload certificate
    upload_res = client.post(
        "/api/v1/certificates/upload",
        headers={"Authorization": f"Bearer {engineer_token}"},
        data={
            "calibration_event_id": cal_event_id,
            "asset_id": asset_id,
            "certificate_number": "CERT-2026-TEST-999",
            "issue_date": issue_date,
            "expiry_date": expiry_date
        }
    )
    assert upload_res.status_code == 201
    cert_data = upload_res.json()
    assert cert_data["verification_status"] == "PENDING"

    # Quality Engineer verifies certificate
    verify_res = client.patch(
        f"/api/v1/certificates/{cert_data['id']}/verify",
        headers={"Authorization": f"Bearer {quality_token}"},
        json={"verification_status": "VERIFIED"}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "VERIFIED"


def test_certificate_cross_asset_mismatch_detected(client, engineer_token):
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id_1 = assets_res.json()[0]["id"]

    # Create second asset
    res_asset2 = client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_name": "Secondary Sensor",
            "instrument_type_id": 1,
            "serial_number": "SN-TEST-002",
            "manufacturer": "Yokogawa",
            "model_number": "EJA530E",
            "plant_location": "Building A",
            "production_line": "Line 2",
            "calibration_interval_days": 90,
            "requires_calibration": True,
            "requires_certificate": True
        }
    )
    asset_id_2 = res_asset2.json()["id"]

    # Cal event belongs to asset 1
    events_res = client.get(f"/api/v1/calibration/events?asset_id={asset_id_1}", headers={"Authorization": f"Bearer {engineer_token}"})
    cal_event_id = events_res.json()[0]["id"]

    # Deliberate anomaly: certificate provided with asset_id_2
    issue_date = datetime.now(timezone.utc).isoformat()
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()

    upload_res = client.post(
        "/api/v1/certificates/upload",
        headers={"Authorization": f"Bearer {engineer_token}"},
        data={
            "calibration_event_id": cal_event_id,
            "asset_id": asset_id_2,  # MISMATCH!
            "certificate_number": "CERT-MISMATCH-001",
            "issue_date": issue_date,
            "expiry_date": expiry_date
        }
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["verification_status"] == "INVALID"
