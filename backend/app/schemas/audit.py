from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AuditRecordOut(BaseModel):
    id: int
    record_code: str
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    entity_type: str
    entity_id: str
    action: str
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None

    class Config:
        from_attributes = True
