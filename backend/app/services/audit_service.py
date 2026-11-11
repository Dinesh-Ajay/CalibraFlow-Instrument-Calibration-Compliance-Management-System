import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.audit_record import AuditRecord
from app.utils.id_generator import generate_audit_code
from app.utils.date_utils import utcnow


def log_audit(
    db: Session,
    actor_id: Optional[int],
    entity_type: str,
    entity_id: str,
    action: str,
    previous_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None
) -> AuditRecord:
    count = db.query(func.count(AuditRecord.id)).scalar() or 0
    record_code = generate_audit_code(count + 1)

    record = AuditRecord(
        record_code=record_code,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        previous_value=previous_value if isinstance(previous_value, (dict, list)) else ({"value": previous_value} if previous_value is not None else None),
        new_value=new_value if isinstance(new_value, (dict, list)) else ({"value": new_value} if new_value is not None else None),
        reason=reason,
        timestamp=utcnow(),
        request_id=request_id
    )
    db.add(record)
    db.flush()
    return record
