from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, get_user_role_names
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    Token,
    UserOut,
)
from app.services.audit_service import log_audit
from app.services.bootstrap_service import ensure_roles, ensure_required_users
from app.services.notification_service import send_email_notification
from app.utils.date_utils import utcnow
from app.utils.password_reset import consume_reset_token, generate_reset_token, invalidate_user_tokens, store_reset_token
from app.utils.rbac import to_display
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_out(user: User) -> UserOut:
    role_names = get_user_role_names(user)
    role_ids = [ur.role_id for ur in (user.roles or []) if getattr(ur, "role_id", None) is not None]
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[to_display(r) for r in role_names],
        role_ids=role_ids,
        created_at=getattr(user, "created_at", None),
        updated_at=getattr(user, "updated_at", None),
    )


@router.post("/login", response_model=Token)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Ensure required roles/accounts exist (idempotent, safe)
    try:
        ensure_roles(db)
        ensure_required_users(db, actor_id=None, request_id=get_request_id(request))
        db.commit()
    except Exception:
        db.rollback()
        # Do not block login if bootstrap encounters a non-critical issue; continue with existing data

    identifier = (req.username or "").strip()
    user = (
        db.query(User)
        .filter((User.username == identifier) | (User.email == identifier))
        .first()
    )
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    roles_internal = get_user_role_names(user)
    roles_display = [to_display(r) for r in roles_internal]
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "user_id": user.id,
            "username": user.username,
            "roles": roles_display,  # informational claim; backend always verifies from DB
        }
    )

    try:
        log_audit(
            db=db,
            actor_id=user.id,
            entity_type="User",
            entity_id=str(user.id),
            action="LOGIN",
            previous_value=None,
            new_value={"username": user.username},
            reason="User authenticated",
            request_id=get_request_id(request),
        )
        db.commit()
    except Exception:
        db.rollback()

    return Token(access_token=access_token, token_type="bearer", user=_user_out(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    # Always return generic response to avoid account enumeration
    generic = {"message": "If the email is registered, a password recovery message has been sent."}
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.is_active:
        return generic

    token = generate_reset_token()
    client_ip = request.client.host if request.client else None
    store_reset_token(user.id, token, ttl_minutes=30, db=db, request_ip=client_ip)
    reset_link_hint = f"/reset-password?token={token}"
    body = (
        f"<p>Hello {user.full_name},</p>"
        f"<p>A password reset was requested for your CalibraFlow account.</p>"
        f"<p><strong>Recovery token:</strong> {token}</p>"
        f"<p>This token expires in 30 minutes and can be used once.</p>"
        f"<p>If you did not request this, you can ignore this message.</p>"
    )
    try:
        send_email_notification(user.email, "CalibraFlow Password Recovery", body)
        log_audit(
            db=db,
            actor_id=user.id,
            entity_type="User",
            entity_id=str(user.id),
            action="PASSWORD_RESET_REQUESTED",
            previous_value=None,
            new_value={"email": user.email},
            reason="Password recovery requested",
            request_id=get_request_id(request),
        )
        db.commit()
    except Exception:
        db.rollback()
    # In dev environments without SMTP visibility, do not expose token in API response/logs.
    return generic


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    user_id = consume_reset_token(req.token, db=db)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired recovery token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired recovery token")

    user.hashed_password = hash_password(req.new_password)
    user.updated_at = utcnow()
    invalidate_user_tokens(user.id, db=db)
    log_audit(
        db=db,
        actor_id=user.id,
        entity_type="User",
        entity_id=str(user.id),
        action="PASSWORD_RESET",
        previous_value=None,
        new_value={"username": user.username},
        reason="Password reset completed",
        request_id=get_request_id(request),
    )
    db.commit()
    return {"message": "Password has been reset successfully. Please sign in with your new password."}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(req.new_password)
    current_user.updated_at = utcnow()
    invalidate_user_tokens(current_user.id, db=db)
    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="User",
        entity_id=str(current_user.id),
        action="PASSWORD_CHANGED",
        previous_value=None,
        new_value={"username": current_user.username},
        reason="User changed password",
        request_id=get_request_id(request),
    )
    db.commit()
    return {"message": "Password changed successfully."}
