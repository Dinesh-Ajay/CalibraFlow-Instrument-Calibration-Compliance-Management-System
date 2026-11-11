from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user, get_user_role_names
from app.models.asset import Asset
from app.models.calibration_event import CalibrationEvent
from app.models.certificate import Certificate
from app.models.impact_assessment import ImpactAssessment
from app.models.user import User
from app.models.work_order import WorkOrder

router = APIRouter(prefix="/assistant", tags=["AI Analytics Assistant"])


class AssistantQuery(BaseModel):
    query: str


class AssistantResponse(BaseModel):
    answer: str
    sources: Optional[list] = []


@router.post("/query", response_model=AssistantResponse)
def query_assistant(req: AssistantQuery, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = (req.query or "").lower().strip()
    roles = set(get_user_role_names(current_user))
    is_admin = "admin" in roles

    def can(*allowed):
        return is_admin or bool(roles.intersection(set(allowed)))

    overdue_assets = db.query(Asset).filter(Asset.calibration_status == "OVERDUE").order_by(Asset.next_due_date.asc()).limit(20).all() if can("admin","operator","maint_eng","quality_eng","planner") else []
    failed_events = db.query(CalibrationEvent).filter(CalibrationEvent.result == "FAIL").order_by(CalibrationEvent.calibration_date.desc()).limit(20).all() if can("admin","maint_eng","quality_eng","planner") else []
    open_wos = db.query(WorkOrder).filter(WorkOrder.status.in_(["OPEN","ASSIGNED","IN_PROGRESS","ON_HOLD"])).order_by(WorkOrder.scheduled_date.desc()).limit(20).all() if can("admin","maint_eng","planner","quality_eng") else []
    pending_ias = db.query(ImpactAssessment).filter(ImpactAssessment.status.in_(["PENDING","IN_PROGRESS"])).order_by(ImpactAssessment.created_at.desc()).limit(20).all() if can("admin","quality_eng","maint_eng") else []
    cert_issues = db.query(Certificate).filter(Certificate.verification_status.in_(["PENDING","INVALID","REJECTED"])).order_by(Certificate.created_at.desc()).limit(20).all() if can("admin","quality_eng","maint_eng") else []

    if "overdue" in q:
        if not can("admin","operator","maint_eng","quality_eng","planner"):
            return AssistantResponse(answer="You do not have permission to view overdue instrument details.", sources=[])
        items = [f"- {a.asset_code} ({a.asset_name}) due {a.next_due_date.strftime('%Y-%m-%d') if a.next_due_date else 'N/A'} on {a.production_line}" for a in overdue_assets]
        return AssistantResponse(answer=f"Overdue instruments: {len(overdue_assets)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[a.asset_code for a in overdue_assets])

    if "fail" in q or "failed" in q:
        if not can("admin","maint_eng","quality_eng","planner"):
            return AssistantResponse(answer="You do not have permission to view failed calibration details.", sources=[])
        items = [f"- {e.calibration_code} asset={e.asset.asset_code if e.asset else e.asset_id} error={e.measurement_error} tol={e.tolerance} date={e.calibration_date.strftime('%Y-%m-%d') if e.calibration_date else 'N/A'}" for e in failed_events]
        return AssistantResponse(answer=f"Recent failed calibration events: {len(failed_events)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[e.calibration_code for e in failed_events])

    if "work order" in q or "work orders" in q:
        if not can("admin","maint_eng","planner","quality_eng"):
            return AssistantResponse(answer="You do not have permission to view work order details.", sources=[])
        items = [f"- {w.work_order_code} [{w.status}/{w.priority}] asset={w.asset.asset_code if w.asset else w.asset_id} due={w.scheduled_date.strftime('%Y-%m-%d') if w.scheduled_date else 'N/A'}" for w in open_wos]
        return AssistantResponse(answer=f"Open/in-progress work orders: {len(open_wos)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[w.work_order_code for w in open_wos])

    if "certificate" in q or "certificates" in q:
        if not can("admin","quality_eng","maint_eng"):
            return AssistantResponse(answer="You do not have permission to view certificate verification details.", sources=[])
        items = [f"- {c.certificate_code} asset={c.asset.asset_code if c.asset else c.asset_id} status={c.verification_status} number={c.certificate_number}" for c in cert_issues]
        return AssistantResponse(answer=f"Certificates requiring attention: {len(cert_issues)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[c.certificate_code for c in cert_issues])

    if "impact" in q:
        if not can("admin","quality_eng","maint_eng"):
            return AssistantResponse(answer="You do not have permission to view impact assessment details.", sources=[])
        items = [f"- {ia.assessment_code} asset={ia.asset.asset_code if ia.asset else ia.asset_id} status={ia.status} risk={ia.risk_level}" for ia in pending_ias]
        return AssistantResponse(answer=f"Pending/in-progress impact assessments: {len(pending_ias)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[ia.assessment_code for ia in pending_ias])

    if "cannot be used" in q or "blocked" in q or "not usable" in q:
        if not can("admin","operator","maint_eng","quality_eng","planner"):
            return AssistantResponse(answer="You do not have permission to view instrument usage status details.", sources=[])
        blocked_assets = db.query(Asset).filter((Asset.operational_status != "ACTIVE") | (Asset.calibration_status.in_(["OVERDUE","FAILED","RESTRICTED"]))).limit(30).all()
        items = [f"- {a.asset_code} ({a.asset_name}) op={a.operational_status} cal={a.calibration_status}" for a in blocked_assets]
        return AssistantResponse(answer=f"Instruments potentially not usable: {len(blocked_assets)}" + ("\n" + "\n".join(items) if items else "\nNone found."), sources=[a.asset_code for a in blocked_assets])

    # Role-aware summary
    lines = ["CalibraFlow operational summary (authorized data):"]
    if can("admin","operator","maint_eng","quality_eng","planner"):
        lines.append(f"- Overdue instruments: {len(overdue_assets)}")
    if can("admin","maint_eng","quality_eng","planner"):
        lines.append(f"- Recent failed calibrations: {len(failed_events)}")
    if can("admin","maint_eng","planner","quality_eng"):
        lines.append(f"- Open/in-progress work orders: {len(open_wos)}")
    if can("admin","quality_eng","maint_eng"):
        lines.append(f"- Certificates needing attention: {len(cert_issues)}")
        lines.append(f"- Pending/in-progress impact assessments: {len(pending_ias)}")
    lines.append("Ask about overdue instruments, failed calibrations, work orders, certificates, impact assessments, or instruments that cannot be used.")
    return AssistantResponse(answer="\n".join(lines), sources=[])
