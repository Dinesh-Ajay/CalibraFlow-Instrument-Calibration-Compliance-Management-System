from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user, get_user_role_names
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertAcknowledgeRequest, AlertOut, AlertResolveRequest
from app.services.alert_service import acknowledge_alert, resolve_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if asset_id:
        query = query.filter(Alert.asset_id == asset_id)
    alerts = query.order_by(Alert.generated_at.desc()).offset(offset).limit(limit).all()
    results = []
    for a in alerts:
        out = AlertOut.model_validate(a)
        out.asset_code = a.asset.asset_code if a.asset else None
        out.asset_name = a.asset.asset_name if a.asset else None
        out.acknowledged_by_name = a.acknowledger.full_name if a.acknowledger else None
        results.append(out)
    return results


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert_endpoint(
    alert_id: int,
    req: Optional[AlertAcknowledgeRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roles = get_user_role_names(current_user)
    # Operators may acknowledge relevant/production alerts where permitted; keep broad authenticated ack but auditable
    alert = acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.commit()
    db.refresh(alert)
    out = AlertOut.model_validate(alert)
    out.asset_code = alert.asset.asset_code if alert.asset else None
    out.asset_name = alert.asset.asset_name if alert.asset else None
    out.acknowledged_by_name = current_user.full_name
    return out


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert_endpoint(
    alert_id: int,
    req: Optional[AlertResolveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Restrict resolve to authorized roles (admin/maintenance/quality/planner as appropriate)
    roles = set(get_user_role_names(current_user))
    if not roles.intersection({"admin", "maint_eng", "quality_eng", "planner"}):
        raise HTTPException(status_code=403, detail="Access forbidden: insufficient permissions")
    alert = resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.commit()
    db.refresh(alert)
    out = AlertOut.model_validate(alert)
    out.asset_code = alert.asset.asset_code if alert.asset else None
    out.asset_name = alert.asset.asset_name if alert.asset else None
    out.acknowledged_by_name = alert.acknowledger.full_name if alert.acknowledger else None
    return out
