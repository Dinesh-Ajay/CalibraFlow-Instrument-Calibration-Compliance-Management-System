from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class KPISummary(BaseModel):
    total_instruments: int
    calibration_compliant: int
    upcoming_calibration: int
    overdue_instruments: int
    failed_calibrations: int
    missing_certificates: int
    open_work_orders: int
    blocked_production_usage: int


class MetricRates(BaseModel):
    compliance_rate: float
    calibration_failure_rate: float
    certificate_coverage: float
    blocked_usage_rate: float
    corrective_action_completion_rate: float


class DistributionItem(BaseModel):
    name: str
    value: int
    percentage: Optional[float] = None


class TrendItem(BaseModel):
    label: str
    total: int
    passed: int
    failed: int


class DowntimeTrendItem(BaseModel):
    label: str
    downtime_minutes: int


class DashboardSummaryResponse(BaseModel):
    kpis: KPISummary
    rates: MetricRates
    calibration_status_distribution: List[DistributionItem]
    work_order_status_distribution: List[DistributionItem]
    production_decision_distribution: List[DistributionItem]
    line_compliance: List[Dict[str, Any]]
    overdue_by_type: List[Dict[str, Any]]
    monthly_trends: List[TrendItem]
    downtime_trends: List[DowntimeTrendItem]
    recent_alerts: List[Dict[str, Any]]
