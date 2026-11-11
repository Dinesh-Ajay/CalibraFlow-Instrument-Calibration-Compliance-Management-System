from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from app.models.impact_assessment import ImpactAssessment
from app.models.calibration_event import CalibrationEvent
from app.models.production_use import ProductionUse
from app.models.asset import Asset
from app.schemas.corrective_action import ImpactAssessmentCreate, ImpactAssessmentUpdate
from app.utils.id_generator import generate_impact_assessment_code
from app.utils.date_utils import utcnow
from app.services.audit_service import log_audit


def create_impact_assessment(
    db: Session,
    ia_in: ImpactAssessmentCreate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> ImpactAssessment:
    asset = db.query(Asset).filter(Asset.id == ia_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {ia_in.asset_id} does not exist")

    count = db.query(func.count(ImpactAssessment.id)).scalar() or 0
    code = generate_impact_assessment_code(count + 1)

    # Compute affected production uses if time window provided
    affected_count = ia_in.affected_usage_count or 0
    if ia_in.affected_production_start and ia_in.affected_production_end:
        affected_count = db.query(func.count(ProductionUse.id)).filter(
            ProductionUse.asset_id == asset.id,
            ProductionUse.usage_timestamp >= ia_in.affected_production_start,
            ProductionUse.usage_timestamp <= ia_in.affected_production_end
        ).scalar() or 0

    ia = ImpactAssessment(
        assessment_code=code,
        calibration_event_id=ia_in.calibration_event_id,
        asset_id=ia_in.asset_id,
        affected_production_start=ia_in.affected_production_start,
        affected_production_end=ia_in.affected_production_end,
        affected_usage_count=affected_count,
        risk_level=ia_in.risk_level,
        assessment_notes=ia_in.assessment_notes,
        assessed_by=actor_id,
        status="PENDING",
        created_at=utcnow()
    )
    db.add(ia)
    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="ImpactAssessment",
        entity_id=code,
        action="CREATE_IMPACT_ASSESSMENT",
        previous_value=None,
        new_value={"code": code, "asset_code": asset.asset_code, "risk_level": ia.risk_level},
        reason="Impact assessment initiated",
        request_id=request_id
    )

    db.commit()
    db.refresh(ia)
    return ia


def update_impact_assessment(
    db: Session,
    ia_id: int,
    ia_in: ImpactAssessmentUpdate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> ImpactAssessment:
    ia = db.query(ImpactAssessment).filter(ImpactAssessment.id == ia_id).first()
    if not ia:
        raise ValueError(f"Impact Assessment ID {ia_id} not found")

    old_status = ia.status
    update_data = ia_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(ia, field, val)

    if ia_in.status == "COMPLETED" and not ia.assessed_by:
        ia.assessed_by = actor_id

    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="ImpactAssessment",
        entity_id=ia.assessment_code,
        action="UPDATE_IMPACT_ASSESSMENT",
        previous_value={"status": old_status},
        new_value={"status": ia.status, "risk_level": ia.risk_level, "affected_usage_count": ia.affected_usage_count},
        reason="Impact assessment updated",
        request_id=request_id
    )

    db.commit()
    db.refresh(ia)
    return ia
