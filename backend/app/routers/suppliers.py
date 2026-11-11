from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate
from app.services.audit_service import log_audit
from app.utils.date_utils import utcnow
from app.utils.id_generator import generate_supplier_code

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=List[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Supplier).order_by(Supplier.supplier_name.asc()).all()


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    req: SupplierCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "admin", "quality_eng"])),
):
    count = db.query(Supplier).count()
    code = req.supplier_code or generate_supplier_code(count + 1)
    supp = Supplier(
        supplier_code=code,
        supplier_name=req.supplier_name,
        contact_email=req.contact_email,
        contact_phone=req.contact_phone,
        address=req.address,
        accreditation_reference=req.accreditation_reference,
        status=req.status,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(supp)
    db.flush()
    log_audit(db=db, actor_id=current_user.id, entity_type="Supplier", entity_id=code, action="CREATE", previous_value=None, new_value={"code": code, "name": supp.supplier_name}, reason="Supplier registered", request_id=get_request_id(request))
    db.commit()
    db.refresh(supp)
    return supp


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: int,
    req: SupplierUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "admin", "quality_eng"])),
):
    supp = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Supplier not found")
    old_state = {"name": supp.supplier_name, "status": supp.status}
    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(supp, field, val)
    supp.updated_at = utcnow()
    db.flush()
    log_audit(db=db, actor_id=current_user.id, entity_type="Supplier", entity_id=supp.supplier_code, action="UPDATE", previous_value=old_state, new_value=update_data, reason="Supplier details updated", request_id=get_request_id(request))
    db.commit()
    db.refresh(supp)
    return supp
