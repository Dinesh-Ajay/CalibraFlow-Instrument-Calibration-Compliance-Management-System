from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.corrective_action import CorrectiveAction
from app.models.asset import Asset
from app.schemas.corrective_action import CorrectiveActionCreate, CorrectiveActionUpdate
from app.utils.id_generator import generate_corrective_action_code
from app.utils.date_utils import utcnow
from app.services.audit_service import log_audit


def create_corrective_action(
    db: Session,
    capa_in: CorrectiveActionCreate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> CorrectiveAction:
    asset = db.query(Asset).filter(Asset.id == capa_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {capa_in.asset_id} does not exist")

    count = db.query(func.count(CorrectiveAction.id)).scalar() or 0
    code = generate_corrective_action_code(count + 1)

    capa = CorrectiveAction(
        corrective_action_code=code,
        calibration_event_id=capa_in.calibration_event_id,
        asset_id=capa_in.asset_id,
        description=capa_in.description,
        assigned_to=capa_in.assigned_to,
        root_cause=capa_in.root_cause,
        status="OPEN",
        opened_at=utcnow()
    )
    db.add(capa)
    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="CorrectiveAction",
        entity_id=code,
        action="CREATE_CAPA",
        previous_value=None,
        new_value={"code": code, "asset_code": asset.asset_code, "status": "OPEN"},
        reason="Corrective action initiated",
        request_id=request_id
    )

    db.commit()
    db.refresh(capa)
    return capa


def update_corrective_action(
    db: Session,
    capa_id: int,
    capa_in: CorrectiveActionUpdate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> CorrectiveAction:
    capa = db.query(CorrectiveAction).filter(CorrectiveAction.id == capa_id).first()
    if not capa:
        raise ValueError(f"Corrective Action ID {capa_id} not found")

    old_status = capa.status
    update_data = capa_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(capa, field, val)

    if capa.status in ["RESOLVED", "CLOSED"] and not capa.closed_at:
        capa.closed_at = utcnow()

    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="CorrectiveAction",
        entity_id=capa.corrective_action_code,
        action="UPDATE_CAPA",
        previous_value={"status": old_status},
        new_value={"status": capa.status, "action_taken": capa.action_taken},
        reason="Corrective action updated",
        request_id=request_id
    )

    db.commit()
    db.refresh(capa)
    return capa
