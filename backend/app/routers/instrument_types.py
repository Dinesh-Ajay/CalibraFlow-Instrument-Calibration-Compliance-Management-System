from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.asset import Asset
from app.models.instrument_type import InstrumentType
from app.models.user import User
from app.schemas.instrument_type import InstrumentTypeCreate, InstrumentTypeOut, InstrumentTypeUpdate
from app.services.audit_service import log_audit
from app.utils.date_utils import utcnow

router = APIRouter(prefix="/instrument-types", tags=["Instrument Types"])


@router.get("", response_model=List[InstrumentTypeOut])
def get_instrument_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = Query(default=False),
    search: Optional[str] = None,
):
    q = db.query(InstrumentType)
    if not include_inactive:
        q = q.filter(InstrumentType.is_active == True)  # noqa: E712
    if search:
        s = f"%{search}%"
        q = q.filter((InstrumentType.type_name.ilike(s)) | (InstrumentType.type_code.ilike(s)))
    return q.order_by(InstrumentType.type_name.asc()).all()


@router.post("", response_model=InstrumentTypeOut, status_code=status.HTTP_201_CREATED)
def create_instrument_type(
    req: InstrumentTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    existing = db.query(InstrumentType).filter(InstrumentType.type_code == req.type_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Instrument type code already exists")
    itype = InstrumentType(
        type_code=req.type_code.upper(),
        type_name=req.type_name,
        description=req.description,
        measurement_unit=req.measurement_unit,
        default_calibration_interval_days=req.default_calibration_interval_days,
        default_tolerance=req.default_tolerance,
        is_active=req.is_active,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(itype)
    db.flush()
    log_audit(db, current_user.id, "InstrumentType", itype.type_code, "CREATE", None,
              {"type_code": itype.type_code, "type_name": itype.type_name}, "Instrument type created", get_request_id(request))
    db.commit()
    db.refresh(itype)
    return itype


@router.put("/{type_id}", response_model=InstrumentTypeOut)
def update_instrument_type(
    type_id: int,
    req: InstrumentTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    itype = db.query(InstrumentType).filter(InstrumentType.id == type_id).first()
    if not itype:
        raise HTTPException(status_code=404, detail="Instrument type not found")
    prev = {
        "type_name": itype.type_name, "description": itype.description, "measurement_unit": itype.measurement_unit,
        "default_calibration_interval_days": itype.default_calibration_interval_days,
        "default_tolerance": itype.default_tolerance, "is_active": itype.is_active,
    }
    data = req.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(itype, k, v)
    itype.updated_at = utcnow()
    db.flush()
    log_audit(db, current_user.id, "InstrumentType", itype.type_code, "UPDATE", prev, data, "Instrument type updated", get_request_id(request))
    db.commit()
    db.refresh(itype)
    return itype


@router.post("/{type_id}/deactivate", response_model=InstrumentTypeOut)
def deactivate_instrument_type(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    itype = db.query(InstrumentType).filter(InstrumentType.id == type_id).first()
    if not itype:
        raise HTTPException(status_code=404, detail="Instrument type not found")
    # Prevent "deletion" semantics issues by deactivation only; referenced assets remain valid
    prev = {"is_active": itype.is_active}
    itype.is_active = False
    itype.updated_at = utcnow()
    log_audit(db, current_user.id, "InstrumentType", itype.type_code, "DEACTIVATE", prev, {"is_active": False}, "Instrument type deactivated", get_request_id(request))
    db.commit()
    db.refresh(itype)
    return itype


@router.post("/{type_id}/reactivate", response_model=InstrumentTypeOut)
def reactivate_instrument_type(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "Administrator"])),
):
    itype = db.query(InstrumentType).filter(InstrumentType.id == type_id).first()
    if not itype:
        raise HTTPException(status_code=404, detail="Instrument type not found")
    prev = {"is_active": itype.is_active}
    itype.is_active = True
    itype.updated_at = utcnow()
    log_audit(db, current_user.id, "InstrumentType", itype.type_code, "REACTIVATE", prev, {"is_active": True}, "Instrument type reactivated", get_request_id(request))
    db.commit()
    db.refresh(itype)
    return itype
