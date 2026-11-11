# CalibraFlow — REST API Specification

The CalibraFlow backend provides 48 REST API endpoints under `/api/v1` organized by business domain.

## 1. Authentication & Users (`/api/v1/auth`)
- `POST /auth/register`: Register new user with assigned roles.
- `POST /auth/login`: Authenticate with username and password; returns JWT access token and user metadata.
- `GET /auth/me`: Retrieve current authenticated user profile and roles.
- `GET /auth/users`: List users in the system (Admin only).

## 2. Master Assets (`/api/v1/assets`)
- `GET /assets`: List instruments with pagination and filters (`calibration_status`, `operational_status`, `search`).
- `POST /assets`: Register a new physical instrument asset.
- `GET /assets/{asset_id}`: Retrieve detailed instrument record.
- `PATCH /assets/{asset_id}`: Update asset properties.
- `DELETE /assets/{asset_id}`: Decommission/delete asset.
- `GET /assets/{asset_id}/history`: Retrieve full service history and calibration events for an instrument.

## 3. Instrument Types & Metrology Plans (`/api/v1/instrument-types`, `/api/v1/calibration-plans`)
- `GET /instrument-types`: List metrological categories (Pressure, Temperature, Flow, etc.).
- `POST /instrument-types`: Create new category with default tolerance and intervals.
- `GET /calibration-plans`: List defined calibration plans.
- `POST /calibration-plans`: Define periodic calibration intervals and tolerance limits.
- `GET /calibration-plans/{plan_id}`: Retrieve plan specifications.

## 4. Calibration Execution & Events (`/api/v1/calibration`)
- `POST /calibration/events`: Record observed calibration test data; computes percentage error and evaluates PASS/FAIL.
- `GET /calibration/events`: List calibration history records.
- `GET /calibration/events/{event_id}`: Retrieve event details with measured values.
- `GET /calibration/upcoming`: Scan instruments due within 14-30 days.
- `GET /calibration/overdue`: Scan instruments currently overdue.
- `POST /calibration/scan-schedule`: Trigger scheduled rules engine pass to raise alerts and create work orders.

## 5. Traceable Certificates (`/api/v1/certificates`)
- `GET /certificates`: List registered certificates with verification status.
- `POST /certificates`: Register certificate metadata.
- `POST /certificates/upload`: Upload official certificate PDF/image with metadata.
- `GET /certificates/{cert_id}`: Retrieve certificate details.
- `PATCH /certificates/{cert_id}/verify`: Quality Engineer sign-off action (`VERIFIED` or `REJECTED`).

## 6. Maintenance Work Orders (`/api/v1/work-orders`)
- `GET /work-orders`: List maintenance work orders with status filter.
- `POST /work-orders`: Generate new work order.
- `GET /work-orders/{wo_id}`: Retrieve work order record.
- `PATCH /work-orders/{wo_id}/status`: Transition lifecycle state (`OPEN` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`) with downtime logging.

## 7. Production Usage Gating (`/api/v1/production`)
- `POST /production/validate-usage`: Dry-run evaluation against 9-step compliance policy (`ALLOWED`, `ALLOWED_WITH_EXCEPTION`, `BLOCKED`).
- `POST /production/usage`: Record actual deployment attempt; enforces gating decision and triggers alerts on violation.
- `GET /production/usage`: Query production usage history log.

## 8. Corrective Actions (CAPA) & Impact Assessments (`/api/v1/corrective-actions`, `/api/v1/impact-assessments`)
- `GET /corrective-actions`: List open and resolved CAPAs.
- `POST /corrective-actions`: Open new CAPA investigation.
- `PATCH /corrective-actions/{capa_id}`: Update containment and root-cause analysis.
- `GET /impact-assessments`: List product impact evaluations for out-of-spec instruments.
- `POST /impact-assessments`: File containment assessment for manufactured batches.

## 9. Emergency Calibration Extensions (`/api/v1/emergency-extensions`)
- `GET /emergency-extensions`: List active and historical extensions.
- `POST /emergency-extensions`: Request emergency grace period.
- `PATCH /emergency-extensions/{ext_id}/approve`: Quality Engineer approval sign-off.

## 10. Compliance Alerts & Notifications (`/api/v1/alerts`)
- `GET /alerts`: List active and historical compliance alerts.
- `PATCH /alerts/{alert_id}/acknowledge`: Mark alert as acknowledged.
- `PATCH /alerts/{alert_id}/resolve`: Resolve and close alert.

## 11. Immutable Audit Ledger (`/api/v1/audit`)
- `GET /audit`: Query append-only audit trail records with before/after JSON diffs.

## 12. Operations Dashboard & Analytics (`/api/v1/dashboard`)
- `GET /dashboard/summary`: Aggregated operational metrics, compliance rates, weekly distributions, and trends.

## 13. AI Operational Assistant (`/api/v1/assistant`)
- `POST /assistant/query`: Natural-language analytics questions over database telemetry.
