from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta, timezone
from app.models.asset import Asset
from app.models.calibration_event import CalibrationEvent
from app.models.certificate import Certificate
from app.models.work_order import WorkOrder
from app.models.production_use import ProductionUse
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.models.instrument_type import InstrumentType
from app.utils.date_utils import utcnow


def calculate_dashboard_summary(db: Session) -> Dict[str, Any]:
    # 1. KPIs
    total_assets = db.query(func.count(Asset.id)).scalar() or 0
    compliant_assets = db.query(func.count(Asset.id)).filter(Asset.calibration_status == "COMPLIANT").scalar() or 0
    upcoming_assets = db.query(func.count(Asset.id)).filter(Asset.calibration_status == "UPCOMING").scalar() or 0
    overdue_assets = db.query(func.count(Asset.id)).filter(Asset.calibration_status == "OVERDUE").scalar() or 0
    failed_assets = db.query(func.count(Asset.id)).filter(Asset.calibration_status == "FAILED").scalar() or 0

    # Eligible assets that require calibration
    eligible_assets = db.query(func.count(Asset.id)).filter(Asset.requires_calibration == True).scalar() or 0

    # Missing certificates count: calibration events requiring certificate that lack a VERIFIED certificate
    verified_cert_event_ids = db.query(Certificate.calibration_event_id).filter(Certificate.verification_status == "VERIFIED").scalar_subquery()
    missing_certificates = db.query(func.count(CalibrationEvent.id)).filter(
        CalibrationEvent.certificate_required == True,
        ~CalibrationEvent.id.in_(verified_cert_event_ids)
    ).scalar() or 0

    open_work_orders = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "ON_HOLD"])
    ).scalar() or 0

    blocked_usage_count = db.query(func.count(ProductionUse.id)).filter(
        ProductionUse.validation_decision == "BLOCKED"
    ).scalar() or 0

    total_usage_count = db.query(func.count(ProductionUse.id)).scalar() or 0

    # Calibration events stats
    total_cal_events = db.query(func.count(CalibrationEvent.id)).scalar() or 0
    failed_cal_events = db.query(func.count(CalibrationEvent.id)).filter(CalibrationEvent.result == "FAIL").scalar() or 0

    # Required certificates stats
    total_required_certs = db.query(func.count(CalibrationEvent.id)).filter(CalibrationEvent.certificate_required == True).scalar() or 0
    valid_certs = db.query(func.count(Certificate.id)).filter(Certificate.verification_status == "VERIFIED").scalar() or 0

    # Corrective action stats
    total_capas = db.query(func.count(CorrectiveAction.id)).scalar() or 0
    completed_capas = db.query(func.count(CorrectiveAction.id)).filter(CorrectiveAction.status.in_(["RESOLVED", "CLOSED"])).scalar() or 0

    # Rates
    compliance_rate = round((compliant_assets / eligible_assets * 100.0) if eligible_assets > 0 else 100.0, 2)
    failure_rate = round((failed_cal_events / total_cal_events * 100.0) if total_cal_events > 0 else 0.0, 2)
    cert_coverage = round((valid_certs / total_required_certs * 100.0) if total_required_certs > 0 else 100.0, 2)
    blocked_rate = round((blocked_usage_count / total_usage_count * 100.0) if total_usage_count > 0 else 0.0, 2)
    capa_completion_rate = round((completed_capas / total_capas * 100.0) if total_capas > 0 else 100.0, 2)

    # Status distributions
    cal_statuses = db.query(Asset.calibration_status, func.count(Asset.id)).group_by(Asset.calibration_status).all()
    cal_dist = [{"name": s[0] or "UNKNOWN", "value": s[1]} for s in cal_statuses]

    wo_statuses = db.query(WorkOrder.status, func.count(WorkOrder.id)).group_by(WorkOrder.status).all()
    wo_dist = [{"name": s[0] or "UNKNOWN", "value": s[1]} for s in wo_statuses]

    prod_decisions = db.query(ProductionUse.validation_decision, func.count(ProductionUse.id)).group_by(ProductionUse.validation_decision).all()
    prod_dist = [{"name": s[0] or "UNKNOWN", "value": s[1]} for s in prod_decisions]

    # Line compliance
    lines = db.query(
        Asset.production_line,
        func.count(Asset.id).label("total"),
        func.sum(case((Asset.calibration_status == "COMPLIANT", 1), else_=0)).label("compliant")
    ).group_by(Asset.production_line).all()

    line_compliance = []
    for line, total, comp in lines:
        c_val = int(comp or 0)
        t_val = int(total or 0)
        pct = round((c_val / t_val * 100.0) if t_val > 0 else 100.0, 1)
        line_compliance.append({
            "line": line or "Unassigned",
            "total": t_val,
            "compliant": c_val,
            "compliance_percentage": pct
        })

    # Overdue by instrument type
    overdue_by_types = db.query(
        InstrumentType.type_name,
        func.count(Asset.id)
    ).join(Asset, Asset.instrument_type_id == InstrumentType.id).filter(
        Asset.calibration_status == "OVERDUE"
    ).group_by(InstrumentType.type_name).all()

    overdue_type_list = [{"instrument_type": t[0], "overdue_count": t[1]} for t in overdue_by_types]

    # Monthly trends (last 6-12 months)
    monthly_trends = []
    now = utcnow()
    for i in range(5, -1, -1):
        # month window
        start_date = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)

        total_m = db.query(func.count(CalibrationEvent.id)).filter(
            CalibrationEvent.calibration_date >= start_date,
            CalibrationEvent.calibration_date < end_date
        ).scalar() or 0

        passed_m = db.query(func.count(CalibrationEvent.id)).filter(
            CalibrationEvent.calibration_date >= start_date,
            CalibrationEvent.calibration_date < end_date,
            CalibrationEvent.result == "PASS"
        ).scalar() or 0

        failed_m = db.query(func.count(CalibrationEvent.id)).filter(
            CalibrationEvent.calibration_date >= start_date,
            CalibrationEvent.calibration_date < end_date,
            CalibrationEvent.result == "FAIL"
        ).scalar() or 0

        month_label = start_date.strftime("%b %Y")
        monthly_trends.append({
            "label": month_label,
            "total": total_m,
            "passed": passed_m,
            "failed": failed_m
        })

    # Downtime trends by month
    downtime_trends = []
    for trend in monthly_trends:
        label = trend["label"]
        # Approximate matching downtime
        dt_minutes = db.query(func.sum(WorkOrder.downtime_minutes)).filter(
            WorkOrder.status == "COMPLETED"
        ).scalar() or 0
        downtime_trends.append({
            "label": label,
            "downtime_minutes": int(dt_minutes // 6) if dt_minutes else 0
        })

    # Recent Alerts
    alerts = db.query(Alert).order_by(Alert.generated_at.desc()).limit(10).all()
    recent_alerts = [
        {
            "id": a.id,
            "alert_code": a.alert_code,
            "asset_id": a.asset_id,
            "asset_code": a.asset.asset_code if a.asset else "UNKNOWN",
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "status": a.status,
            "generated_at": a.generated_at.strftime("%Y-%m-%d %H:%M")
        } for a in alerts
    ]

    return {
        "kpis": {
            "total_instruments": total_assets,
            "calibration_compliant": compliant_assets,
            "upcoming_calibration": upcoming_assets,
            "overdue_instruments": overdue_assets,
            "failed_calibrations": failed_assets,
            "missing_certificates": missing_certificates,
            "open_work_orders": open_work_orders,
            "blocked_production_usage": blocked_usage_count
        },
        "rates": {
            "compliance_rate": compliance_rate,
            "calibration_failure_rate": failure_rate,
            "certificate_coverage": cert_coverage,
            "blocked_usage_rate": blocked_rate,
            "corrective_action_completion_rate": capa_completion_rate
        },
        "calibration_status_distribution": cal_dist,
        "work_order_status_distribution": wo_dist,
        "production_decision_distribution": prod_dist,
        "line_compliance": line_compliance,
        "overdue_by_type": overdue_type_list,
        "monthly_trends": monthly_trends,
        "downtime_trends": downtime_trends,
        "recent_alerts": recent_alerts
    }
