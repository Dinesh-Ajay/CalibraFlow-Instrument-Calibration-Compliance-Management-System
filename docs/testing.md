# CalibraFlow — Testing & Verification Guide

CalibraFlow uses an automated test framework covering isolated SQLite testing and full API workflow integration.

## 1. Test Architecture

- **Test Suite**: `backend/tests/` (Pytest + HTTPX / Starlette TestClient)
- **Authoritative DB**: MySQL 8+ (`calibraflow`)
- **Automated Test DB**: Isolated SQLite in-memory engine (`sqlite:///:memory:`) ensures fast test execution without mutating production MySQL records.

## 2. Test Execution

### Running All Automated Unit & Integration Tests
```bash
python -m pytest -v backend/tests
```

### Running Specific Test Modules
```bash
# Assets and due-date logic
python -m pytest -v backend/tests/test_assets.py

# Authentication & RBAC
python -m pytest -v backend/tests/test_auth.py

# Password reset token persistence & security
python -m pytest -v backend/tests/test_password_reset.py

# Calibration formulas and events
python -m pytest -v backend/tests/test_calibration.py

# Certificate verification and asset mismatch
python -m pytest -v backend/tests/test_certificates.py

# Production usage gate evaluation
python -m pytest -v backend/tests/test_production_validation.py

# Work order lifecycle
python -m pytest -v backend/tests/test_work_orders.py

# Canonical route singleton verification
python -m pytest -v backend/tests/test_route_registration.py

# Synthetic data validation engine
python -m pytest -v backend/tests/test_data_validation.py
```

## 3. End-to-End Workflow Verification Script

CalibraFlow includes an integration verification script testing all seven core manufacturing business scenarios:

```bash
python backend/scripts/verify_integration_isolated.py
```

### Verified Scenarios:
1. **Workflow A**: Instrument creation -> calibration plan -> scheduling.
2. **Workflow B**: Calibration PASS -> certificate verification -> production usage allowed.
3. **Workflow C**: Calibration FAIL -> instrument restriction -> corrective action -> impact assessment.
4. **Workflow D**: Expired instrument usage -> BLOCKED -> persisted attempt -> audit.
5. **Workflow E**: Emergency extension request -> Quality approval -> policy evaluation.
6. **Workflow F**: Wrong-asset certificate -> verification rejected.
7. **Workflow G**: Failed calibration without impact assessment -> data-quality detection.
