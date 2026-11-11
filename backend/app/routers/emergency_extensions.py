from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.emergency_extension import EmergencyExtension
from app.models.user import User
from app.schemas.corrective_action import EmergencyExtensionCreate, EmergencyExtensionDecision, EmergencyExtensionOut
from app.services.emergency_extension_service import decide_emergency_extension, request_emergency_extension

router = APIRouter(prefix="/emergency-extensions", tags=["Emergency Extensions"])


@router.post("", response_model=EmergencyExtensionOut, status_code=status.HTTP_201_CREATED)
def request_extension_endpoint(
    req: EmergencyExtensionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Production Planner", "Administrator", "maint_eng", "planner", "admin"])),
):
    try:
        ext = request_emergency_extension(db, req, requested_by=current_user.id, request_id=get_request_id(request))
        out = EmergencyExtensionOut.model_validate(ext)
        out.asset_code = ext.asset.asset_code if ext.asset else None
        out.asset_name = ext.asset.asset_name if ext.asset else None
        out.requester_name = ext.requester.full_name if ext.requester else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[EmergencyExtensionOut])
def list_emergency_extensions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    approval_status: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(EmergencyExtension)
    if approval_status:
        query = query.filter(EmergencyExtension.approval_status == approval_status)
    if asset_id:
        query = query.filter(EmergencyExtension.asset_id == asset_id)
    exts = query.order_by(EmergencyExtension.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for ext in exts:
        out = EmergencyExtensionOut.model_validate(ext)
        out.asset_code = ext.asset.asset_code if ext.asset else None
        out.asset_name = ext.asset.asset_name if ext.asset else None
        out.requester_name = ext.requester.full_name if ext.requester else None
        out.approver_name = ext.approver.full_name if ext.approver else None
        results.append(out)
    return results


@router.patch("/{extension_id}/approve", response_model=EmergencyExtensionOut)
def approve_extension(
    extension_id: int,
    decision_in: Optional[EmergencyExtensionDecision] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Quality Engineer", "Administrator", "quality_eng", "admin"])),
):
    notes = (decision_in.notes if decision_in else None) or "Approved"
    try:
        ext = decide_emergency_extension(db=db, ext_id=extension_id, approve=True, approver_id=current_user.id, notes=notes, request_id=get_request_id(request) if request else None)
        out = EmergencyExtensionOut.model_validate(ext)
        out.asset_code = ext.asset.asset_code if ext.asset else None
        out.asset_name = ext.asset.asset_name if ext.asset else None
        out.requester_name = ext.requester.full_name if ext.requester else None
        out.approver_name = ext.approver.full_name if ext.approver else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{extension_id}/reject", response_model=EmergencyExtensionOut)
def reject_extension(
    extension_id: int,
    decision_in: Optional[EmergencyExtensionDecision] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Quality Engineer", "Administrator", "quality_eng", "admin"])),
):
    notes = (decision_in.notes if decision_in else None) or "Rejected"
    try:
        ext = decide_emergency_extension(db=db, ext_id=extension_id, approve=False, approver_id=current_user.id, notes=notes, request_id=get_request_id(request) if request else None)
        out = EmergencyExtensionOut.model_validate(ext)
        out.asset_code = ext.asset.asset_code if ext.asset else None
        out.asset_name = ext.asset.asset_name if ext.asset else None
        out.requester_name = ext.requester.full_name if ext.requester else None
        out.approver_name = ext.approver.full_name if ext.approver else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
