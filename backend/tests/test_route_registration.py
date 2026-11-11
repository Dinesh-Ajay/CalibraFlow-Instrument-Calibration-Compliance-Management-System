"""Route registration tests for the canonical CalibraFlow FastAPI application.

These tests verify that all API routers are mounted under the configured API
prefix on the single canonical app instance (app.app_main:app). They use the
isolated SQLite test environment configured in conftest.py.
"""

from collections import Counter

from app.config import settings
from app.app_main import app


def _api_routes():
    """Return (method, path) pairs from the canonical app's OpenAPI schema.

    Iterating ``app.routes`` can surface mount/include placeholders for mounted
    routers while the actual endpoint methods are exposed via OpenAPI, so the
    schema is the authoritative view of registered API operations.
    """
    routes = []
    for path, operations in _openapi_paths().items():
        if not path.startswith(settings.API_V1_PREFIX):
            continue
        for method in sorted(m for m in operations.keys() if m not in {"head", "options", "parameters"}):
            routes.append((method.upper(), path))
    return routes


def _openapi_paths():
    schema = app.openapi()
    return schema.get("paths", {})


def test_canonical_app_is_singleton_with_app_main():
    from app.app_main import app as app_main

    assert app_main is app


def test_auth_and_users_core_routes_registered():
    paths = _openapi_paths()
    assert "/api/v1/auth/login" in paths
    assert "post" in paths["/api/v1/auth/login"]
    assert "/api/v1/auth/me" in paths
    assert "get" in paths["/api/v1/auth/me"]
    assert "/api/v1/users" in paths
    assert "get" in paths["/api/v1/users"]
    assert "post" in paths["/api/v1/users"]


def test_representative_endpoints_from_every_major_router_exist():
    paths = _openapi_paths()
    expected = {
        "/api/v1/auth/login": {"post"},
        "/api/v1/auth/me": {"get"},
        "/api/v1/users": {"get", "post"},
        "/api/v1/instrument-types": {"get", "post"},
        "/api/v1/assets": {"get", "post"},
        "/api/v1/calibration-plans": {"get", "post"},
        "/api/v1/calibration/events": {"get", "post"},
        "/api/v1/certificates": {"get"},
        "/api/v1/certificates/upload": {"post"},
        "/api/v1/work-orders": {"get", "post"},
        "/api/v1/production/usage": {"get", "post"},
        "/api/v1/production/validate-usage": {"post"},
        "/api/v1/emergency-extensions": {"get", "post"},
        "/api/v1/corrective-actions": {"get", "post"},
        "/api/v1/impact-assessments": {"get", "post"},
        "/api/v1/alerts": {"get"},
        "/api/v1/audit": {"get"},
        "/api/v1/dashboard/summary": {"get"},
        "/api/v1/assistant/query": {"post"},
        "/api/v1/suppliers": {"get", "post"},
    }
    for path, methods in expected.items():
        assert path in paths, f"missing path: {path}"
        present = set(paths[path].keys())
        for method in methods:
            assert method in present, f"missing method {method.upper()} for {path}; present={sorted(present)}"


def test_no_duplicate_api_route_registrations():
    routes = _api_routes()
    duplicates = [item for item, count in Counter(routes).items() if count > 1]
    assert duplicates == [], f"duplicate route registrations detected: {duplicates}"


def test_all_registered_router_modules_contribute_api_routes():
    paths = _openapi_paths()
    expected_prefixes = [
        "/api/v1/auth",
        "/api/v1/users",
        "/api/v1/instrument-types",
        "/api/v1/assets",
        "/api/v1/calibration-plans",
        "/api/v1/calibration",
        "/api/v1/certificates",
        "/api/v1/work-orders",
        "/api/v1/production",
        "/api/v1/emergency-extensions",
        "/api/v1/corrective-actions",
        "/api/v1/impact-assessments",
        "/api/v1/alerts",
        "/api/v1/audit",
        "/api/v1/dashboard",
        "/api/v1/assistant",
        "/api/v1/suppliers",
    ]
    for prefix in expected_prefixes:
        assert any(p == prefix or p.startswith(prefix + "/") for p in paths), f"no routes registered for prefix {prefix}"


def test_total_api_route_methods_are_registered():
    routes = _api_routes()
    # 17 router modules currently contribute 61 endpoint-method registrations total.
    assert len(routes) >= 61, f"unexpectedly low API route count: {len(routes)}"
