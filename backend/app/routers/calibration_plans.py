from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.calibration_plan import CalibrationPlan
from app.models.instrument_type import InstrumentType
from app.models.user import User
from app.schemas.asset import CalibrationPlanCreate, CalibrationPlanOut, CalibrationPlanUpdate
from app.services.audit_service import log_audit
from app.utils.date_utils import utcnow
from app.utils.id_generator import generate_plan_code

router = APIRouter(prefix="/calibration-plans", tags=["Calibration Plans"])


def _to_out(plan: CalibrationPlan) -> CalibrationPlanOut:
    out = CalibrationPlanOut.model_validate(plan)
    try:
        out.instrument_type_name = plan.instrument_type.type_name if getattr(plan, "instrument_type", None) else None
    except Exception:
        out.instrument_type_name = None
    # model has no plan_name column; expose code/name-friendly fallback for frontend compatibility
    out.plan_name = getattr(plan, "plan_name", None) or plan.plan_code
    return out


@router.get("", response_model=List[CalibrationPlanOut])
def list_calibration_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset_id: Optional[int] = None,
    instrument_type_id: Optional[int] = None,
):
    query = db.query(CalibrationPlan)
    if asset_id:
        query = query.filter(CalibrationPlan.asset_id == asset_id)
    if instrument_type_id:
        query = query.filter(CalibrationPlan.instrument_type_id == instrument_type_id)
    plans = query.order_by(CalibrationPlan.id.desc()).all()
    return [_to_out(p) for p in plans]


@router.post("", response_model=CalibrationPlanOut, status_code=status.HTTP_201_CREATED)
def create_calibration_plan(
    req: CalibrationPlanCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    # Frontend compatibility mappings
    interval_days = req.calibration_interval_days
    if req.interval_months is not None:
        interval_days = int(req.interval_months) * 30
    tolerance = req.tolerance if req.tolerance is not None else (req.tolerance_percentage if req.tolerance_percentage is not None else 2.0)
    calc_method = req.calculation_method or req.due_date_calculation_method or "CALENDAR_DAYS"

    if not db.query(InstrumentType).filter(InstrumentType.id == req.instrument_type_id, InstrumentType.is_active == True).first():  # noqa: E712
        raise HTTPException(status_code=400, detail="Invalid or inactive instrument type")

    count = db.query(CalibrationPlan).count()
    plan_code = req.plan_code or generate_plan_code(count + 1)
    if db.query(CalibrationPlan).filter(CalibrationPlan.plan_code == plan_code).first():
        raise HTTPException(status_code=400, detail="Plan code already exists")

    # If creating asset-specific plan, supersede existing active plan for that asset
    if req.asset_id:
        active_plan = db.query(CalibrationPlan).filter(
            CalibrationPlan.asset_id == req.asset_id,
            CalibrationPlan.status == "ACTIVE",
        ).first()
        if active_plan:
            active_plan.status = "SUPERSEDED"
            active_plan.effective_until = utcnow()
            active_plan.updated_at = utcnow()

    plan = CalibrationPlan(
        plan_code=plan_code,
        asset_id=req.asset_id,
        instrument_type_id=req.instrument_type_id,
        calibration_interval_days=int(interval_days),
        tolerance=float(tolerance),
        effective_from=req.effective_from or utcnow(),
        effective_until=req.effective_until,
        due_date_calculation_method=calc_method,
        grace_period_days=req.grace_period_days or 0,
        certificate_required=req.certificate_required,
        emergency_extension_allowed=req.emergency_extension_allowed,
        status="ACTIVE",
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(plan)
    db.flush()

    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="CalibrationPlan",
        entity_id=plan.plan_code,
        action="CREATE",
        previous_value=None,
        new_value={
            "plan_code": plan.plan_code,
            "instrument_type_id": plan.instrument_type_id,
            "interval_days": plan.calibration_interval_days,
            "tolerance": plan.tolerance,
            "calculation_method": plan.due_date_calculation_method,
        },
        reason="Calibration plan created",
        request_id=get_request_id(request),
    )
    db.commit()
    db.refresh(plan)
    return _to_out(plan)


@router.put("/{plan_id}", response_model=CalibrationPlanOut)
def update_calibration_plan(
    plan_id: int,
    req: CalibrationPlanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    plan = db.query(CalibrationPlan).filter(CalibrationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Calibration plan not found")

    old_state = {
        "interval": plan.calibration_interval_days,
        "tolerance": plan.tolerance,
        "status": plan.status,
        "effective_until": str(plan.effective_until) if plan.effective_until else None,
    }
    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(plan, field, val)
    plan.updated_at = utcnow()
    db.flush()

    log_audit(
        db=db,
        actor_id=current_user.id,
        entity_type="CalibrationPlan",
        entity_id=plan.plan_code,
        action="UPDATE",
        previous_value=old_state,
        new_value=update_data,
        reason="Calibration plan updated",
        request_id=get_request_id(request),
    )
    db.commit()
    db.refresh(plan)
    return _to_out(plan)
