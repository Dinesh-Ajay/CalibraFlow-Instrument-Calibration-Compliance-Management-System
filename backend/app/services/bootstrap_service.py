"""Idempotent bootstrap for roles and required initial application accounts.

Safe to run repeatedly:
- ensures required roles exist
- creates missing required accounts with specified initial credentials
- updates required accounts' email/full_name/is_active/role assignment to match spec
- does NOT overwrite passwords for existing required accounts on rerun
- never deletes historical records or demo data automatically

NOTE: Initial passwords below are required by project spec for first-time setup.
Do not log them. Frontend must not hardcode them.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User, Role, UserRole
from app.services.audit_service import log_audit
from app.utils.date_utils import utcnow
from app.utils.security import hash_password, verify_password
from app.utils.rbac import DISPLAY_TO_INTERNAL, INTERNAL_TO_DISPLAY

REQUIRED_ROLES = [
    ("admin", "Administrator", "Full system administration and policy control"),
    ("operator", "Plant Operator", "Records production usage and checks instrument availability"),
    ("maint_eng", "Maintenance Engineer", "Manages instruments, executes calibration, handles work orders"),
    ("quality_eng", "Quality Engineer", "Verifies certificates, manages quality decisions and extensions"),
    ("planner", "Production Planner", "Schedules calibrations/work orders and monitors planning impact"),
]

# Spec-mandated initial accounts (created/ensured idempotently)
REQUIRED_USERS = [
    {"username": "Ajay", "full_name": "Ajay", "role": "admin", "password": "Aj@y10572", "email": "ajaykrishna874@gmail.com"},
    {"username": "dinesh", "full_name": "Dinesh", "role": "operator", "password": "Aj@y10572", "email": "dineshajay874@gmail.com"},
    {"username": "Ali", "full_name": "Ali", "role": "maint_eng", "password": "Ali10572", "email": "ali874@gmail.com"},
    {"username": "Kali", "full_name": "kali", "role": "quality_eng", "password": "K@li10572", "email": "kali874@gmail.com"},
    {"username": "krish", "full_name": "krishna", "role": "planner", "password": "Aj@y10572", "email": "krishnaaj123@gmail.com"},
]


def ensure_roles(db: Session) -> dict[str, Role]:
    role_map: dict[str, Role] = {}
    # Ensure canonical roles exist (store display name in role_name for compatibility with existing UI/data)
    for internal, display, desc in REQUIRED_ROLES:
        role = db.query(Role).filter(Role.role_name == display).first()
        if not role:
            # also check internal id stored as name in some deployments
            role = db.query(Role).filter(Role.role_name == internal).first()
        if not role:
            role = Role(role_name=display, description=desc)
            db.add(role)
            db.flush()
        else:
            if role.description != desc:
                role.description = desc
        role_map[internal] = role
        role_map[display] = role
    db.flush()
    return role_map


def _get_user_by_username_case_insensitive(db: Session, username: str) -> User | None:
    # MySQL collations often case-insensitive, but do explicit check for safety
    users = db.query(User).all()
    for u in users:
        if (u.username or "").lower() == username.lower():
            return u
    return None


def ensure_required_users(db: Session, actor_id: int | None = None, request_id: str | None = None) -> list[dict]:
    roles = ensure_roles(db)
    results = []
    for spec in REQUIRED_USERS:
        internal_role = spec["role"]
        display_role = INTERNAL_TO_DISPLAY[internal_role]
        role = roles[internal_role]
        user = _get_user_by_username_case_insensitive(db, spec["username"])
        created = False
        if not user:
            # Avoid email collision by checking existing email owner
            email_owner = db.query(User).filter(User.email == spec["email"]).first()
            if email_owner and email_owner.username.lower() != spec["username"].lower():
                # keep existing owner untouched; cannot safely claim email
                results.append({"username": spec["username"], "status": "skipped_email_conflict", "conflict_user_id": email_owner.id})
                continue
            user = User(
                username=spec["username"],
                email=spec["email"],
                full_name=spec["full_name"],
                hashed_password=hash_password(spec["password"]),
                is_active=True,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(user)
            db.flush()
            created = True
        else:
            # Idempotent update of profile/role/email/active status; do not reset password on rerun
            # Resolve email conflict safely: only set if free or already owned by this user
            email_owner = db.query(User).filter(User.email == spec["email"]).first()
            if not email_owner or email_owner.id == user.id:
                user.email = spec["email"]
            user.full_name = spec["full_name"]
            user.is_active = True
            user.updated_at = utcnow()
            # If somehow password was never set/invalid, set initial one (best-effort safety)
            if not getattr(user, "hashed_password", None):
                user.hashed_password = hash_password(spec["password"])

        # Ensure exact required role assignment (replace roles with the specified one for these managed accounts)
        # to prevent privilege drift; keep operation idempotent
        existing_links = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        desired_role_id = role.id
        current_role_ids = sorted([ur.role_id for ur in existing_links])
        if current_role_ids != [desired_role_id]:
            for ur in existing_links:
                db.delete(ur)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=desired_role_id))

        db.flush()
        log_audit(
            db=db,
            actor_id=actor_id,
            entity_type="User",
            entity_id=str(user.id),
            action="BOOTSTRAP_CREATE" if created else "BOOTSTRAP_ENSURE",
            previous_value=None,
            new_value={"username": user.username, "email": user.email, "role": display_role, "is_active": True},
            reason="Idempotent required account initialization",
            request_id=request_id,
        )
        results.append({"username": user.username, "id": user.id, "status": "created" if created else "ensured", "role": display_role})
    db.commit()
    return results


def bootstrap_required_access(db: Session, actor_id: int | None = None, request_id: str | None = None) -> dict:
    roles = ensure_roles(db)
    users = ensure_required_users(db, actor_id=actor_id, request_id=request_id)
    return {"roles_ensured": len(REQUIRED_ROLES), "users": users}
