from datetime import datetime, timezone, timedelta


def test_work_order_lifecycle(client, engineer_token):
    # Get asset
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id = assets_res.json()[0]["id"]

    sched_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_res = client.post(
        "/api/v1/work-orders",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_id": asset_id,
            "priority": "HIGH",
            "work_order_type": "CALIBRATION",
            "description": "Routine calibration work order",
            "scheduled_date": sched_date
        }
    )
    assert create_res.status_code == 201
    wo_data = create_res.json()
    assert wo_data["status"] == "OPEN"
    wo_id = wo_data["id"]

    # Transition: OPEN -> IN_PROGRESS
    start_res = client.patch(
        f"/api/v1/work-orders/{wo_id}/status",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={"status": "IN_PROGRESS", "notes": "Started technician dispatch"}
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"

    # Transition: IN_PROGRESS -> COMPLETED
    complete_res = client.patch(
        f"/api/v1/work-orders/{wo_id}/status",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={"status": "COMPLETED", "downtime_minutes": 45, "notes": "Calibration complete"}
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["downtime_minutes"] == 45
