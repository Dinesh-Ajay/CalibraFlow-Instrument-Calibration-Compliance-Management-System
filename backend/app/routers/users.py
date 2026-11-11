from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, get_user_role_names, require_roles
from app.models.audit_record import AuditRecord
from app.models.user import Role, User, UserRole
from app.schemas.auth import RoleOut, UserOut
from app.schemas.user_admin import AdminResetPasswordRequest, AssignRolesRequest, UserActivityItem, UserCreateRequest, UserUpdateRequest
from app.services.audit_service import log_audit
from app.utils.date_utils import utcnow
from app.utils.password_reset import invalidate_user_tokens
from app.utils.rbac import INTERNAL_TO_DISPLAY, ROLE_PERMISSIONS, normalize_role, normalize_roles, roles_have_permission, to_display
from app.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["Users & Roles"])


def _to_user_out(u: User) -> UserOut:
    role_names = get_user_role_names(u)
    return UserOut(
        id=u.id,
        username=u.username,
        email=u.email,
        full_name=u.full_name,
        is_active=u.is_active,
        roles=[to_display(r) for r in role_names],
        role_ids=[ur.role_id for ur in (u.roles or [])],
        created_at=getattr(u, "created_at", None),
        updated_at=getattr(u, "updated_at", None),
    )


def _ensure_not_removing_last_admin(db: Session, target_user: User, new_role_ids: List[int], make_inactive: bool = False):
    admin_role = db.query(Role).filter(Role.role_name.in_(["Administrator", "admin"])).first()
    if not admin_role:
        return
    # Determine if target will remain active admin after change
    target_current_admin = any(ur.role_id == admin_role.id for ur in (target_user.roles or []))
    target_new_admin = admin_role.id in (new_role_ids or [])
    target_will_be_active_admin = (target_new_admin and not make_inactive and target_user.is_active) or (target_new_admin and not make_inactive)
    if make_inactive:
        target_will_be_active_admin = False
    if target_current_admin and not target_will_be_active_admin:
        # count other active admins
        active_admins = 0
        links = db.query(UserRole).filter(UserRole.role_id == admin_role.id).all()
        for link in links:
            u = db.query(User).filter(User.id == link.user_id).first()
            if u and u.is_active:
                active_admins += 1
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove or deactivate the last active administrator")


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    query = db.query(User)
    if search:
        s = f"%{search}%"
        query = query.filter((User.username.ilike(s)) | (User.email.ilike(s)) | (User.full_name.ilike(s)))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    users = query.order_by(User.id.asc()).all()
    results = []
    for u in users:
        roles_display = [to_display(r) for r in get_user_role_names(u)]
        if role:
            rn = normalize_role(role)
            if not rn or rn not in normalize_roles(roles_display):
                # compare normalized
                if rn not in get_user_role_names(u):
                    continue
        results.append(_to_user_out(u))
    return results


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    req: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    existing = db.query(User).filter((User.username == req.username) | (User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=req.username.strip(),
        email=str(req.email).strip(),
        full_name=req.full_name.strip(),
        hashed_password=hash_password(req.password),
        is_active=bool(req.is_active),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(user)
    db.flush()

    role_ids = list(dict.fromkeys(req.role_ids or []))
    if role_ids:
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
        if len(roles) != len(role_ids):
            raise HTTPException(status_code=400, detail="One or more role IDs are invalid")
        for r in roles:
            db.add(UserRole(user_id=user.id, role_id=r.id))

    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="User",
        entity_id=str(user.id),
        action="CREATE_USER",
        previous_value=None,
        new_value={"username": user.username, "email": user.email, "is_active": user.is_active, "role_ids": role_ids},
        reason="Administrator created user",
        request_id=get_request_id(request),
    )
    db.commit()
    db.refresh(user)
    return _to_user_out(user)


@router.get("/roles", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    roles = db.query(Role).order_by(Role.id.asc()).all()
    return [RoleOut(id=r.id, role_name=r.role_name, description=r.description) for r in roles]


@router.get("/permissions/matrix")
def get_permission_matrix(current_user: User = Depends(require_roles(["admin", "Administrator"]))):
    matrix = []
    for role_internal, perms in ROLE_PERMISSIONS.items():
        matrix.append({
            "role": INTERNAL_TO_DISPLAY.get(role_internal, role_internal),
            "role_internal": role_internal,
            "permissions": sorted(list(perms)),
        })
    return {"roles": matrix, "permission_definitions": sorted({p for ps in ROLE_PERMISSIONS.values() for p in ps if p != "*"})}


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["admin", "Administrator"]))):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_out(u)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    req: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if req.role_ids is not None:
        new_role_ids = list(dict.fromkeys(req.role_ids))
        _ensure_not_removing_last_admin(db, u, new_role_ids, make_inactive=(req.is_active is False))
    elif req.is_active is False:
        _ensure_not_removing_last_admin(db, u, [ur.role_id for ur in (u.roles or [])], make_inactive=True)

    prev = {"email": u.email, "full_name": u.full_name, "is_active": u.is_active, "role_ids": [ur.role_id for ur in (u.roles or [])]}
    if req.email is not None:
        other = db.query(User).filter(User.email == str(req.email), User.id != u.id).first()
        if other:
            raise HTTPException(status_code=400, detail="Email already in use")
        u.email = str(req.email).strip()
    if req.full_name is not None:
        u.full_name = req.full_name.strip()
    if req.is_active is not None:
        u.is_active = bool(req.is_active)

    if req.role_ids is not None:
        role_ids = list(dict.fromkeys(req.role_ids))
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
        if len(roles) != len(role_ids):
            raise HTTPException(status_code=400, detail="One or more role IDs are invalid")
        for ur in list(u.roles or []):
            db.delete(ur)
        db.flush()
        for r in roles:
            db.add(UserRole(user_id=u.id, role_id=r.id))

    u.updated_at = utcnow()
    db.flush()
    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="User",
        entity_id=str(u.id),
        action="UPDATE_USER",
        previous_value=prev,
        new_value={"email": u.email, "full_name": u.full_name, "is_active": u.is_active, "role_ids": [ur.role_id for ur in (u.roles or [])]},
        reason="Administrator updated user",
        request_id=get_request_id(request),
    )
    db.commit()
    db.refresh(u)
    return _to_user_out(u)


