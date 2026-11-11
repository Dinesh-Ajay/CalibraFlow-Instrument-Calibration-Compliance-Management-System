"""Centralized RBAC: role identifiers, display names, and permission checks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_MAINT_ENG = "maint_eng"
ROLE_QUALITY_ENG = "quality_eng"
ROLE_PLANNER = "planner"

DISPLAY_TO_INTERNAL = {
    "Administrator": ROLE_ADMIN,
    "Plant Operator": ROLE_OPERATOR,
    "Maintenance Engineer": ROLE_MAINT_ENG,
    "Quality Engineer": ROLE_QUALITY_ENG,
    "Production Planner": ROLE_PLANNER,
}
INTERNAL_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_INTERNAL.items()}

# Accept both legacy/display names and internal identifiers from DB/tokens
ALIASES = {
    "admin": ROLE_ADMIN,
    "administrator": ROLE_ADMIN,
    "operator": ROLE_OPERATOR,
    "plant operator": ROLE_OPERATOR,
    "plant_operator": ROLE_OPERATOR,
    "maint_eng": ROLE_MAINT_ENG,
    "maintenance engineer": ROLE_MAINT_ENG,
    "maintenance_engineer": ROLE_MAINT_ENG,
    "quality_eng": ROLE_QUALITY_ENG,
    "quality engineer": ROLE_QUALITY_ENG,
    "quality_engineer": ROLE_QUALITY_ENG,
    "planner": ROLE_PLANNER,
    "production planner": ROLE_PLANNER,
    "production_planner": ROLE_PLANNER,
}


def normalize_role(role: str) -> Optional[str]:
    if not role:
        return None
    key = str(role).strip()
    return ALIASES.get(key.lower()) or (key if key in INTERNAL_TO_DISPLAY else None)


def normalize_roles(roles: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for r in roles or []:
        n = normalize_role(r)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def to_display(role: str) -> str:
    n = normalize_role(role)
    return INTERNAL_TO_DISPLAY.get(n, role) if n else role


# Permission names (centralized)
PERM_VIEW_DASHBOARD = "dashboard.view"
PERM_VIEW_ASSETS = "assets.view"
PERM_MANAGE_ASSETS = "assets.manage"
PERM_MANAGE_INSTRUMENT_TYPES = "instrument_types.manage"
PERM_VIEW_CALIBRATION_PLANS = "calibration_plans.view"
PERM_MANAGE_CALIBRATION_PLANS = "calibration_plans.manage"
PERM_RECORD_CALIBRATION = "calibration.record"
PERM_VERIFY_CERTIFICATES = "certificates.verify"
PERM_UPLOAD_CERTIFICATES = "certificates.upload"
PERM_CREATE_WORK_ORDERS = "work_orders.create"
PERM_SCHEDULE_WORK_ORDERS = "work_orders.schedule"
PERM_EXECUTE_WORK_ORDERS = "work_orders.execute"
PERM_RECORD_PRODUCTION_USE = "production.record"
PERM_VIEW_PRODUCTION_USE = "production.view"
PERM_APPROVE_EXTENSIONS = "extensions.approve"
PERM_MANAGE_EXTENSIONS = "extensions.manage"
PERM_IMPACT_ASSESSMENT = "impact.manage"
PERM_VIEW_AUDIT = "audit.view"
PERM_MANAGE_USERS = "users.manage"
PERM_MANAGE_ROLES = "roles.manage"
PERM_MANAGE_SUPPLIERS = "suppliers.manage"
PERM_VIEW_DATA_QUALITY = "data_quality.view"
PERM_VIEW_ALERTS = "alerts.view"
PERM_ACK_ALERTS = "alerts.ack"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_ADMIN: {"*"},
    ROLE_OPERATOR: {
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_ASSETS,
        PERM_RECORD_PRODUCTION_USE,
        PERM_VIEW_PRODUCTION_USE,
        PERM_VIEW_ALERTS,
        PERM_ACK_ALERTS,
    },
    ROLE_MAINT_ENG: {
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_ASSETS,
        PERM_MANAGE_ASSETS,
        PERM_VIEW_CALIBRATION_PLANS,
        PERM_MANAGE_CALIBRATION_PLANS,
        PERM_RECORD_CALIBRATION,
        PERM_UPLOAD_CERTIFICATES,
        PERM_CREATE_WORK_ORDERS,
        PERM_SCHEDULE_WORK_ORDERS,
        PERM_EXECUTE_WORK_ORDERS,
        PERM_VIEW_PRODUCTION_USE,
        PERM_VIEW_ALERTS,
        PERM_ACK_ALERTS,
        PERM_IMPACT_ASSESSMENT,
    },
    ROLE_QUALITY_ENG: {
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_ASSETS,
        PERM_VIEW_CALIBRATION_PLANS,
        PERM_VERIFY_CERTIFICATES,
        PERM_UPLOAD_CERTIFICATES,
        PERM_VIEW_PRODUCTION_USE,
        PERM_APPROVE_EXTENSIONS,
        PERM_MANAGE_EXTENSIONS,
        PERM_IMPACT_ASSESSMENT,
        PERM_VIEW_AUDIT,
        PERM_VIEW_DATA_QUALITY,
        PERM_VIEW_ALERTS,
        PERM_ACK_ALERTS,
    },
    ROLE_PLANNER: {
        PERM_VIEW_DASHBOARD,
        PERM_VIEW_ASSETS,
        PERM_VIEW_CALIBRATION_PLANS,
        PERM_CREATE_WORK_ORDERS,
        PERM_SCHEDULE_WORK_ORDERS,
        PERM_VIEW_PRODUCTION_USE,
        PERM_VIEW_ALERTS,
        PERM_ACK_ALERTS,
    },
}


def roles_have_permission(user_roles: Iterable[str], permission: str) -> bool:
    roles = normalize_roles(user_roles)
    if ROLE_ADMIN in roles:
        return True
    for r in roles:
        perms = ROLE_PERMISSIONS.get(r, set())
        if "*" in perms or permission in perms:
            return True
    return False


def role_display_list(user_roles: Iterable[str]) -> list[str]:
    return [to_display(r) for r in normalize_roles(user_roles)]


@dataclass(frozen=True)
class PermissionMatrixRow:
    feature: str
    permissions: list[str]
