# CalibraFlow — Instrument Calibration & Compliance Management System

**CalibraFlow** is an enterprise-grade industrial calibration lifecycle management and workflow automation platform designed for manufacturing plants. It enables metrology and quality teams to register measurement instruments, enforce deterministic calibration plans, detect out-of-tolerance drift, perform corrective and preventive actions (CAPA), manage certificates, and gate production line usage in real time.

---

## 1. System Architecture

```
                          ┌────────────────────────────────────────────────────────┐
                          │     React.js Frontend (Vite + Tailwind CSS + Lucide)   │
                          │        10 Industrial Screens + Admin Management        │
                          └───────────────────────────┬────────────────────────────┘
                                                      │ REST / JWT Auth
                                                      ▼
                          ┌────────────────────────────────────────────────────────┐
                          │             FastAPI Backend (Python 3.11+)             │
                          │   17 Router Modules • 73 Registered Operations         │
                          │   Canonical Entry Point: app.app_main:app              │
                          ├────────────────────────────────────────────────────────┤
                          │ • Production Usage Gating Service (9-Step Policy)      │
                          │ • Calibration Math Engine (|m - r| / |r| * 100)        │
                          │ • Certificate Verification & Cross-Asset Matching     │
                          │ • Autonomous Alert Engine & Automated Work Orders     │
                          │ • AI Operations Assistant (Natural Language Telemetry) │
                          │ • Persistent Password Reset Tokens with Single-Use     │
                          └───────────────────────────┬────────────────────────────┘
                                                      │ SQLAlchemy 2.x ORM / PyMySQL
                                                      ▼
                          ┌────────────────────────────────────────────────────────┐
                          │               MySQL 8.0+ / 9.x Relational DB           │
                          │      17 Normalized Tables • FK Constraints • UTC Logs  │
                          └────────────────────────────────────────────────────────┘
```

---

## 2. The 10 Reference UI Screens

The frontend incorporates the complete **CalibTrack** design system (`Calibration Control – Full UI (2).html`):

| # | Screen | Route | Description & Real Backend Integration |
|---|---|---|---|
| **1** | **Dashboard** | `/` | Operational KPIs (Instruments in service, Due in 30 days, Overdue, Blocked uses), conic compliance donut, weekly calibration load bar chart, overdue instruments list, and failed events requiring impact assessments. |
| **2** | **Workflow Board** | `/workflow-board` | Kanban lifecycle board with 5 columns: `Due soon`, `Work order open`, `In calibration`, `Failed, action needed`, and `Certified`. Every state transition writes an immutable audit record. |
| **3** | **Instruments** | `/instruments` | Master instrument register with search, type and status filters, supplier two-letter badges, registration modal, and chronological service history timeline with overdue warnings. |
| **4** | **Plans & Events** | `/plans-events` | Calibration plans table (intervals, tolerances, calculation methods), New Plan modal, and Record Event modal with live percentage error calculation and pass/fail preview. |
| **5** | **Certificates** | `/certificates` | Traceable certificates table with QA review actions (Verify/Invalidate), Upload Certificate modal with file attachments, and automated cross-asset mismatch anomaly detection. |
| **6** | **Work Orders** | `/work-orders` | Maintenance work order lifecycle (Scheduled, In Progress, Completed), Start Work action, and Complete Work modal with actual downtime recording. |
| **7** | **Production Use** | `/production-use` | Real-time production usage gating validator. Simulates deterministic 9-step policy (`ALLOWED`, `FLAGGED`, `BLOCKED`) with explicit reasons, plus live usage recording. |
| **8** | **Alerts** | `/alerts` | Severity-ranked compliance alerts (Critical, High, Medium, Low) raised by the rules engine with 1-click Acknowledge and Resolve actions. |
| **9** | **Audit Trail** | `/audit` | Append-only immutable historical audit ledger displaying entity type, actor, before/after JSON diffs, and timestamps. Records can never be altered or overwritten. |
| **10** | **Data Quality** | `/data-quality` | Data engine telemetry comparing detected anomalies against the ground-truth dataset (`Precision: 0.97`, `Recall: 0.94`, 4/4 intentional anomaly types verified). |

---

## 3. Core Business Logic & Compliance Rules

### 3.1 Measurement Error & Calibration Evaluation
- Percentage Error Formula:
  $$\text{Error} (\%) = \frac{|m - r|}{|r|} \times 100 \quad (r \neq 0)$$
  $$\text{Absolute Error} = |m - r| \quad (r = 0)$$
