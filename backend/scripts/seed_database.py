import os
import sys
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models.user import User, Role, UserRole
from app.models.instrument_type import InstrumentType
from app.models.supplier import Supplier
from app.models.asset import Asset
from app.models.calibration_plan import CalibrationPlan
from app.models.calibration_event import CalibrationEvent
from app.models.certificate import Certificate
from app.models.work_order import WorkOrder
from app.models.production_use import ProductionUse
from app.models.alert import Alert
from app.models.audit_record import AuditRecord
from app.models.corrective_action import CorrectiveAction
from app.models.impact_assessment import ImpactAssessment
from app.models.emergency_extension import EmergencyExtension
from app.services.bootstrap_service import bootstrap_required_access
from app.utils.date_utils import utcnow


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
    except Exception:
        return None


def parse_bool(b_str):
    if isinstance(b_str, bool):
        return b_str
    return str(b_str).lower() in ["true", "1", "yes"]


def _get_or_create_roles_compat(db):
    # Ensure canonical roles exist via bootstrap and also keep legacy display names usable
    bootstrap_required_access(db, actor_id=None, request_id="seed-bootstrap")
    role_map = {}
    for r in db.query(Role).all():
        role_map[r.role_name] = r.id
    return role_map


def seed_database(data_dir: str = "data"):
    print("=== Seeding CalibraFlow database (safe/idempotent where possible) ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Ensure required roles and required initial accounts (no demo admin/admin123 accounts)
        bootstrap_required_access(db, actor_id=None, request_id="seed-bootstrap")
        db.commit()

        # Determine an admin user id for historical seeded records (prefer Ajay)
        admin_user = db.query(User).filter(User.username == "Ajay").first() or db.query(User).first()
        admin_user_id = admin_user.id if admin_user else 1

        csv_dir = os.path.join(data_dir, "synthetic")
        if not os.path.exists(csv_dir):
            print(f"Directory {csv_dir} does not exist. Skipping synthetic CSV import.")
            return

        def read_records(filename):
            path = os.path.join(csv_dir, filename)
            if not os.path.exists(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))

        # 0. Instrument Types
        itypes_data = read_records("instrument_types.csv")
        itype_map = {}
        for it in itypes_data:
            t = db.query(InstrumentType).filter(InstrumentType.type_code == it.get("type_code")).first()
            if not t and it.get("type_name"):
                t = db.query(InstrumentType).filter(InstrumentType.type_name == it.get("type_name")).first()
            if not t:
                t = InstrumentType(
                    type_code=it.get("type_code") or f"IT-{it.get('id','0')}",
                    type_name=it.get("type_name") or "Instrument Type",
                    description=it.get("description", f"{it.get('type_name','Instrument')} instruments"),
                    measurement_unit=it.get("measurement_unit", "unit"),
                    default_calibration_interval_days=int(it.get("default_calibration_interval_days", 90)),
                    default_tolerance=float(it.get("default_tolerance", 2.0)),
                    is_active=True,
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(t)
                db.flush()
            if it.get("id"):
                itype_map[it["id"]] = t.id
            if it.get("type_code"):
                itype_map[it["type_code"]] = t.id
            itype_map[str(t.id)] = t.id
        db.commit()

        # 1. Suppliers
        suppliers_data = read_records("suppliers.csv")
        supplier_map = {}
        for s in suppliers_data:
            supp = db.query(Supplier).filter(Supplier.supplier_code == s.get("supplier_code")).first()
            if not supp:
                supp = Supplier(
                    supplier_code=s.get("supplier_code") or f"SUP-{s.get('id','0')}",
                    supplier_name=s.get("supplier_name") or "Supplier",
                    contact_email=s.get("contact_email"),
                    contact_phone=s.get("contact_phone"),
                    address=s.get("address"),
                    accreditation_reference=s.get("accreditation_reference"),
                    status=s.get("status", "ACTIVE"),
                )
                db.add(supp)
                db.flush()
            if s.get("id"):
                supplier_map[s["id"]] = supp.id
            if s.get("supplier_code"):
                supplier_map[s["supplier_code"]] = supp.id
        db.commit()

        # 2. Assets
        assets_data = read_records("assets.csv")
        asset_map = {}
        for a in assets_data:
            ass = db.query(Asset).filter(Asset.asset_code == a.get("asset_code")).first() if a.get("asset_code") else None
            if not ass:
                ass = Asset(
                    asset_code=a.get("asset_code") or f"AST-{a.get('id','0')}",
                    asset_name=a.get("asset_name") or "Asset",
                    instrument_type_id=itype_map.get(a.get("instrument_type_id"), list(itype_map.values())[0] if itype_map else 1),
                    serial_number=a.get("serial_number") or f"SN-{a.get('id','0')}",
                    manufacturer=a.get("manufacturer") or "Unknown",
                    model_number=a.get("model_number") or "Unknown",
                    plant_location=a.get("plant_location") or "Plant",
                    production_line=a.get("production_line") or "Line 1",
                    installation_date=parse_dt(a.get("installation_date")),
                    commissioning_date=parse_dt(a.get("commissioning_date")),
                    calibration_interval_days=int(a.get("calibration_interval_days", 90)),
                    last_calibration_date=parse_dt(a.get("last_calibration_date")),
                    next_due_date=parse_dt(a.get("next_due_date")),
                    operational_status=a.get("operational_status", "ACTIVE"),
                    calibration_status=a.get("calibration_status", "COMPLIANT"),
                    requires_calibration=parse_bool(a.get("requires_calibration", True)),
                    requires_certificate=parse_bool(a.get("requires_certificate", True)),
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(ass)
                db.flush()
            if a.get("id"):
                asset_map[a["id"]] = ass.id
            if a.get("asset_code"):
                asset_map[a["asset_code"]] = ass.id
        db.commit()

        # 3. Calibration Plans
        plans_data = read_records("calibration_plans.csv")
        plan_map = {}
        for p in plans_data:
            plan = db.query(CalibrationPlan).filter(CalibrationPlan.plan_code == p.get("plan_code")).first() if p.get("plan_code") else None
            if not plan:
                plan = CalibrationPlan(
                    plan_code=p.get("plan_code") or f"PLN-{p.get('id','0')}",
                    asset_id=asset_map.get(p.get("asset_id")),
                    instrument_type_id=itype_map.get(p.get("instrument_type_id"), list(itype_map.values())[0] if itype_map else 1),
                    calibration_interval_days=int(p.get("calibration_interval_days", 90)),
                    tolerance=float(p.get("tolerance", 2.0)),
                    effective_from=parse_dt(p.get("effective_from")) or utcnow(),
                    effective_until=parse_dt(p.get("effective_until")),
                    due_date_calculation_method=p.get("due_date_calculation_method", "CALENDAR_DAYS"),
                    grace_period_days=int(p.get("grace_period_days", 0)),
                    certificate_required=parse_bool(p.get("certificate_required", True)),
                    emergency_extension_allowed=parse_bool(p.get("emergency_extension_allowed", True)),
                    status=p.get("status", "ACTIVE"),
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(plan)
                db.flush()
            if p.get("id"):
                plan_map[p["id"]] = plan.id
            if p.get("plan_code"):
                plan_map[p["plan_code"]] = plan.id
        db.commit()

        # 4-12: preserve existing historical import behavior where records don't exist
        events_data = read_records("calibration_events.csv")
        event_map = {}
        for e in events_data:
            ev = db.query(CalibrationEvent).filter(CalibrationEvent.calibration_code == e.get("calibration_code")).first() if e.get("calibration_code") else None
            if not ev:
                aid = asset_map.get(e.get("asset_id"))
                pid = plan_map.get(e.get("calibration_plan_id")) or (list(plan_map.values())[0] if plan_map else None)
                if not aid or not pid:
                    continue
                ev = CalibrationEvent(
                    calibration_code=e.get("calibration_code") or f"CAL-{e.get('id','0')}",
                    asset_id=aid,
                    calibration_plan_id=pid,
                    supplier_id=supplier_map.get(e.get("supplier_id")),
                    calibration_date=parse_dt(e.get("calibration_date")) or utcnow(),
                    previous_due_date=parse_dt(e.get("previous_due_date")),
                    calculated_next_due_date=parse_dt(e.get("calculated_next_due_date")),
                    measured_value=float(e.get("measured_value", 0)),
                    reference_value=float(e.get("reference_value", 0)),
                    measurement_error=float(e.get("measurement_error", 0)),
                    tolerance=float(e.get("tolerance", 0)),
                    result=e.get("result", "PASS"),
                    calibration_status=e.get("calibration_status", "COMPLETED"),
                    performed_by=e.get("performed_by", "system"),
                    reviewed_by=e.get("reviewed_by"),
                    certificate_required=parse_bool(e.get("certificate_required", True)),
                    notes=e.get("notes"),
                    created_at=utcnow(),
                )
                db.add(ev)
                db.flush()
            if e.get("id"):
                event_map[e["id"]] = ev.id
            if e.get("calibration_code"):
                event_map[e["calibration_code"]] = ev.id
        db.commit()

        for c in read_records("certificates.csv"):
            if c.get("certificate_code") and db.query(Certificate).filter(Certificate.certificate_code == c["certificate_code"]).first():
                continue
            cal_id = event_map.get(c.get("calibration_event_id"))
            ass_id = asset_map.get(c.get("asset_id"))
            if not cal_id or not ass_id:
                continue
            db.add(Certificate(
                certificate_code=c.get("certificate_code") or f"CERT-{c.get('id','0')}",
                calibration_event_id=cal_id,
                asset_id=ass_id,
                supplier_id=supplier_map.get(c.get("supplier_id")),
                certificate_number=c.get("certificate_number") or f"CNUM-{c.get('id','0')}",
                issue_date=parse_dt(c.get("issue_date")) or utcnow(),
                expiry_date=parse_dt(c.get("expiry_date")) or utcnow(),
                verification_status=c.get("verification_status", "PENDING"),
                verified_by=c.get("verified_by"),
                verified_at=parse_dt(c.get("verified_at")),
                created_at=utcnow(),
                updated_at=utcnow(),
            ))
        db.commit()

        for w in read_records("work_orders.csv"):
            if w.get("work_order_code") and db.query(WorkOrder).filter(WorkOrder.work_order_code == w["work_order_code"]).first():
                continue
            ass_id = asset_map.get(w.get("asset_id"))
            if not ass_id:
                continue
            db.add(WorkOrder(
                work_order_code=w.get("work_order_code") or f"WO-{w.get('id','0')}",
                asset_id=ass_id,
                calibration_plan_id=plan_map.get(w.get("calibration_plan_id")),
                assigned_to=admin_user_id,
                priority=w.get("priority", "MEDIUM"),
                work_order_type=w.get("work_order_type", "CALIBRATION"),
                description=w.get("description"),
                scheduled_date=parse_dt(w.get("scheduled_date")),
                start_time=parse_dt(w.get("start_time")),
                completion_time=parse_dt(w.get("completion_time")),
                downtime_minutes=int(w.get("downtime_minutes", 0) or 0),
                status=w.get("status", "OPEN"),
                created_at=utcnow(),
                updated_at=utcnow(),
            ))
        db.commit()

        ext_map = {}
        for ext in read_records("emergency_extensions.csv"):
            ex_obj = db.query(EmergencyExtension).filter(EmergencyExtension.extension_code == ext.get("extension_code")).first() if ext.get("extension_code") else None
            ass_id = asset_map.get(ext.get("asset_id"))
            if not ex_obj and ass_id:
                ex_obj = EmergencyExtension(
                    extension_code=ext.get("extension_code") or f"EXT-{ext.get('id','0')}",
                    asset_id=ass_id,
                    original_due_date=parse_dt(ext.get("original_due_date")),
                    extended_due_date=parse_dt(ext.get("extended_due_date")),
                    reason=ext.get("reason", "Operational continuity"),
                    requested_by=admin_user_id,
                    approved_by=admin_user_id if ext.get("approval_status") == "APPROVED" else None,
                    approval_status=ext.get("approval_status", "PENDING"),
                    approved_at=parse_dt(ext.get("approved_at")),
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(ex_obj)
                db.flush()
            if ex_obj:
                if ext.get("id"):
                    ext_map[ext["id"]] = ex_obj.id
                if ext.get("extension_code"):
                    ext_map[ext["extension_code"]] = ex_obj.id
        db.commit()

        for ca in read_records("corrective_actions.csv"):
            if ca.get("corrective_action_code") and db.query(CorrectiveAction).filter(CorrectiveAction.corrective_action_code == ca["corrective_action_code"]).first():
                continue
            cal_id = event_map.get(ca.get("calibration_event_id"))
            ass_id = asset_map.get(ca.get("asset_id"))
            if not cal_id or not ass_id:
                continue
            db.add(CorrectiveAction(
                corrective_action_code=ca.get("corrective_action_code") or f"CA-{ca.get('id','0')}",
                calibration_event_id=cal_id,
                asset_id=ass_id,
                description=ca.get("description") or "Corrective action",
                assigned_to=admin_user_id,
                root_cause=ca.get("root_cause"),
                action_taken=ca.get("action_taken"),
                status=ca.get("status", "OPEN"),
                opened_at=parse_dt(ca.get("opened_at")) or utcnow(),
                closed_at=parse_dt(ca.get("closed_at")),
            ))
        db.commit()

        for ia in read_records("impact_assessments.csv"):
            if ia.get("assessment_code") and db.query(ImpactAssessment).filter(ImpactAssessment.assessment_code == ia["assessment_code"]).first():
                continue
            cal_id = event_map.get(ia.get("calibration_event_id"))
            ass_id = asset_map.get(ia.get("asset_id"))
            if not cal_id or not ass_id:
                continue
            db.add(ImpactAssessment(
                assessment_code=ia.get("assessment_code") or f"IA-{ia.get('id','0')}",
                calibration_event_id=cal_id,
                asset_id=ass_id,
                affected_production_start=parse_dt(ia.get("affected_production_start")),
                affected_production_end=parse_dt(ia.get("affected_production_end")),
                affected_usage_count=int(ia.get("affected_usage_count", 0) or 0),
                risk_level=ia.get("risk_level", "MEDIUM"),
                assessment_notes=ia.get("assessment_notes"),
                assessed_by=admin_user_id,
                status=ia.get("status", "PENDING"),
                created_at=utcnow(),
                updated_at=utcnow(),
            ))
        db.commit()

        for u in read_records("production_uses.csv"):
            if u.get("usage_code") and db.query(ProductionUse).filter(ProductionUse.usage_code == u["usage_code"]).first():
                continue
            ass_id = asset_map.get(u.get("asset_id"))
            if not ass_id:
                continue
            db.add(ProductionUse(
                usage_code=u.get("usage_code") or f"USE-{u.get('id','0')}",
                asset_id=ass_id,
                production_line=u.get("production_line") or "Line 1",
                operator_id=admin_user_id,
                usage_timestamp=parse_dt(u.get("usage_timestamp")) or utcnow(),
                usage_end_timestamp=parse_dt(u.get("usage_end_timestamp")),
                usage_status=u.get("usage_status", "RECORDED"),
                validation_decision=u.get("validation_decision", "ALLOWED"),
                decision_reason=u.get("decision_reason", "Seeded record"),
                exception_id=ext_map.get(u.get("exception_id")),
                created_at=utcnow(),
            ))
        db.commit()

        for al in read_records("alerts.csv"):
            if al.get("alert_code") and db.query(Alert).filter(Alert.alert_code == al["alert_code"]).first():
                continue
            ass_id = asset_map.get(al.get("asset_id"))
            if not ass_id:
                continue
            db.add(Alert(
                alert_code=al.get("alert_code") or f"ALT-{al.get('id','0')}",
                asset_id=ass_id,
                alert_type=al.get("alert_type", "GENERAL"),
                severity=al.get("severity", "MEDIUM"),
                message=al.get("message", ""),
                status=al.get("status", "OPEN"),
                generated_at=parse_dt(al.get("generated_at")) or utcnow(),
            ))
        db.commit()

        for au in read_records("audit_records.csv"):
            if au.get("record_code") and db.query(AuditRecord).filter(AuditRecord.record_code == au["record_code"]).first():
                continue
            prev = None
            newv = None
            try:
                prev = json.loads(au["previous_value"]) if au.get("previous_value") else None
            except Exception:
                prev = {"raw": au.get("previous_value")}
            try:
                newv = json.loads(au["new_value"]) if au.get("new_value") else None
            except Exception:
                newv = {"raw": au.get("new_value")}
            db.add(AuditRecord(
                record_code=au.get("record_code") or f"AUD-{au.get('id','0')}",
                actor_id=admin_user_id,
                entity_type=au.get("entity_type", "System"),
                entity_id=str(au.get("entity_id", "")),
                action=au.get("action", "SEED"),
                previous_value=prev,
                new_value=newv,
                reason=au.get("reason"),
                timestamp=parse_dt(au.get("timestamp")) or utcnow(),
                request_id=au.get("request_id"),
            ))
        db.commit()

        print("[SUCCESS] Database seed/import completed (required accounts ensured, demo auto-accounts not created).")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database("data")
