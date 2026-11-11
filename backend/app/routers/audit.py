from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.audit_record import AuditRecord
from app.models.user import User
from app.schemas.audit import AuditRecordOut

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("", response_model=List[AuditRecordOut])
def list_audit_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "admin", "quality_eng"])),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(AuditRecord)
    if entity_type:
        query = query.filter(AuditRecord.entity_type == entity_type)
    if action:
        query = query.filter(AuditRecord.action == action)
    if actor_id:
        query = query.filter(AuditRecord.actor_id == actor_id)
    records = query.order_by(AuditRecord.timestamp.desc()).offset(offset).limit(limit).all()
    results = []
    for r in records:
        out = AuditRecordOut.model_validate(r)
        out.actor_name = r.actor.full_name if r.actor else None
        results.append(out)
    return results