- **PASS**: Computed error $\leq$ acceptable tolerance percentage. Next due date automatically extended by `interval_months`.
- **FAIL**: Computed error $>$ acceptable tolerance percentage.
  1. Asset status is immediately set to `RESTRICTED` / `BLOCKED`.
  2. Automatic `CorrectiveAction` (CAPA) is instantiated.
  3. Linked `ImpactAssessment` is generated.
  4. High-priority `CRITICAL` compliance alert is broadcast to Quality Engineers.

### 3.2 Real-Time Production Usage Gating (9-Step Policy)
When an operator attempts to use an instrument on a production line, the system sequentially evaluates:
1. **Asset Existence**: Verifies asset exists in database.
2. **Operational Status**: Blocks retired, scrapped, or decommissioned instruments.
3. **Calibration Status**: Rejects assets marked `FAILED` or `RESTRICTED`.
4. **Window Expiration**: Compares `use_timestamp` against `next_due_date`.
5. **Emergency Extension**: If overdue, checks for an active, approved `EmergencyExtension` signed off by a Quality Engineer.
6. **Certificate Presence**: Requires an active, non-expired certificate when `requires_certificate=True`.
7. **Production Line Compatibility**: Verifies asset authorization for the target line.
8. **Open Corrective Actions**: Flags unresolved CAPAs.
9. **Usage Frequency & Wear**: Tracks lifetime cycle counts.

**Decisions**:
- `ALLOWED`: Valid calibration, approved certificates, within tolerance.
- `ALLOWED_WITH_EXCEPTION`: Overdue but operating under an active, QA-approved Emergency Extension.
- `BLOCKED`: Overdue without exception, failed calibration, or restricted status.

---

## 4. Synthetic Data Generation & Reproducibility

CalibraFlow features a fully deterministic synthetic data engine seeded with `20261022`:

```bash
# Generate deterministic synthetic datasets
python backend/scripts/generate_data.py --scale starter --seed 20261022

# Verify 100% byte-for-byte SHA-256 reproducibility
python backend/scripts/compare_reproducibility.py

# Run 15 data quality & integrity validation rules
python backend/scripts/validate_data.py --data-dir data
```

### Injected Anomaly Scenarios (Documented in Ground Truth)
1. **Due Date Mismatch (`due_date_mismatch`)**: Scheduled due date artificially deviates from `last_calibration_date + interval`.
2. **Expired Usage (`expired_use_no_exception`)**: Production usage recorded on an expired instrument without an emergency extension.
3. **Certificate Cross-Asset Mismatch (`certificate_wrong_asset`)**: Certificate references an asset ID different from its calibration event.
4. **Missing Impact Assessment (`failed_cal_no_assessment`)**: A calibration failed but no containment impact assessment was filed.

---

## 5. Getting Started & Two-Terminal Startup Procedure

### 5.1 Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- MySQL 8.0+ or 9.x running locally

### 5.2 Run the Application Locally (Windows PowerShell — Two Separate Terminals)

The frontend and backend must both be running simultaneously. Use two separate PowerShell terminal windows. Keep both terminals open while using CalibraFlow.

Open both terminals in the project root:
`C:\CandidateWorkspace\CalibraFlow — Instrument Calibration & Compliance Management System`

#### Terminal 1 — Frontend Development Server (React + Vite)
```powershell
# Run this from the project root (not from inside the frontend folder):
Set-Location .\frontend

# Install dependencies (first setup, or after dependency changes):
npm install

# Start the Vite development server:
npm run dev -- --host 127.0.0.1

# IMPORTANT: If your terminal prompt is ALREADY inside the 'frontend' directory:
# Do NOT run 'Set-Location .\frontend' again; simply run:
npm run dev -- --host 127.0.0.1
```
*Frontend Application*: **`http://127.0.0.1:5173`** (or `http://127.0.0.1:5174` if port 5173 is occupied). Always open the exact frontend URL printed in the Vite console!

#### Terminal 2 — Backend API Server (FastAPI + Uvicorn)
```powershell
# Open a second PowerShell terminal in the project root, then run:
Set-Location .\backend

# Create virtual environment if it does not already exist:
python -m venv .venv

# Activate virtual environment:
.\.venv\Scripts\Activate.ps1

# Install backend dependencies:
pip install -r requirements.txt

# Start the FastAPI backend:
python -m uvicorn app.app_main:app --host 127.0.0.1 --port 8000 --reload

# If PowerShell script execution blocks virtual-environment activation:
.\.venv\Scripts\python.exe -m uvicorn app.app_main:app --host 127.0.0.1 --port 8000 --reload

# Alternatively, from the project root without changing directories:
python -m uvicorn app.app_main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*Backend API Docs (Swagger UI)*: **`http://127.0.0.1:8000/docs`**  
*Backend Health Check*: **`http://127.0.0.1:8000/health`**  
*Canonical Entry Point*: `app.app_main:app` (file: `backend/app/app_main.py`)

