from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from app.models.asset import Asset
from app.models.calibration_event import CalibrationEvent
from app.models.certificate import Certificate
from app.models.emergency_extension import EmergencyExtension
from app.models.production_use import ProductionUse
from app.models.alert import Alert
from app.utils.id_generator import generate_usage_code
from app.utils.date_utils import utcnow, is_overdue
from app.services.audit_service import log_audit
from app.services.alert_service import create_alert


def evaluate_asset_production_eligibility(
    db: Session,
    asset_id: int,
    usage_timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    if usage_timestamp is None:
        usage_timestamp = utcnow()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return {
            "decision": "BLOCKED",
            "reason": f"Asset with ID {asset_id} does not exist in the system.",
            "asset_code": "UNKNOWN",
            "asset_name": "UNKNOWN",
            "applicable_due_date": None,
            "certificate_status": None,
            "exception_reference": None,
            "last_calibration_date": None,
            "latest_calibration_event_id": None,
            "exception_id": None,
            "is_allowed": False
        }

    # 1. Check Operational Status
    if asset.operational_status != "ACTIVE":
        return {
            "decision": "BLOCKED",
            "reason": f"Asset {asset.asset_code} operational status is '{asset.operational_status}' (must be 'ACTIVE' for production use).",
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "applicable_due_date": asset.next_due_date,
            "certificate_status": None,
            "exception_reference": None,
            "last_calibration_date": asset.last_calibration_date,
            "latest_calibration_event_id": None,
            "exception_id": None,
            "is_allowed": False
        }

    # 2. Check if calibration is required
    if not asset.requires_calibration:
        return {
            "decision": "ALLOWED",
            "reason": f"Asset {asset.asset_code} does not require periodic calibration per engineering policy.",
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "applicable_due_date": None,
            "certificate_status": "EXEMPT",
            "exception_reference": None,
            "last_calibration_date": asset.last_calibration_date,
            "latest_calibration_event_id": None,
            "exception_id": None,
            "is_allowed": True
        }

    # 3. Check for failed calibration state
    if asset.calibration_status == "FAILED":
        return {
            "decision": "BLOCKED",
            "reason": f"Asset {asset.asset_code} failed its latest calibration. Production usage is strictly prohibited until recalibration and CAPA sign-off.",
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "applicable_due_date": asset.next_due_date,
            "certificate_status": "FAILED",
            "exception_reference": None,
            "last_calibration_date": asset.last_calibration_date,
            "latest_calibration_event_id": None,
            "exception_id": None,
            "is_allowed": False
        }

    # 4. Check latest calibration event
    latest_event = db.query(CalibrationEvent).filter(
        CalibrationEvent.asset_id == asset.id
    ).order_by(CalibrationEvent.calibration_date.desc()).first()

    if latest_event and latest_event.result == "FAIL":
        return {
            "decision": "BLOCKED",
            "reason": f"Latest calibration event {latest_event.calibration_code} resulted in FAIL. Instrument is quarantined.",
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "applicable_due_date": asset.next_due_date,
            "certificate_status": "FAILED",
            "exception_reference": None,
            "last_calibration_date": asset.last_calibration_date,
            "latest_calibration_event_id": latest_event.id,
            "exception_id": None,
            "is_allowed": False
        }

    # 5. Check Emergency Extensions
    active_approved_extension = db.query(EmergencyExtension).filter(
        EmergencyExtension.asset_id == asset.id,
        EmergencyExtension.approval_status == "APPROVED",
        EmergencyExtension.extended_due_date >= usage_timestamp
    ).order_by(EmergencyExtension.extended_due_date.desc()).first()

    # 6. Check Due Date vs Usage Timestamp
    is_date_expired = False
    effective_due_date = asset.next_due_date

    if asset.next_due_date:
        # Normalize comparison
        due = asset.next_due_date
        u_ts = usage_timestamp
        if due.tzinfo is not None and u_ts.tzinfo is None:
            u_ts = u_ts.replace(tzinfo=due.tzinfo)
        elif due.tzinfo is None and u_ts.tzinfo is not None:
            due = due.replace(tzinfo=u_ts.tzinfo)

        if u_ts > due:
            is_date_expired = True

    if is_date_expired:
        if active_approved_extension:
            return {
                "decision": "ALLOWED_WITH_EXCEPTION",
                "reason": f"Instrument calibration expired on {asset.next_due_date.strftime('%Y-%m-%d')}, but an approved Emergency Extension ({active_approved_extension.extension_code}) is active until {active_approved_extension.extended_due_date.strftime('%Y-%m-%d')}.",
                "asset_code": asset.asset_code,
                "asset_name": asset.asset_name,
                "applicable_due_date": active_approved_extension.extended_due_date,
                "certificate_status": "EXCEPTION_AUTHORIZED",
                "exception_reference": active_approved_extension.extension_code,
                "last_calibration_date": asset.last_calibration_date,
                "latest_calibration_event_id": latest_event.id if latest_event else None,
                "exception_id": active_approved_extension.id,
                "is_allowed": True
            }
        else:
            return {
                "decision": "BLOCKED",
                "reason": f"Calibration expired on {asset.next_due_date.strftime('%Y-%m-%d %H:%M')}. No approved emergency extension exists.",
                "asset_code": asset.asset_code,
                "asset_name": asset.asset_name,
                "applicable_due_date": asset.next_due_date,
                "certificate_status": "EXPIRED",
                "exception_reference": None,
                "last_calibration_date": asset.last_calibration_date,
                "latest_calibration_event_id": latest_event.id if latest_event else None,
                "exception_id": None,
                "is_allowed": False
            }

    # 7. Check Certificate Status if certificate required
    cert_status = "NOT_REQUIRED"
    if asset.requires_certificate:
        if not latest_event:
            # If no calibration event has ever been completed and certificate is required
            if asset.commissioning_date and not active_approved_extension:
                return {
                    "decision": "BLOCKED",
                    "reason": f"Asset requires initial calibration certificate prior to production commissioning.",
                    "asset_code": asset.asset_code,
                    "asset_name": asset.asset_name,
                    "applicable_due_date": asset.next_due_date,
                    "certificate_status": "MISSING",
                    "exception_reference": None,
                    "last_calibration_date": asset.last_calibration_date,
                    "latest_calibration_event_id": None,
                    "exception_id": None,
                    "is_allowed": False
                }
        else:
            cert = db.query(Certificate).filter(
                Certificate.calibration_event_id == latest_event.id
            ).first()

            if not cert:
                cert_status = "MISSING"
                return {
                    "decision": "BLOCKED",
                    "reason": f"Calibration event {latest_event.calibration_code} requires a verified certificate, but no certificate is uploaded.",
                    "asset_code": asset.asset_code,
                    "asset_name": asset.asset_name,
                    "applicable_due_date": asset.next_due_date,
                    "certificate_status": "MISSING",
                    "exception_reference": None,
                    "last_calibration_date": asset.last_calibration_date,
                    "latest_calibration_event_id": latest_event.id,
                    "exception_id": None,
                    "is_allowed": False
                }
            elif cert.verification_status == "INVALID":
                return {
                    "decision": "BLOCKED",
                    "reason": f"Certificate {cert.certificate_code} is flagged INVALID (possible asset mismatch or failed verification).",
                    "asset_code": asset.asset_code,
                    "asset_name": asset.asset_name,
                    "applicable_due_date": asset.next_due_date,
                    "certificate_status": "INVALID",
                    "exception_reference": None,
                    "last_calibration_date": asset.last_calibration_date,
                    "latest_calibration_event_id": latest_event.id,
                    "exception_id": None,
                    "is_allowed": False
                }
            elif cert.verification_status != "VERIFIED":
                return {
                    "decision": "BLOCKED",
                    "reason": f"Certificate {cert.certificate_code} status is '{cert.verification_status}'. Quality verification is required before production usage.",
                    "asset_code": asset.asset_code,
                    "asset_name": asset.asset_name,
                    "applicable_due_date": asset.next_due_date,
                    "certificate_status": cert.verification_status,
                    "exception_reference": None,
                    "last_calibration_date": asset.last_calibration_date,
                    "latest_calibration_event_id": latest_event.id,
                    "exception_id": None,
                    "is_allowed": False
                }
            else:
                cert_status = "VERIFIED"

    # All checks passed!
    return {
        "decision": "ALLOWED",
        "reason": f"Instrument {asset.asset_code} is valid, calibrated, and compliant for production use.",
        "asset_code": asset.asset_code,
        "asset_name": asset.asset_name,
        "applicable_due_date": asset.next_due_date,
        "certificate_status": cert_status,
        "exception_reference": None,
        "last_calibration_date": asset.last_calibration_date,
        "latest_calibration_event_id": latest_event.id if latest_event else None,
        "exception_id": None,
        "is_allowed": True
    }


def record_production_usage(
    db: Session,
    asset_id: int,
    production_line: str,
    operator_id: int,
    usage_timestamp: Optional[datetime] = None,
    usage_end_timestamp: Optional[datetime] = None,
    usage_status: str = "RECORDED",
    actor_id: Optional[int] = None,
    request_id: Optional[str] = None
) -> ProductionUse:
    if usage_timestamp is None:
        usage_timestamp = utcnow()

    # Run deterministic validation
    eval_res = evaluate_asset_production_eligibility(db, asset_id, usage_timestamp)
    asset_code = eval_res["asset_code"]

    usage_code = generate_usage_code(asset_code, usage_timestamp)

    prod_use = ProductionUse(
        usage_code=usage_code,
        asset_id=asset_id,
        production_line=production_line,
        operator_id=operator_id,
        usage_timestamp=usage_timestamp,
        usage_end_timestamp=usage_end_timestamp,
        usage_status=usage_status,
        validation_decision=eval_res["decision"],
        decision_reason=eval_res["reason"],
        calibration_event_id=eval_res["latest_calibration_event_id"],
        exception_id=eval_res["exception_id"],
        created_at=utcnow()
    )
    db.add(prod_use)
    db.flush()

    # If BLOCKED, generate alert & audit
    if eval_res["decision"] == "BLOCKED":
        create_alert(
            db=db,
            asset_id=asset_id,
            alert_type="PROHIBITED_USAGE",
            severity="HIGH",
            message=f"UNAUTHORIZED USAGE ATTEMPT: Operator {operator_id} attempted to use {asset_code} on line '{production_line}'. Reason: {eval_res['reason']}"
        )

        log_audit(
            db=db,
            actor_id=actor_id or operator_id,
            entity_type="ProductionUse",
            entity_id=usage_code,
            action="BLOCKED_PRODUCTION_USE",
            previous_value=None,
            new_value={
                "asset_id": asset_id,
                "asset_code": asset_code,
                "line": production_line,
                "decision": "BLOCKED",
                "reason": eval_res["reason"]
            },
            reason="Blocked production use attempt",
            request_id=request_id
        )
    else:
        log_audit(
            db=db,
            actor_id=actor_id or operator_id,
            entity_type="ProductionUse",
            entity_id=usage_code,
            action="RECORD_PRODUCTION_USE",
            previous_value=None,
            new_value={
                "asset_id": asset_id,
                "asset_code": asset_code,
                "line": production_line,
                "decision": eval_res["decision"]
            },
            reason="Production usage recorded",
            request_id=request_id
        )

    db.commit()
    db.refresh(prod_use)
    return prod_use
