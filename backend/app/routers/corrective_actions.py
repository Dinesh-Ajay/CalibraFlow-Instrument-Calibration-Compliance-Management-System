from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.corrective_action import CorrectiveAction
from app.models.user import User
from app.schemas.corrective_action import CorrectiveActionCreate, CorrectiveActionOut, CorrectiveActionUpdate
from app.services.corrective_action_service import create_corrective_action, update_corrective_action

router = APIRouter(prefix="/corrective-actions", tags=["Corrective Actions"])


@router.post("", response_model=CorrectiveActionOut, status_code=status.HTTP_201_CREATED)
def create_capa_endpoint(
    req: CorrectiveActionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Quality Engineer", "Administrator", "maint_eng", "quality_eng", "admin"])),
):
    try:
        capa = create_corrective_action(db, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = CorrectiveActionOut.model_validate(capa)
        out.asset_code = capa.asset.asset_code if capa.asset else None
        out.asset_name = capa.asset.asset_name if capa.asset else None
        out.assignee_name = capa.assignee.full_name if capa.assignee else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[CorrectiveActionOut])
def list_corrective_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(CorrectiveAction)
    if status:
        query = query.filter(CorrectiveAction.status == status)
    if asset_id:
        query = query.filter(CorrectiveAction.asset_id == asset_id)
    capas = query.order_by(CorrectiveAction.opened_at.desc()).offset(offset).limit(limit).all()
    results = []
    for c in capas:
        out = CorrectiveActionOut.model_validate(c)
        out.asset_code = c.asset.asset_code if c.asset else None
        out.asset_name = c.asset.asset_name if c.asset else None
        out.assignee_name = c.assignee.full_name if c.assignee else None
        results.append(out)
    return results


@router.patch("/{action_id}", response_model=CorrectiveActionOut)
def update_capa_endpoint(
    action_id: int,
    req: CorrectiveActionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Quality Engineer", "Administrator", "maint_eng", "quality_eng", "admin"])),
):
    try:
        capa = update_corrective_action(db, action_id, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = CorrectiveActionOut.model_validate(capa)
        out.asset_code = capa.asset.asset_code if capa.asset else None
        out.asset_name = capa.asset.asset_name if capa.asset else None
        out.assignee_name = capa.assignee.full_name if capa.assignee else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