@router.post("/{user_id}/roles", response_model=UserOut)
def assign_roles(
    user_id: int,
    req: AssignRolesRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    role_ids = list(dict.fromkeys(req.role_ids or []))
    _ensure_not_removing_last_admin(db, u, role_ids, make_inactive=False)
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    if len(roles) != len(role_ids):
        raise HTTPException(status_code=400, detail="One or more role IDs are invalid")
    prev = {"role_ids": [ur.role_id for ur in (u.roles or [])]}
    for ur in list(u.roles or []):
        db.delete(ur)
    db.flush()
    for r in roles:
        db.add(UserRole(user_id=u.id, role_id=r.id))
    u.updated_at = utcnow()
    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="User",
        entity_id=str(u.id),
        action="ASSIGN_ROLES",
        previous_value=prev,
        new_value={"role_ids": role_ids},
        reason="Administrator updated role assignments",
        request_id=get_request_id(request),
    )
    db.commit()
    db.refresh(u)
    return _to_user_out(u)


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    _ensure_not_removing_last_admin(db, u, [ur.role_id for ur in (u.roles or [])], make_inactive=True)
    prev = {"is_active": u.is_active}
    u.is_active = False
    u.updated_at = utcnow()
    invalidate_user_tokens(u.id)
    log_audit(db, current_user.id, "User", str(u.id), "DEACTIVATE_USER", prev, {"is_active": False}, "Administrator deactivated user", get_request_id(request))
    db.commit()
    db.refresh(u)
    return _to_user_out(u)


@router.post("/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    prev = {"is_active": u.is_active}
    u.is_active = True
    u.updated_at = utcnow()
    log_audit(db, current_user.id, "User", str(u.id), "REACTIVATE_USER", prev, {"is_active": True}, "Administrator reactivated user", get_request_id(request))
    db.commit()
    db.refresh(u)
    return _to_user_out(u)


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    req: AdminResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.hashed_password = hash_password(req.new_password)
    u.updated_at = utcnow()
    invalidate_user_tokens(u.id)
    log_audit(db, current_user.id, "User", str(u.id), "ADMIN_RESET_PASSWORD", None, {"username": u.username}, "Administrator reset user password", get_request_id(request))
    db.commit()
    return {"message": "Password reset successfully"}


@router.get("/{user_id}/activity", response_model=List[UserActivityItem])
def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
    limit: int = Query(default=50, ge=1, le=200),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    rows = (
        db.query(AuditRecord)
        .filter(AuditRecord.actor_id == user_id)
        .order_by(AuditRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [UserActivityItem(action=r.action, entity_type=r.entity_type, entity_id=r.entity_id, timestamp=r.timestamp, reason=r.reason) for r in rows]
