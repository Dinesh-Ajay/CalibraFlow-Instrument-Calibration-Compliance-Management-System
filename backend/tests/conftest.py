import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
from app.app_main import app
from app.models.user import User, Role, UserRole
from app.models.instrument_type import InstrumentType
from app.models.asset import Asset
from app.models.calibration_plan import CalibrationPlan
from app.utils.security import hash_password
from app.utils.date_utils import utcnow

# SQLite in-memory engine for fast, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed roles
    roles = [
        "Administrator",
        "Plant Operator",
        "Maintenance Engineer",
        "Quality Engineer",
        "Production Planner"
    ]
    for r in roles:
        if not db.query(Role).filter(Role.role_name == r).first():
            db.add(Role(role_name=r, description=f"Test role {r}"))
    db.commit()

    # Seed test users
    users = [
        ("admin", "admin@test.internal", "Admin User", "admin123", ["Administrator"]),
        ("operator", "operator@test.internal", "Operator User", "operator123", ["Plant Operator"]),
        ("engineer", "engineer@test.internal", "Engineer User", "engineer123", ["Maintenance Engineer"]),
        ("quality", "quality@test.internal", "Quality User", "quality123", ["Quality Engineer"]),
        ("planner", "planner@test.internal", "Planner User", "Production Planner", ["Production Planner"])
    ]
    for username, email, full_name, raw_pwd, uroles in users:
        u = db.query(User).filter(User.username == username).first()
        if not u:
            u = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(raw_pwd),
                is_active=True
            )
            db.add(u)
            db.flush()
            for rname in uroles:
                r_obj = db.query(Role).filter(Role.role_name == rname).first()
                if r_obj:
                    db.add(UserRole(user_id=u.id, role_id=r_obj.id))
    db.commit()

    # Seed standard test instrument type
    if not db.query(InstrumentType).filter(InstrumentType.type_code == "PRESSURE").first():
        db.add(InstrumentType(
            type_code="PRESSURE",
            type_name="Pressure Gauge",
            description="Pressure gauge sensor",
            measurement_unit="bar",
            default_calibration_interval_days=90,
            default_tolerance=2.0,
            is_active=True
        ))
        db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def operator_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "operator", "password": "operator123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def engineer_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "engineer", "password": "engineer123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def quality_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "quality", "password": "quality123"})
    assert res.status_code == 200
    return res.json()["access_token"]

