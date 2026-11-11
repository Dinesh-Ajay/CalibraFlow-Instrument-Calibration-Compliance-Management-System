from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.calibration_event import CalibrationEvent
from app.models.asset import Asset
from app.models.calibration_plan import CalibrationPlan
from app.models.corrective_action import CorrectiveAction
from app.models.impact_assessment import ImpactAssessment
from app.models.alert import Alert
from app.schemas.calibration import CalibrationEventCreate
from app.utils.id_generator import (
    generate_calibration_code,
    generate_corrective_action_code,
    generate_impact_assessment_code
)
from app.utils.date_utils import calculate_next_due_date, utcnow
from app.services.audit_service import log_audit
from app.services.alert_service import create_alert


def compute_measurement_error(measured: float, reference: float) -> Tuple[float, str]:
    """
    Computes measurement error.
    For non-zero reference: percentage_error = abs(measured - reference) / abs(reference) * 100
    For zero reference: absolute_error = abs(measured - reference)
    """
    if abs(reference) < 1e-9:
        return abs(measured - reference), "ABSOLUTE"
    return (abs(measured - reference) / abs(reference)) * 100.0, "PERCENTAGE"


def record_calibration_event(
    db: Session,
    event_in: CalibrationEventCreate,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> CalibrationEvent:
    asset = db.query(Asset).filter(Asset.id == event_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {event_in.asset_id} does not exist")

    # Find active calibration plan for this asset
    plan = None
    if event_in.calibration_plan_id:
        plan = db.query(CalibrationPlan).filter(CalibrationPlan.id == event_in.calibration_plan_id).first()

    if not plan:
        plan = db.query(CalibrationPlan).filter(
            CalibrationPlan.asset_id == asset.id,
            CalibrationPlan.status == "ACTIVE"
        ).first()

    if not plan:
        plan = db.query(CalibrationPlan).filter(
            CalibrationPlan.instrument_type_id == asset.instrument_type_id,
            CalibrationPlan.status == "ACTIVE"
        ).first()

    if not plan:
        raise ValueError(f"No active calibration plan found for Asset {asset.asset_code}")

    tolerance = event_in.tolerance if event_in.tolerance is not None else plan.tolerance
    error_val, error_mode = compute_measurement_error(event_in.measured_value, event_in.reference_value)

    cal_date = event_in.calibration_date or utcnow()
    prev_due = asset.next_due_date

    # Determine result strictly from measured value and tolerance
    if error_val <= tolerance:
        result = "PASS"
        calculated_next_due = calculate_next_due_date(cal_date, plan.calibration_interval_days)
    else:
        result = "FAIL"
        calculated_next_due = prev_due  # Never push next_due_date forward on failure

    # Generate sequential calibration code
    event_count = db.query(func.count(CalibrationEvent.id)).scalar() or 0
    cal_code = generate_calibration_code(asset.asset_code, event_count + 1, cal_date.year)

    cal_event = CalibrationEvent(
        calibration_code=cal_code,
        asset_id=asset.id,
        calibration_plan_id=plan.id,
        supplier_id=event_in.supplier_id,
        work_order_id=event_in.work_order_id,
        calibration_date=cal_date,
        previous_due_date=prev_due,
        calculated_next_due_date=calculated_next_due,
        measured_value=event_in.measured_value,
        reference_value=event_in.reference_value,
        measurement_error=round(error_val, 4),
        tolerance=tolerance,
        result=result,
        calibration_status="COMPLETED",
        performed_by=event_in.performed_by,
        reviewed_by=event_in.reviewed_by,
        certificate_required=event_in.certificate_required if event_in.certificate_required is not None else plan.certificate_required,
        notes=event_in.notes,
        created_at=utcnow()
    )
    db.add(cal_event)
    db.flush()

    if result == "PASS":
        asset.last_calibration_date = cal_date
        asset.next_due_date = calculated_next_due
        asset.operational_status = "ACTIVE"
        if cal_event.certificate_required:
            asset.calibration_status = "PENDING_CERTIFICATE"
            create_alert(
                db=db,
                asset_id=asset.id,
                alert_type="MISSING_CERTIFICATE",
                severity="MEDIUM",
                message=f"Calibration {cal_code} passed. Certificate verification is pending.",
                related_calibration_id=cal_event.id
            )
        else:
            asset.calibration_status = "COMPLIANT"

        # Resolve previous overdue / failed alerts
        open_alerts = db.query(Alert).filter(
            Alert.asset_id == asset.id,
            Alert.alert_type.in_(["OVERDUE_CALIBRATION", "FAILED_CALIBRATION"]),
            Alert.status == "OPEN"
        ).all()
        for al in open_alerts:
            al.status = "RESOLVED"
            al.resolved_at = utcnow()

    else:
        # FAILED calibration
        asset.operational_status = "RESTRICTED"
        asset.calibration_status = "FAILED"

        # Auto-create Corrective Action (CAPA)
        capa_count = db.query(func.count(CorrectiveAction.id)).scalar() or 0
        capa_code = generate_corrective_action_code(capa_count + 1)
        capa = CorrectiveAction(
            corrective_action_code=capa_code,
            calibration_event_id=cal_event.id,
            asset_id=asset.id,
            description=f"Calibration failed for {asset.asset_code}: error {error_val:.2f}% exceeded tolerance {tolerance:.2f}%. Instrument restricted from production.",
            root_cause="Out-of-tolerance measurement during scheduled calibration.",
            status="OPEN",
            opened_at=utcnow()
        )
        db.add(capa)
        db.flush()

        # Auto-create Impact Assessment (IA)
        ia_count = db.query(func.count(ImpactAssessment.id)).scalar() or 0
        ia_code = generate_impact_assessment_code(ia_count + 1)
        ia = ImpactAssessment(
            assessment_code=ia_code,
            calibration_event_id=cal_event.id,
            asset_id=asset.id,
            risk_level="HIGH",
            assessment_notes=f"Automatic impact assessment created following failed calibration {cal_code}. Investigate affected batches and usage between {prev_due.strftime('%Y-%m-%d') if prev_due else 'unknown'} and {cal_date.strftime('%Y-%m-%d')}.",
            status="PENDING",
            created_at=utcnow()
        )
        db.add(ia)
        db.flush()

        # Create Critical Alert
        create_alert(
            db=db,
            asset_id=asset.id,
            alert_type="FAILED_CALIBRATION",
            severity="CRITICAL",
            message=f"CRITICAL: Calibration {cal_code} FAILED. Error {error_val:.2f}% > tolerance {tolerance:.2f}%. Asset {asset.asset_code} restricted. CAPA {capa_code} and Impact Assessment {ia_code} opened.",
            related_calibration_id=cal_event.id
        )

    asset.updated_at = utcnow()
    db.flush()

    # Log audit entry
    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="CalibrationEvent",
        entity_id=cal_code,
        action="EXECUTE_CALIBRATION",
        previous_value={"asset_operational_status": "ACTIVE" if result == "FAIL" else asset.operational_status},
        new_value={
            "result": result,
            "measured_value": cal_event.measured_value,
            "reference_value": cal_event.reference_value,
            "error": cal_event.measurement_error,
            "tolerance": cal_event.tolerance,
            "operational_status": asset.operational_status,
            "calibration_status": asset.calibration_status
        },
        reason=f"Calibration recorded by {cal_event.performed_by}",
        request_id=request_id
    )

    db.commit()
    db.refresh(cal_event)
    return cal_event
