from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.asset import Asset
from app.models.user import User
from app.schemas.alert import AlertOut
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate
from app.schemas.audit import AuditRecordOut
from app.schemas.calibration import CalibrationEventOut
from app.schemas.certificate import CertificateOut
from app.schemas.production_use import ProductionUseOut
from app.schemas.work_order import WorkOrderOut
from app.services.asset_service import get_asset_history, register_asset, update_asset

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(
    req: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    try:
        asset = register_asset(db, req, actor_id=current_user.id, request_id=get_request_id(request))
        res = AssetOut.model_validate(asset)
        res.instrument_type_name = asset.instrument_type.type_name if asset.instrument_type else None
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    operational_status: Optional[str] = None,
    calibration_status: Optional[str] = None,
    production_line: Optional[str] = None,
    instrument_type_id: Optional[int] = None,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Asset)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Asset.asset_code.ilike(search_fmt),
                Asset.asset_name.ilike(search_fmt),
                Asset.serial_number.ilike(search_fmt),
                Asset.manufacturer.ilike(search_fmt),
                Asset.model_number.ilike(search_fmt),
                Asset.production_line.ilike(search_fmt),
                Asset.plant_location.ilike(search_fmt),
            )
        )
    if operational_status:
        query = query.filter(Asset.operational_status == operational_status)
    if calibration_status:
        query = query.filter(Asset.calibration_status == calibration_status)
    if production_line:
        query = query.filter(Asset.production_line == production_line)
    if instrument_type_id:
        query = query.filter(Asset.instrument_type_id == instrument_type_id)

    assets = query.order_by(Asset.id.asc()).offset(offset).limit(limit).all()
    results = []
    for a in assets:
        out = AssetOut.model_validate(a)
        out.instrument_type_name = a.instrument_type.type_name if a.instrument_type else None
        results.append(out)
    return results


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    out = AssetOut.model_validate(asset)
    out.instrument_type_name = asset.instrument_type.type_name if asset.instrument_type else None
    return out


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset_endpoint(
    asset_id: int,
    req: AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Administrator", "maint_eng", "admin"])),
):
    try:
        asset = update_asset(db, asset_id, req, actor_id=current_user.id, request_id=get_request_id(request))
        out = AssetOut.model_validate(asset)
        out.instrument_type_name = asset.instrument_type.type_name if asset.instrument_type else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{asset_id}/history")
def get_asset_history_endpoint(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        history = get_asset_history(db, asset_id)
        asset_obj = history["asset"]
        out_asset = AssetOut.model_validate(asset_obj)
        out_asset.instrument_type_name = asset_obj.instrument_type.type_name if asset_obj.instrument_type else None
        events_out = [CalibrationEventOut.model_validate(e) for e in history["calibration_events"]]
        certs_out = [CertificateOut.model_validate(c) for c in history["certificates"]]
        wos_out = [WorkOrderOut.model_validate(w) for w in history["work_orders"]]
        uses_out = [ProductionUseOut.model_validate(u) for u in history["production_uses"]]
        alerts_out = [AlertOut.model_validate(a) for a in history["alerts"]]
        audits_out = [AuditRecordOut.model_validate(au) for au in history["audit_records"]]
        return {
            "asset": out_asset,
            "calibration_events": events_out,
            "certificates": certs_out,
            "work_orders": wos_out,
            "production_uses": uses_out,
            "alerts": alerts_out,
            "audit_records": audits_out,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
