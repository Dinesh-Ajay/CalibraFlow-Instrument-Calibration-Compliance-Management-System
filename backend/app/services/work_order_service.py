from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.work_order import WorkOrder
from app.models.asset import Asset
from app.schemas.work_order import WorkOrderCreate, WorkOrderStatusUpdate
from app.utils.id_generator import generate_work_order_code
from app.utils.date_utils import utcnow
from app.services.audit_service import log_audit


VALID_TRANSITIONS = {
    "OPEN": ["ASSIGNED", "CANCELLED", "ON_HOLD", "IN_PROGRESS"],
    "ASSIGNED": ["IN_PROGRESS", "ON_HOLD", "CANCELLED", "OPEN"],
    "IN_PROGRESS": ["COMPLETED", "ON_HOLD", "CANCELLED"],
    "ON_HOLD": ["IN_PROGRESS", "ASSIGNED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": []
}


def create_work_order(
    db: Session,
    wo_in: WorkOrderCreate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> WorkOrder:
    asset = db.query(Asset).filter(Asset.id == wo_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {wo_in.asset_id} does not exist")

    count = db.query(func.count(WorkOrder.id)).scalar() or 0
    wo_code = generate_work_order_code(count + 1)

    initial_status = "ASSIGNED" if wo_in.assigned_to else "OPEN"

    wo = WorkOrder(
        work_order_code=wo_code,
        asset_id=asset.id,
        calibration_plan_id=wo_in.calibration_plan_id,
        assigned_to=wo_in.assigned_to,
        priority=wo_in.priority,
        work_order_type=wo_in.work_order_type,
        description=wo_in.description,
        scheduled_date=wo_in.scheduled_date,
        status=initial_status,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db.add(wo)
    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="WorkOrder",
        entity_id=wo.work_order_code,
        action="CREATE_WORK_ORDER",
        previous_value=None,
        new_value={
            "work_order_code": wo.work_order_code,
            "asset_code": asset.asset_code,
            "priority": wo.priority,
            "type": wo.work_order_type,
            "status": wo.status
        },
        reason="Work order created",
        request_id=request_id
    )

    db.commit()
    db.refresh(wo)
    return wo


def update_work_order_status(
    db: Session,
    wo_id: int,
    status_in: WorkOrderStatusUpdate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> WorkOrder:
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise ValueError(f"Work Order ID {wo_id} not found")

    old_status = wo.status
    target_status = status_in.status.upper()

    if target_status != old_status and target_status not in VALID_TRANSITIONS.get(old_status, []):
        raise ValueError(f"Invalid transition from {old_status} to {target_status}. Permitted: {', '.join(VALID_TRANSITIONS.get(old_status, []))}")

    wo.status = target_status
    if status_in.assigned_to is not None:
        wo.assigned_to = status_in.assigned_to

    if target_status == "IN_PROGRESS" and not wo.start_time:
        wo.start_time = status_in.start_time or utcnow()

    if target_status == "COMPLETED":
        if not wo.completion_time:
            wo.completion_time = status_in.completion_time or utcnow()
        if status_in.downtime_minutes is not None:
            wo.downtime_minutes = status_in.downtime_minutes
        elif wo.start_time and wo.completion_time:
            diff = (wo.completion_time - wo.start_time).total_seconds() / 60.0
            wo.downtime_minutes = max(0, int(diff))

    wo.updated_at = utcnow()
    db.flush()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="WorkOrder",
        entity_id=wo.work_order_code,
        action="UPDATE_STATUS",
        previous_value={"status": old_status},
        new_value={"status": target_status, "downtime_minutes": wo.downtime_minutes},
        reason=status_in.notes or f"Transitioned from {old_status} to {target_status}",
        request_id=request_id
    )

    db.commit()
    db.refresh(wo)
    return wo
