from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.impact_assessment import ImpactAssessment
from app.models.user import User
from app.schemas.corrective_action import ImpactAssessmentCreate, ImpactAssessmentOut, ImpactAssessmentUpdate
from app.services.impact_assessment_service import create_impact_assessment, update_impact_assessment

router = APIRouter(prefix="/impact-assessments", tags=["Impact Assessments"])


@router.post("", response_model=ImpactAssessmentOut, status_code=status.HTTP_201_CREATED)
def create_ia_endpoint(
    req: ImpactAssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Quality Engineer", "Administrator", "quality_eng", "admin"])),
):
    try:
        ia = create_impact_assessment(db, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = ImpactAssessmentOut.model_validate(ia)
        out.asset_code = ia.asset.asset_code if ia.asset else None
        out.asset_name = ia.asset.asset_name if ia.asset else None
        out.assessor_name = ia.assessor.full_name if ia.assessor else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ImpactAssessmentOut])
def list_impact_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(ImpactAssessment)
    if status:
        query = query.filter(ImpactAssessment.status == status)
    if asset_id:
        query = query.filter(ImpactAssessment.asset_id == asset_id)
    ias = query.order_by(ImpactAssessment.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for ia in ias:
        out = ImpactAssessmentOut.model_validate(ia)
        out.asset_code = ia.asset.asset_code if ia.asset else None
        out.asset_name = ia.asset.asset_name if ia.asset else None
        out.assessor_name = ia.assessor.full_name if ia.assessor else None
        results.append(out)
    return results


@router.patch("/{assessment_id}", response_model=ImpactAssessmentOut)
def update_ia_endpoint(
    assessment_id: int,
    req: ImpactAssessmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Quality Engineer", "Administrator", "quality_eng", "admin", "Maintenance Engineer", "maint_eng"])),
):
    try:
        ia = update_impact_assessment(db, assessment_id, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = ImpactAssessmentOut.model_validate(ia)
        out.asset_code = ia.asset.asset_code if ia.asset else None
        out.asset_name = ia.asset.asset_name if ia.asset else None
        out.assessor_name = ia.assessor.full_name if ia.assessor else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
