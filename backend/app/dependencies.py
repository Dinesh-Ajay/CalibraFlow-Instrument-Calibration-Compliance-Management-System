from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Iterable, List, Optional

from app.database import get_db
from app.models.user import User
from app.utils.rbac import normalize_roles, roles_have_permission, to_display
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _extract_token(request: Request, token: Optional[str]) -> Optional[str]:
    if token:
        return token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def get_user_role_names(user: User) -> List[str]:
    names: List[str] = []
    for ur in getattr(user, "roles", []) or []:
        role = getattr(ur, "role", None)
        if role and getattr(role, "role_name", None):
            names.append(role.role_name)
    return normalize_roles(names)


def get_user_role_display_names(user: User) -> List[str]:
    return [to_display(r) for r in get_user_role_names(user)]


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    raw_token = _extract_token(request, token)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub") or payload.get("user_id")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Attach verified identity context for downstream use (never trust client-sent role)
    request.state.current_user_id = user.id
    request.state.current_user_roles = get_user_role_names(user)
    return user


def require_roles(allowed_roles: Iterable[str]):
    allowed = list(allowed_roles)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = get_user_role_names(current_user)
        # Admin has universal access
        if "admin" in user_roles:
            return current_user
        # Accept display/internal names in route declarations
        allowed_norm = normalize_roles(allowed)
        if any(r in allowed_norm for r in user_roles):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: insufficient role permissions",
        )

    return role_checker


def require_permissions(*permissions: str):
    def perm_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = get_user_role_names(current_user)
        for perm in permissions:
            if not roles_have_permission(user_roles, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: insufficient permissions",
                )
        return current_user

    return perm_checker


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "system-internal")
