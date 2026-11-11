from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.production_use import ProductionUse
from app.models.user import User
from app.schemas.production_use import (
    ProductionUseOut,
    ProductionUseRecordRequest,
    ProductionValidateRequest,
    ProductionValidateResponse,
)
from app.services.production_validation import evaluate_asset_production_eligibility, record_production_usage

router = APIRouter(prefix="/production", tags=["Production Usage"])


@router.post("/validate-usage", response_model=ProductionValidateResponse)
def validate_usage_dry_run(
    req: ProductionValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eval_res = evaluate_asset_production_eligibility(
        db=db,
        asset_id=req.asset_id,
        usage_timestamp=req.usage_timestamp,
    )
    return ProductionValidateResponse(
        asset_id=req.asset_id,
        asset_code=eval_res.get("asset_code", ""),
        asset_name=eval_res.get("asset_name", ""),
        decision=eval_res["decision"],
        decision_reason=eval_res["reason"],
        applicable_due_date=eval_res.get("applicable_due_date"),
        certificate_status=eval_res.get("certificate_status"),
        exception_reference=eval_res.get("exception_reference"),
        last_calibration_date=eval_res.get("last_calibration_date"),
        is_allowed=eval_res.get("is_allowed", False),
    )


@router.post("/usage", response_model=ProductionUseOut, status_code=status.HTTP_201_CREATED)
def record_usage_endpoint(
    req: ProductionUseRecordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Plant Operator", "Administrator", "operator", "admin"])),
):
    usage = record_production_usage(
        db=db,
        asset_id=req.asset_id,
        production_line=req.production_line,
        operator_id=current_user.id,  # never trust client operator identity
        usage_timestamp=req.usage_timestamp,
        usage_end_timestamp=req.usage_end_timestamp,
        usage_status=req.usage_status,
        actor_id=current_user.id,
        request_id=get_request_id(request),
    )
    out = ProductionUseOut.model_validate(usage)
    out.asset_code = usage.asset.asset_code if usage.asset else None
    out.asset_name = usage.asset.asset_name if usage.asset else None
    out.operator_name = usage.operator.full_name if usage.operator else None
    return out


@router.get("/usage", response_model=List[ProductionUseOut])
def list_production_uses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset_id: Optional[int] = None,
    validation_decision: Optional[str] = None,
    production_line: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(ProductionUse)
    if asset_id:
        query = query.filter(ProductionUse.asset_id == asset_id)
    if validation_decision:
        query = query.filter(ProductionUse.validation_decision == validation_decision)
    if production_line:
        query = query.filter(ProductionUse.production_line == production_line)

    uses = query.order_by(ProductionUse.usage_timestamp.desc()).offset(offset).limit(limit).all()
    results = []
    for u in uses:
        out = ProductionUseOut.model_validate(u)
        out.asset_code = u.asset.asset_code if u.asset else None
        out.asset_name = u.asset.asset_name if u.asset else None
        out.operator_name = u.operator.full_name if u.operator else None
        results.append(out)
    return results


@router.get("/usage/{usage_id}", response_model=ProductionUseOut)
def get_production_use(
    usage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage = db.query(ProductionUse).filter(ProductionUse.id == usage_id).first()
    if not usage:
        raise HTTPException(status_code=404, detail="Production usage record not found")
    out = ProductionUseOut.model_validate(usage)
    out.asset_code = usage.asset.asset_code if usage.asset else None
    out.asset_name = usage.asset.asset_name if usage.asset else None
    out.operator_name = usage.operator.full_name if usage.operator else None
    return out