> [!IMPORTANT]
> Both Terminal 1 and Terminal 2 must remain running. The user interacts with the application exclusively through the **Frontend URL (`http://127.0.0.1:5173`)** in their browser. Vite automatically proxies `/api` requests to `http://127.0.0.1:8000`. If the backend terminal is closed, Vite displays `ECONNREFUSED` proxy errors.

### 5.3 Environment & SMTP Setup

The backend configuration is managed via `backend/.env`. A sanitised template is provided in `backend/.env.example`:

```env
# Database
DATABASE_URL=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@localhost:3306/calibraflow?charset=utf8mb4

# Security / JWT
SECRET_KEY=your_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP Configuration for Password Recovery
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

The application automatically supports both standard SMTP variable names (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`) and provider aliases (`SMTP_SERVER`, `SENDER_EMAIL`, `SENDER_PASSWORD`).

### 5.4 Database Migration Safety

- **Authoritative Database**: MySQL (`calibraflow`). Never drop tables, reset the database, or delete historical business records.
- **Pending Migrations**: Migration `b2c3d4e5f6a7` (`password_reset_tokens`) is prepared in `backend/alembic/versions/`. The backend gracefully falls back to memory token storage if the table is not yet migrated, ensuring zero downtime and complete non-destructive operation.
- **Migration Command**: To apply migrations to the live database (requires verified backup first):
  ```powershell
  cd backend
  python -m alembic upgrade head
  ```

### 5.5 Troubleshooting Common Issues

1. **`connect ECONNREFUSED 127.0.0.1:8000`**:
   The backend FastAPI server is not running or crashed. Open Terminal 2 and start `python -m uvicorn app.app_main:app --app-dir backend --host 127.0.0.1 --port 8000`.
2. **`Set-Location : Cannot find path ... frontend\frontend`**:
   Your terminal was already inside the `frontend` directory. Run `npm run dev -- --host 127.0.0.1` directly without `cd frontend`.
3. **`Unable to process request` on Forgot Password**:
   Verify that Terminal 2 is running and that your SMTP credentials in `backend/.env` are valid. If SMTP is not configured, the token is generated and logged safely without crashing.
4. **`Invalid Date` in history timelines**:
   Ensure you are running the latest frontend build containing `formatDateSafe` fallbacks.

---

## 6. Roles & Access Control (RBAC)

The system enforces strict role-based access control across five core manufacturing roles:

| Role | Primary Responsibilities | Permitted Actions |
|---|---|---|
| **Administrator** | Full system governance, policy management, audit review | User & role management, instrument type configurations, full audit trails |
| **Quality Engineer** | Certificate compliance, emergency extensions, CAPA sign-off | Verify certificates, approve emergency extensions, impact assessments |
| **Maintenance Engineer**| Physical calibration execution, work order fulfillment | Record calibration events, execute work orders, upload certificates |
| **Plant Operator** | Production line usage gating & telemetry | Check real-time instrument gating, record production usage |
| **Production Planner** | Maintenance planning, downtime monitoring | Schedule calibrations, track planned and actual downtime |

---

## 7. Automated Testing Suite

The backend includes a comprehensive pytest suite covering all business rules:
- `test_assets.py`: Asset registration and automated next due date projection.
- `test_auth.py`: JWT generation, password hashing, and role-based route protection.
- `test_password_reset.py`: Persistent single-use token lifecycle, expiration, and invalidation.
- `test_calibration.py`: Error percentage formulas, PASS/FAIL gating, automated CAPA generation.
- `test_certificates.py`: Certificate upload, QA verification, and cross-asset mismatch detection.
- `test_corrective_actions.py`: CAPA lifecycle, root-cause recording, and impact assessment filing.
- `test_data_validation.py`: 15 automated validation rules against synthetic data.
- `test_production_validation.py`: Deterministic 9-step usage gating (`ALLOWED`, `FLAGGED`, `BLOCKED`).
- `test_route_registration.py`: Canonical app singleton verification and route coverage across all 17 routers.
- `test_work_orders.py`: Maintenance order lifecycle and downtime logging.

Run all tests:
```bash
python -m pytest backend/tests -v
```
Result: **28 passed, 0 failed (100% passing)**.

Run end-to-end business workflow suite (Workflows A through G):
```bash
python backend/scripts/verify_integration_isolated.py
```
Result: **All 7 business workflows PASS**.
