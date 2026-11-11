from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.emergency_extension import EmergencyExtension
from app.models.asset import Asset
from app.schemas.corrective_action import EmergencyExtensionCreate
from app.utils.id_generator import generate_extension_code
from app.utils.date_utils import utcnow
from app.services.audit_service import log_audit


def request_emergency_extension(
    db: Session,
    ext_in: EmergencyExtensionCreate,
    requested_by: Optional[int],
    request_id: Optional[str] = None
) -> EmergencyExtension:
    asset = db.query(Asset).filter(Asset.id == ext_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {ext_in.asset_id} does not exist")

    original_due = asset.next_due_date or utcnow()
    ext_due = ext_in.extended_due_date
    if original_due.tzinfo is not None and ext_due.tzinfo is None:
        ext_due = ext_due.replace(tzinfo=original_due.tzinfo)
    elif original_due.tzinfo is None and ext_due.tzinfo is not None:
        original_due = original_due.replace(tzinfo=ext_due.tzinfo)

    if ext_due <= original_due:
        raise ValueError("Extended due date must be strictly after the current calibration due date.")

    count = db.query(func.count(EmergencyExtension.id)).scalar() or 0
    code = generate_extension_code(count + 1)

    ext = EmergencyExtension(
        extension_code=code,
        asset_id=asset.id,
        original_due_date=original_due,
        extended_due_date=ext_in.extended_due_date,
        reason=ext_in.reason,
        requested_by=requested_by,
        approval_status="PENDING",
        created_at=utcnow()
    )
    db.add(ext)
    db.flush()

    log_audit(
        db=db,
        actor_id=requested_by,
        entity_type="EmergencyExtension",
        entity_id=code,
        action="REQUEST_EXTENSION",
        previous_value=None,
        new_value={
            "extension_code": code,
            "asset_code": asset.asset_code,
            "original_due_date": str(original_due),
            "extended_due_date": str(ext_in.extended_due_date),
            "status": "PENDING"
        },
        reason=ext_in.reason,
        request_id=request_id
    )

    db.commit()
    db.refresh(ext)
    return ext


def decide_emergency_extension(
    db: Session,
    ext_id: int,
    approve: bool,
    approver_id: int,
    notes: Optional[str] = None,
    request_id: Optional[str] = None
) -> EmergencyExtension:
    ext = db.query(EmergencyExtension).filter(EmergencyExtension.id == ext_id).first()
    if not ext:
        raise ValueError(f"Emergency Extension ID {ext_id} not found")

    if ext.approval_status != "PENDING":
        raise ValueError(f"Extension {ext.extension_code} has already been decided ({ext.approval_status}).")

    decision_status = "APPROVED" if approve else "REJECTED"
    ext.approval_status = decision_status
    ext.approved_by = approver_id
    ext.approved_at = utcnow()
    db.flush()

    log_audit(
        db=db,
        actor_id=approver_id,
        entity_type="EmergencyExtension",
        entity_id=ext.extension_code,
        action=f"DECIDE_EXTENSION_{decision_status}",
        previous_value={"status": "PENDING"},
        new_value={"status": decision_status, "approved_by": approver_id, "notes": notes},
        reason=notes or f"Quality Engineer decision: {decision_status}",
        request_id=request_id
    )

    db.commit()
    db.refresh(ext)
    return ext
