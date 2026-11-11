import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.routers import alerts, assets, assistant, audit, auth, calibration, calibration_plans, certificates
from app.routers import corrective_actions, dashboard, data_quality, emergency_extensions, impact_assessments, instrument_types
from app.routers import production, suppliers, users, work_orders


def _should_run_startup_bootstrap() -> bool:
    if os.environ.get("CALIBRAFLOW_SKIP_STARTUP_BOOTSTRAP", "").strip() == "1":
        return False
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return True


def _idempotent_startup_bootstrap() -> None:
    if not _should_run_startup_bootstrap():
        return
    try:
        from sqlalchemy.orm import Session
        from app.database import SessionLocal
        from app.services.bootstrap_service import bootstrap_required_access

        db: Session = SessionLocal()
        try:
            bootstrap_required_access(db, actor_id=None, request_id="startup-bootstrap")
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        return


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Instrument Calibration & Compliance Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = settings.API_V1_PREFIX
for module in [
    auth,
    users,
    instrument_types,
    assets,
    calibration_plans,
    calibration,
    certificates,
    work_orders,
    production,
    emergency_extensions,
    corrective_actions,
    impact_assessments,
    alerts,
    audit,
    data_quality,
    dashboard,
    assistant,
    suppliers,
]:
    app.include_router(module.router, prefix=API_PREFIX)


@app.on_event("startup")
async def on_startup():
    _idempotent_startup_bootstrap()


@app.on_event("shutdown")
async def on_shutdown():
    return None


@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "CalibraFlow", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "message": "CalibraFlow Instrument Calibration & Compliance Management System API",
        "docs": "/docs",
        "health": "/health",
    }

