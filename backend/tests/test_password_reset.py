from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.utils.date_utils import utcnow
from app.utils.password_reset import (
    generate_reset_token,
    hash_token,
    store_reset_token,
    consume_reset_token,
    invalidate_user_tokens,
)
from app.utils.security import hash_password, verify_password


def test_password_reset_token_generation_and_hashing():
    t1 = generate_reset_token()
    t2 = generate_reset_token()
    assert len(t1) >= 32
    assert t1 != t2

    h1 = hash_token(t1)
    assert len(h1) == 64
    assert h1 == hash_token(t1)
    assert h1 != hash_token(t2)


def test_password_reset_token_db_persistence(db_session: Session):
    user = db_session.query(User).filter(User.username == "admin").first()
    assert user is not None

    token = generate_reset_token()
    store_reset_token(user.id, token, ttl_minutes=30, db=db_session, request_ip="127.0.0.1")
    db_session.commit()

    # Verify record in DB
    record = (
        db_session.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_token(token))
        .first()
    )
    assert record is not None
    assert record.user_id == user.id
    assert record.is_used is False
    assert record.request_ip == "127.0.0.1"

    # Consume token
    resolved_id = consume_reset_token(token, db=db_session)
    db_session.commit()
    assert resolved_id == user.id

    # Verify record marked as used
    db_session.refresh(record)
    assert record.is_used is True

    # Re-consume should return None (single-use protection)
    re_consumed = consume_reset_token(token, db=db_session)
    assert re_consumed is None


def test_password_reset_token_expiration(db_session: Session):
    user = db_session.query(User).filter(User.username == "operator").first()
    assert user is not None

    token = generate_reset_token()
    # Store token expired in the past
    store_reset_token(user.id, token, ttl_minutes=-10, db=db_session)
    db_session.commit()

    # Should fail to consume because it is expired
    result = consume_reset_token(token, db=db_session)
    assert result is None


def test_password_reset_invalidation(db_session: Session):
    user = db_session.query(User).filter(User.username == "engineer").first()
    assert user is not None

    token1 = generate_reset_token()
    token2 = generate_reset_token()
    store_reset_token(user.id, token1, ttl_minutes=30, db=db_session)
    store_reset_token(user.id, token2, ttl_minutes=30, db=db_session)
    db_session.commit()

    # Invalidate all tokens for this user
    invalidate_user_tokens(user.id, db=db_session)
    db_session.commit()

    assert consume_reset_token(token1, db=db_session) is None
    assert consume_reset_token(token2, db=db_session) is None


def test_api_forgot_and_reset_password_flow(client: TestClient, db_session: Session):
    # Create an isolated user for reset flow test
    reset_user = db_session.query(User).filter(User.username == "reset_tester").first()
    if not reset_user:
        reset_user = User(
            username="reset_tester",
            email="reset_tester@test.internal",
            full_name="Reset Tester",
            hashed_password=hash_password("InitialPassword123!"),
            is_active=True,
        )
        db_session.add(reset_user)
        db_session.commit()

    # Test forgot password endpoint
    res = client.post("/api/v1/auth/forgot-password", json={"email": "reset_tester@test.internal"})
    assert res.status_code == 200
    assert "password recovery" in res.json().get("message", "").lower()

    # Retrieve created token for reset tester
    db_token = (
        db_session.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == reset_user.id, PasswordResetToken.is_used == False)
        .order_by(PasswordResetToken.created_at.desc())
        .first()
    )
    assert db_token is not None

    # Reset password with valid token
    test_reset_token = generate_reset_token()
    store_reset_token(reset_user.id, test_reset_token, ttl_minutes=15, db=db_session)
    db_session.commit()

    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": test_reset_token, "new_password": "NewSecurePassword123!"},
    )
    assert reset_res.status_code == 200
    assert "successfully" in reset_res.json().get("message", "").lower()

    # Verify password changed in DB
    db_session.refresh(reset_user)
    assert verify_password("NewSecurePassword123!", reset_user.hashed_password)

    # Token cannot be reused
    reuse_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": test_reset_token, "new_password": "AnotherPassword123!"},
    )
    assert reuse_res.status_code == 400
