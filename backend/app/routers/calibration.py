from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.asset import Asset
from app.models.calibration_event import CalibrationEvent
from app.models.user import User
from app.schemas.calibration import CalibrationEventCreate, CalibrationEventOut, CalibrationScheduleRequest
from app.schemas.work_order import WorkOrderCreate
from app.services.calibration_service import record_calibration_event
from app.services.scheduling_service import scan_and_update_schedules
from app.services.work_order_service import create_work_order
from app.utils.date_utils import utcnow

router = APIRouter(prefix="/calibration", tags=["Calibration"])


@router.post("/events", response_model=CalibrationEventOut, status_code=status.HTTP_201_CREATED)
def record_event_endpoint(
    req: CalibrationEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    try:
        event = record_calibration_event(db=db, event_in=req, actor_id=current_user.id, request_id=get_request_id(request))
        out = CalibrationEventOut.model_validate(event)
        out.asset_code = event.asset.asset_code if event.asset else None
        out.asset_name = event.asset.asset_name if event.asset else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events", response_model=List[CalibrationEventOut])
def list_calibration_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "Maintenance Engineer", "Production Planner", "admin", "quality_eng", "maint_eng", "planner"])),
    asset_id: Optional[int] = None,
    result: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(CalibrationEvent)
    if asset_id:
        query = query.filter(CalibrationEvent.asset_id == asset_id)
    if result:
        query = query.filter(CalibrationEvent.result == result)
    events = query.order_by(CalibrationEvent.calibration_date.desc()).offset(offset).limit(limit).all()
    results = []
    for e in events:
        out = CalibrationEventOut.model_validate(e)
        out.asset_code = e.asset.asset_code if e.asset else None
        out.asset_name = e.asset.asset_name if e.asset else None
        results.append(out)
    return results


@router.get("/events/{event_id}", response_model=CalibrationEventOut)
def get_calibration_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "Maintenance Engineer", "Production Planner", "admin", "quality_eng", "maint_eng", "planner"])),
):
    event = db.query(CalibrationEvent).filter(CalibrationEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Calibration event not found")
    out = CalibrationEventOut.model_validate(event)
    out.asset_code = event.asset.asset_code if event.asset else None
    out.asset_name = event.asset.asset_name if event.asset else None
    return out


@router.post("/schedule")
def schedule_calibration_endpoint(
    req: CalibrationScheduleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Production Planner", "Administrator", "maint_eng", "planner", "admin"])),
):
    asset = db.query(Asset).filter(Asset.id == req.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    wo_create = WorkOrderCreate(
        asset_id=asset.id,
        assigned_to=req.assigned_to,
        priority=req.priority,
        work_order_type="CALIBRATION",
        description=req.notes or f"Scheduled calibration for {asset.asset_code}",
        scheduled_date=req.scheduled_date or asset.next_due_date or utcnow(),
    )
    wo = create_work_order(db, wo_create, actor_id=current_user.id, request_id=get_request_id(request))
    return {"message": "Calibration work order scheduled successfully", "work_order_code": wo.work_order_code, "id": wo.id}


@router.get("/upcoming")
def get_upcoming_calibrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assets = db.query(Asset).filter(Asset.calibration_status == "UPCOMING").all()
    return [{"id": a.id, "asset_code": a.asset_code, "asset_name": a.asset_name, "production_line": a.production_line, "last_calibration_date": a.last_calibration_date, "next_due_date": a.next_due_date, "operational_status": a.operational_status} for a in assets]


@router.get("/overdue")
def get_overdue_calibrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assets = db.query(Asset).filter(Asset.calibration_status == "OVERDUE").all()
    return [{"id": a.id, "asset_code": a.asset_code, "asset_name": a.asset_name, "production_line": a.production_line, "last_calibration_date": a.last_calibration_date, "next_due_date": a.next_due_date, "operational_status": a.operational_status} for a in assets]


@router.post("/scan-schedules")
def trigger_scan_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Production Planner", "Administrator", "maint_eng", "planner", "admin"])),
):
    return scan_and_update_schedules(db, auto_create_work_orders=True)
