from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.analytics_service import calculate_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Returns DB-backed metrics from analytics service (role-aware filtering can be layered in service if needed)
    return calculate_dashboard_summary(db)


@router.get("/calibration-trends")
def get_calibration_trends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = calculate_dashboard_summary(db)
    return {"monthly_trends": data.get("monthly_trends", []), "downtime_trends": data.get("downtime_trends", [])}


@router.get("/compliance")
def get_compliance_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = calculate_dashboard_summary(db)
    return {
        "rates": data.get("rates", {}),
        "line_compliance": data.get("line_compliance", []),
        "overdue_by_type": data.get("overdue_by_type", []),
        "calibration_status_distribution": data.get("calibration_status_distribution", []),
    }


@router.get("/production-usage")
def get_production_usage_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = calculate_dashboard_summary(db)
    return {
        "production_decision_distribution": data.get("production_decision_distribution", []),
        "blocked_usage_rate": data.get("rates", {}).get("blocked_usage_rate", 0),
    }
