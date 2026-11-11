from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.asset import Asset
from app.models.work_order import WorkOrder
from app.models.alert import Alert
from app.utils.id_generator import generate_work_order_code
from app.utils.date_utils import utcnow, is_overdue, days_until_due
from app.services.alert_service import create_alert


def scan_and_update_schedules(db: Session, auto_create_work_orders: bool = True) -> Dict[str, Any]:
    assets = db.query(Asset).filter(Asset.requires_calibration == True).all()
    now = utcnow()

    overdue_count = 0
    upcoming_count = 0
    work_orders_created = 0

    for asset in assets:
        if asset.calibration_status == "FAILED" or asset.operational_status == "RESTRICTED":
            continue

        if not asset.next_due_date:
            continue

        days_left = days_until_due(asset.next_due_date, now)

        if is_overdue(asset.next_due_date, now):
            asset.calibration_status = "OVERDUE"
            overdue_count += 1
            create_alert(
                db=db,
                asset_id=asset.id,
                alert_type="OVERDUE_CALIBRATION",
                severity="HIGH",
                message=f"Instrument {asset.asset_code} ({asset.asset_name}) is OVERDUE for calibration. Due date was {asset.next_due_date.strftime('%Y-%m-%d')}."
            )

            if auto_create_work_orders:
                existing_wo = db.query(WorkOrder).filter(
                    WorkOrder.asset_id == asset.id,
                    WorkOrder.work_order_type == "CALIBRATION",
                    WorkOrder.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"])
                ).first()
                if not existing_wo:
                    wo_cnt = db.query(func.count(WorkOrder.id)).scalar() or 0
                    wo_code = generate_work_order_code(wo_cnt + 1)
                    wo = WorkOrder(
                        work_order_code=wo_code,
                        asset_id=asset.id,
                        priority="HIGH",
                        work_order_type="CALIBRATION",
                        description=f"Automated calibration work order for overdue instrument {asset.asset_code}",
                        scheduled_date=now,
                        status="OPEN"
                    )
                    db.add(wo)
                    work_orders_created += 1

        elif days_left is not None and days_left <= 14:
            if asset.calibration_status != "PENDING_CERTIFICATE":
                asset.calibration_status = "UPCOMING"
            upcoming_count += 1
            create_alert(
                db=db,
                asset_id=asset.id,
                alert_type="UPCOMING_CALIBRATION",
                severity="LOW" if days_left > 7 else "MEDIUM",
                message=f"Instrument {asset.asset_code} ({asset.asset_name}) calibration due in {days_left} days on {asset.next_due_date.strftime('%Y-%m-%d')}."
            )

        asset.updated_at = now

    db.commit()
    return {
        "total_scanned": len(assets),
        "overdue_identified": overdue_count,
        "upcoming_identified": upcoming_count,
        "work_orders_created": work_orders_created
    }
