import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.utils.date_utils import utcnow

logger = logging.getLogger(__name__)

# In-memory token store fallback
# Format: token_hash -> {user_id, expires_at, used}
_RESET_STORE: dict[str, dict] = {}


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_reset_token(
    user_id: int,
    token: str,
    ttl_minutes: int = 30,
    db: Optional[Session] = None,
    request_ip: Optional[str] = None,
) -> None:
    token_hashed = hash_token(token)
    expires_at = utcnow() + timedelta(minutes=ttl_minutes)

    # Always keep in-memory store synchronized as fallback
    _RESET_STORE[token_hashed] = {
        "user_id": user_id,
        "expires_at": expires_at,
        "used": False,
    }

    if db is not None:
        try:
            from app.models.password_reset import PasswordResetToken
            db_token = PasswordResetToken(
                user_id=user_id,
                token_hash=token_hashed,
                expires_at=expires_at,
                is_used=False,
                created_at=utcnow(),
                request_ip=request_ip,
            )
            db.add(db_token)
            db.flush()
        except Exception as e:
            logger.warning("Could not persist password reset token in database: %s", e)


def consume_reset_token(token: str, db: Optional[Session] = None) -> Optional[int]:
    token_hashed = hash_token(token)

    if db is not None:
        try:
            from app.models.password_reset import PasswordResetToken
            row = (
                db.query(PasswordResetToken)
                .filter(PasswordResetToken.token_hash == token_hashed)
                .first()
            )
            if row is not None:
                if row.is_used:
                    return None
                # Handle timezone-aware or naive datetimes safely
                exp = row.expires_at
                now = utcnow()
                if exp.tzinfo is None and now.tzinfo is not None:
                    exp = exp.replace(tzinfo=now.tzinfo)
                elif exp.tzinfo is not None and now.tzinfo is None:
                    now = now.replace(tzinfo=exp.tzinfo)

                if exp < now:
                    row.is_used = True
                    db.flush()
                    return None

                row.is_used = True
                db.flush()
                # Also mark memory store used
                if token_hashed in _RESET_STORE:
                    _RESET_STORE[token_hashed]["used"] = True
                return int(row.user_id)
        except Exception as e:
            logger.warning("Database token lookup failed, falling back to memory: %s", e)

    # Fallback to memory store
    item = _RESET_STORE.get(token_hashed)
    if not item:
        return None
    if item.get("used"):
        return None
    expires_at = item.get("expires_at")
    if expires_at and expires_at < utcnow():
        item["used"] = True
        return None
    item["used"] = True
    return int(item["user_id"])


def invalidate_user_tokens(user_id: int, db: Optional[Session] = None) -> None:
    # Memory store invalidation
    for item in _RESET_STORE.values():
        if item.get("user_id") == user_id:
            item["used"] = True

    if db is not None:
        try:
            from app.models.password_reset import PasswordResetToken
            tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False,  # noqa: E712
            ).all()
            for t in tokens:
                t.is_used = True
            db.flush()
        except Exception as e:
            logger.warning("Could not invalidate database tokens: %s", e)
