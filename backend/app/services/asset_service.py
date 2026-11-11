from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timezone
from app.models.asset import Asset
from app.models.instrument_type import InstrumentType
from app.models.calibration_plan import CalibrationPlan
from app.models.calibration_event import CalibrationEvent
from app.models.certificate import Certificate
from app.models.work_order import WorkOrder
from app.models.production_use import ProductionUse
from app.models.alert import Alert
from app.models.audit_record import AuditRecord
from app.schemas.asset import AssetCreate, AssetUpdate
from app.utils.id_generator import generate_asset_code, generate_plan_code
from app.utils.date_utils import calculate_next_due_date, is_overdue, utcnow, days_until_due
from app.services.audit_service import log_audit
from app.services.alert_service import create_alert


def register_asset(db: Session, asset_in: AssetCreate, actor_id: Optional[int], request_id: Optional[str] = None) -> Asset:
    itype = db.query(InstrumentType).filter(InstrumentType.id == asset_in.instrument_type_id).first()
    if not itype:
        raise ValueError(f"Instrument Type ID {asset_in.instrument_type_id} does not exist")

    count = db.query(func.count(Asset.id)).scalar() or 0
    asset_code = generate_asset_code(count + 1)

    interval = asset_in.calibration_interval_days or itype.default_calibration_interval_days
    tolerance = asset_in.custom_tolerance if asset_in.custom_tolerance is not None else itype.default_tolerance

    last_cal = asset_in.last_calibration_date
    if last_cal:
        next_due = calculate_next_due_date(last_cal, interval)
    elif asset_in.commissioning_date:
        next_due = calculate_next_due_date(asset_in.commissioning_date, interval)
    else:
        next_due = calculate_next_due_date(utcnow(), interval)

    # Initial calibration status
    if not asset_in.requires_calibration:
        cal_status = "COMPLIANT"
    elif is_overdue(next_due):
        cal_status = "OVERDUE"
    elif days_until_due(next_due) is not None and days_until_due(next_due) <= 14:
        cal_status = "UPCOMING"
    else:
        cal_status = "COMPLIANT"

    asset = Asset(
        asset_code=asset_code,
        asset_name=asset_in.asset_name,
        instrument_type_id=asset_in.instrument_type_id,
        serial_number=asset_in.serial_number,
        manufacturer=asset_in.manufacturer,
        model_number=asset_in.model_number,
        plant_location=asset_in.plant_location,
        production_line=asset_in.production_line,
        installation_date=asset_in.installation_date,
        commissioning_date=asset_in.commissioning_date,
        calibration_interval_days=interval,
        last_calibration_date=last_cal,
        next_due_date=next_due,
        operational_status="ACTIVE",
        calibration_status=cal_status,
        requires_calibration=asset_in.requires_calibration,
        requires_certificate=asset_in.requires_certificate,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db.add(asset)
    db.flush()

    # Create associated CalibrationPlan
    plan_count = db.query(func.count(CalibrationPlan.id)).scalar() or 0
    plan_code = generate_plan_code(plan_count + 1)
    plan = CalibrationPlan(
        plan_code=plan_code,
        asset_id=asset.id,
        instrument_type_id=itype.id,
        calibration_interval_days=interval,
        tolerance=tolerance,
        effective_from=utcnow(),
        due_date_calculation_method="CALENDAR_DAYS",
        grace_period_days=0,
        certificate_required=asset_in.requires_certificate,
        emergency_extension_allowed=True,
        status="ACTIVE"
    )
    db.add(plan)
    db.flush()

    # If overdue upon registration, raise alert
    if cal_status == "OVERDUE":
        create_alert(
            db,
            asset_id=asset.id,
            alert_type="OVERDUE_CALIBRATION",
            severity="HIGH",
            message=f"Instrument {asset.asset_code} registered with overdue calibration due date: {next_due.strftime('%Y-%m-%d')}"
        )

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="Asset",
        entity_id=asset.asset_code,
        action="CREATE",
        previous_value=None,
        new_value={
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "instrument_type": itype.type_name,
            "interval_days": interval,
            "next_due_date": str(next_due),
            "status": asset.operational_status
        },
        reason="Asset registration",
        request_id=request_id
    )

    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset_id: int, asset_in: AssetUpdate, actor_id: Optional[int], request_id: Optional[str] = None) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {asset_id} not found")

    prev_state = {
        "asset_name": asset.asset_name,
        "plant_location": asset.plant_location,
        "production_line": asset.production_line,
        "operational_status": asset.operational_status,
        "calibration_interval_days": asset.calibration_interval_days
    }

    update_data = asset_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(asset, field, val)

    # If interval changed, recalculate next_due_date
    if "calibration_interval_days" in update_data and asset.last_calibration_date:
        asset.next_due_date = calculate_next_due_date(asset.last_calibration_date, asset.calibration_interval_days)

    asset.updated_at = utcnow()
    db.flush()

    new_state = {
        "asset_name": asset.asset_name,
        "plant_location": asset.plant_location,
        "production_line": asset.production_line,
        "operational_status": asset.operational_status,
        "calibration_interval_days": asset.calibration_interval_days
    }

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="Asset",
        entity_id=asset.asset_code,
        action="UPDATE",
        previous_value=prev_state,
        new_value=new_state,
        reason="Permitted asset information update",
        request_id=request_id
    )

    db.commit()
    db.refresh(asset)
    return asset


def get_asset_history(db: Session, asset_id: int) -> Dict[str, Any]:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {asset_id} not found")

    events = db.query(CalibrationEvent).filter(CalibrationEvent.asset_id == asset_id).order_by(CalibrationEvent.calibration_date.desc()).all()
    certificates = db.query(Certificate).filter(Certificate.asset_id == asset_id).order_by(Certificate.issue_date.desc()).all()
    work_orders = db.query(WorkOrder).filter(WorkOrder.asset_id == asset_id).order_by(WorkOrder.scheduled_date.desc()).all()
    production_uses = db.query(ProductionUse).filter(ProductionUse.asset_id == asset_id).order_by(ProductionUse.usage_timestamp.desc()).limit(50).all()
    alerts = db.query(Alert).filter(Alert.asset_id == asset_id).order_by(Alert.generated_at.desc()).all()
    audits = db.query(AuditRecord).filter(AuditRecord.entity_type == "Asset", AuditRecord.entity_id == asset.asset_code).order_by(AuditRecord.timestamp.desc()).all()

    return {
        "asset": asset,
        "calibration_events": events,
        "certificates": certificates,
        "work_orders": work_orders,
        "production_uses": production_uses,
        "alerts": alerts,
        "audit_records": audits
    }
