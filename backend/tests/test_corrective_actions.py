def test_corrective_action_and_impact_assessment(client, engineer_token, quality_token):
    # 1. Failed calibration on asset
    assets_res = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {engineer_token}"})
    asset_id = assets_res.json()[0]["id"]

    fail_res = client.post(
        "/api/v1/calibration/events",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json={
            "asset_id": asset_id,
            "measured_value": 110.0,
            "reference_value": 100.0,
            "tolerance": 2.0,
            "performed_by": "Field Tech",
            "notes": "Failed test for CAPA verification"
        }
    )
    assert fail_res.status_code == 201
    cal_id = fail_res.json()["id"]

    # 2. Check CAPA auto-created
    capas_res = client.get(f"/api/v1/corrective-actions?asset_id={asset_id}", headers={"Authorization": f"Bearer {quality_token}"})
    assert capas_res.status_code == 200
    assert len(capas_res.json()) > 0
    capa_id = capas_res.json()[0]["id"]

    # 3. Update CAPA
    up_capa = client.patch(
        f"/api/v1/corrective-actions/{capa_id}",
        headers={"Authorization": f"Bearer {quality_token}"},
        json={
            "status": "IN_PROGRESS",
            "root_cause": "Aging diaphragm sensor element",
            "action_taken": "Procured replacement diaphragm kit"
        }
    )
    assert up_capa.status_code == 200
    assert up_capa.json()["status"] == "IN_PROGRESS"

    # 4. Check Impact Assessment
    ias_res = client.get(f"/api/v1/impact-assessments?asset_id={asset_id}", headers={"Authorization": f"Bearer {quality_token}"})
    assert ias_res.status_code == 200
    assert len(ias_res.json()) > 0
