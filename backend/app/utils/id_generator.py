from datetime import datetime, timezone
import uuid


def generate_asset_code(seq: int) -> str:
    return f"AST-{seq:06d}"


def generate_calibration_code(asset_code: str, seq: int, year: int = 2026) -> str:
    return f"CAL-{asset_code}-{year}-{seq:06d}"


def generate_certificate_code(calibration_code: str) -> str:
    return f"CERT-{calibration_code}"


def generate_work_order_code(seq: int, year: int = 2026) -> str:
    return f"WO-{year}-{seq:06d}"


def generate_usage_code(asset_code: str, dt: datetime = None, seq: int = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    ts_str = dt.strftime("%Y%m%d%H%M%S")
    if seq is not None:
        suffix = f"{seq:04X}"
    else:
        suffix = uuid.uuid4().hex[:4].upper()
    return f"USE-{asset_code}-{ts_str}-{suffix}"


def generate_supplier_code(seq: int) -> str:
    return f"SUP-{seq:04d}"


def generate_plan_code(seq: int) -> str:
    return f"PLAN-{seq:06d}"


def generate_alert_code(seq: int) -> str:
    return f"ALT-{seq:06d}"


def generate_audit_code(seq: int) -> str:
    return f"AUD-{seq:06d}"


def generate_corrective_action_code(seq: int) -> str:
    return f"CAPA-{seq:06d}"


def generate_impact_assessment_code(seq: int) -> str:
    return f"IA-{seq:06d}"


def generate_extension_code(seq: int) -> str:
    return f"EXT-{seq:06d}"
