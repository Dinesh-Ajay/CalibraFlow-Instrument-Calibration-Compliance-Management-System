import pytest


def test_user_registration(client, admin_token):
    # Open self-registration is disabled; admin provisions users securely
    roles_res = client.get("/api/v1/users/roles", headers={"Authorization": f"Bearer {admin_token}"})
    assert roles_res.status_code == 200
    roles = roles_res.json()
    maint = next((r for r in roles if r["role_name"] in ["Maintenance Engineer", "maint_eng"]), None)
    assert maint is not None

    res = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "new_tech",
            "email": "new_tech@calibraflow.internal",
            "full_name": "New Technician",
            "password": "password123",
            "role_ids": [maint["id"]],
            "is_active": True,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "new_tech"
    assert "Maintenance Engineer" in data["roles"]


def test_user_login(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert res.status_code == 401


def test_role_based_access_forbidden(client, operator_token):
    # Operator cannot register assets or create instrument types
    res = client.post(
        "/api/v1/instrument-types",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "type_code": "FORBIDDEN_TYPE",
            "type_name": "Forbidden Sensor",
            "measurement_unit": "psi",
            "default_calibration_interval_days": 90,
            "default_tolerance": 2.0
        }
    )
    assert res.status_code == 403
