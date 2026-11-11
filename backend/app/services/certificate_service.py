from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.certificate import Certificate
from app.models.calibration_event import CalibrationEvent
from app.models.asset import Asset
from app.models.alert import Alert
from app.schemas.certificate import CertificateCreate
from app.utils.id_generator import generate_certificate_code
from app.utils.date_utils import utcnow, is_overdue
from app.services.audit_service import log_audit
from app.services.alert_service import create_alert


def create_or_upload_certificate(
    db: Session,
    cert_in: CertificateCreate,
    file_path: Optional[str],
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> Certificate:
    cal_event = db.query(CalibrationEvent).filter(CalibrationEvent.id == cert_in.calibration_event_id).first()
    if not cal_event:
        raise ValueError(f"Calibration Event ID {cert_in.calibration_event_id} does not exist")

    asset = db.query(Asset).filter(Asset.id == cert_in.asset_id).first()
    if not asset:
        raise ValueError(f"Asset ID {cert_in.asset_id} does not exist")

    existing_count = db.query(func.count(Certificate.id)).filter(
        Certificate.calibration_event_id == cal_event.id
    ).scalar() or 0
    if existing_count > 0:
        cert_code = f"{generate_certificate_code(cal_event.calibration_code)}-V{existing_count + 1}"
    else:
        cert_code = generate_certificate_code(cal_event.calibration_code)

    # Check for Asset Mismatch Anomaly:
    # If the provided asset_id does not match cal_event.asset_id, mark INVALID and alert!
    is_mismatch = (cert_in.asset_id != cal_event.asset_id)

    verification_status = "INVALID" if is_mismatch else "PENDING"

    cert = Certificate(
        certificate_code=cert_code,
        calibration_event_id=cal_event.id,
        asset_id=cert_in.asset_id,
        supplier_id=cert_in.supplier_id or cal_event.supplier_id,
        certificate_number=cert_in.certificate_number,
        file_path=file_path,
        issue_date=cert_in.issue_date,
        expiry_date=cert_in.expiry_date,
        verification_status=verification_status,
        created_at=utcnow()
    )
    db.add(cert)
    db.flush()

    if is_mismatch:
        create_alert(
            db=db,
            asset_id=cert_in.asset_id,
            alert_type="INVALID_CERTIFICATE",
            severity="CRITICAL",
            message=f"CRITICAL ANOMALY: Certificate {cert_code} specifies Asset ID {cert_in.asset_id} but belongs to Calibration Event {cal_event.calibration_code} for Asset ID {cal_event.asset_id}. Certificate marked INVALID.",
            related_calibration_id=cal_event.id
        )

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="Certificate",
        entity_id=cert.certificate_code,
        action="CREATE_CERTIFICATE",
        previous_value=None,
        new_value={
            "certificate_code": cert.certificate_code,
            "certificate_number": cert.certificate_number,
            "status": cert.verification_status,
            "asset_mismatch_detected": is_mismatch
        },
        reason="Certificate registered/uploaded",
        request_id=request_id
    )

    db.commit()
    db.refresh(cert)
    return cert


def verify_certificate(
    db: Session,
    cert_id: int,
    decision: str,  # VERIFIED, REJECTED, INVALID
    verifier_name: str,
    actor_id: Optional[int],
    request_id: Optional[str] = None
) -> Certificate:
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise ValueError(f"Certificate ID {cert_id} not found")

    cal_event = db.query(CalibrationEvent).filter(CalibrationEvent.id == cert.calibration_event_id).first()
    asset = db.query(Asset).filter(Asset.id == cert.asset_id).first()

    # Integrity verification: never allow approval if asset mismatch exists
    if cal_event and cert.asset_id != cal_event.asset_id and decision == "VERIFIED":
        decision = "INVALID"
        create_alert(
            db=db,
            asset_id=cert.asset_id,
            alert_type="INVALID_CERTIFICATE",
            severity="CRITICAL",
            message=f"Blocked attempt to verify Certificate {cert.certificate_code} due to cross-asset ownership mismatch."
        )

    prev_status = cert.verification_status
    cert.verification_status = decision
    cert.verified_by = verifier_name
    cert.verified_at = utcnow()
    db.flush()

    if asset and decision == "VERIFIED":
        if not is_overdue(asset.next_due_date) and asset.calibration_status == "PENDING_CERTIFICATE":
            asset.calibration_status = "COMPLIANT"

        # Resolve missing certificate alert
        open_alert = db.query(Alert).filter(
            Alert.asset_id == asset.id,
            Alert.alert_type == "MISSING_CERTIFICATE",
            Alert.status == "OPEN"
        ).first()
        if open_alert:
            open_alert.status = "RESOLVED"
            open_alert.resolved_at = utcnow()

    log_audit(
        db=db,
        actor_id=actor_id,
        entity_type="Certificate",
        entity_id=cert.certificate_code,
        action="VERIFY_CERTIFICATE",
        previous_value={"verification_status": prev_status},
        new_value={"verification_status": decision, "verified_by": verifier_name},
        reason=f"Certificate verification reviewed as {decision}",
        request_id=request_id
    )

    db.commit()
    db.refresh(cert)
    return cert
