from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.user import User
from app.models.work_order import WorkOrder
from app.schemas.work_order import WorkOrderCreate, WorkOrderOut, WorkOrderStatusUpdate
from app.services.work_order_service import create_work_order, update_work_order_status
from app.utils.date_utils import utcnow

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


@router.post("", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
def create_work_order_endpoint(
    req: WorkOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Production Planner", "Administrator", "maint_eng", "planner", "admin"])),
):
    try:
        # Frontend compatibility mappings
        if req.scheduled_date is None and req.scheduled_start is not None:
            req.scheduled_date = req.scheduled_start
        if req.scheduled_date is None:
            req.scheduled_date = utcnow()
        wo = create_work_order(db, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = WorkOrderOut.model_validate(wo)
        out.asset_code = wo.asset.asset_code if wo.asset else None
        out.asset_name = wo.asset.asset_name if wo.asset else None
        out.assignee_name = wo.assignee.full_name if wo.assignee else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[WorkOrderOut])
def list_work_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(WorkOrder)
    if status:
        query = query.filter(WorkOrder.status == status)
    if priority:
        query = query.filter(WorkOrder.priority == priority)
    if asset_id:
        query = query.filter(WorkOrder.asset_id == asset_id)
    wos = query.order_by(WorkOrder.scheduled_date.desc()).offset(offset).limit(limit).all()
    results = []
    for w in wos:
        out = WorkOrderOut.model_validate(w)
        out.asset_code = w.asset.asset_code if w.asset else None
        out.asset_name = w.asset.asset_name if w.asset else None
        out.assignee_name = w.assignee.full_name if w.assignee else None
        results.append(out)
    return results


@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(work_order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    out = WorkOrderOut.model_validate(wo)
    out.asset_code = wo.asset.asset_code if wo.asset else None
    out.asset_name = wo.asset.asset_name if wo.asset else None
    out.assignee_name = wo.assignee.full_name if wo.assignee else None
    return out


@router.patch("/{work_order_id}/status", response_model=WorkOrderOut)
def update_status_endpoint(
    work_order_id: int,
    req: WorkOrderStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    try:
        if req.actual_downtime_minutes is not None and req.downtime_minutes is None:
            req.downtime_minutes = req.actual_downtime_minutes
        wo = update_work_order_status(db, work_order_id, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = WorkOrderOut.model_validate(wo)
        out.asset_code = wo.asset.asset_code if wo.asset else None
        out.asset_name = wo.asset.asset_name if wo.asset else None
        out.assignee_name = wo.assignee.full_name if wo.assignee else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
