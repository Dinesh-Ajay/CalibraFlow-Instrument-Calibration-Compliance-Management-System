from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alert import Alert
from app.utils.id_generator import generate_alert_code
from app.utils.date_utils import utcnow
from app.services.notification_service import send_email_notification


def create_alert(
    db: Session,
    asset_id: int,
    alert_type: str,
    severity: str,
    message: str,
    related_calibration_id: Optional[int] = None,
    related_work_order_id: Optional[int] = None
) -> Alert:
    # Check if identical active alert already exists to prevent duplicate alert storms
    existing = db.query(Alert).filter(
        Alert.asset_id == asset_id,
        Alert.alert_type == alert_type,
        Alert.status == "OPEN"
    ).first()

    if existing:
        return existing

    count = db.query(func.count(Alert.id)).scalar() or 0
    alert_code = generate_alert_code(count + 1)

    alert = Alert(
        alert_code=alert_code,
        asset_id=asset_id,
        related_calibration_id=related_calibration_id,
        related_work_order_id=related_work_order_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        status="OPEN",
        generated_at=utcnow()
    )
    db.add(alert)
    db.flush()

    # Optional notification hook
    if severity in ["HIGH", "CRITICAL"]:
        send_email_notification(
            to_email="quality-team@calibraflow.internal",
            subject=f"[{severity}] CalibraFlow Alert: {alert_type}",
            body=f"<p>Asset #{asset_id}: {message}</p>"
        )

    return alert


def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = user_id
    alert.acknowledged_at = utcnow()
    db.flush()
    return alert


def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "RESOLVED"
    alert.resolved_at = utcnow()
    db.flush()
    return alert
