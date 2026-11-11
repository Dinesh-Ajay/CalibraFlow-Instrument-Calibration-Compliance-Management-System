# CalibraFlow — Database Schema Reference

Authoritative Database: **MySQL 8+ / 9.1** (`calibraflow`)
ORM: **SQLAlchemy 2.x** with PyMySQL

## 1. Schema Tables Overview

The system schema comprises 17 authoritative tables:

| Table | Purpose | Primary Keys & Indexes | Foreign Keys |
|---|---|---|---|
| `users` | User credentials and profile | `id` (PK, auto), `username` (unique), `email` (unique) | None |
| `roles` | RBAC role definitions | `id` (PK, auto), `role_name` (unique) | None |
| `user_roles` | User-to-Role assignments | `id` (PK, auto), `(user_id, role_id)` | `users.id`, `roles.id` |
| `instrument_types` | Metrological categories | `id` (PK, auto), `type_code` (unique) | None |
| `suppliers` | Calibration laboratories & vendors | `id` (PK, auto), `supplier_code` (unique) | None |
| `assets` | Physical instruments / gauges | `id` (PK, auto), `asset_code` (unique) | `instrument_types.id`, `suppliers.id`, `calibration_plans.id` |
| `calibration_plans` | Frequency and tolerance specifications | `id` (PK, auto), `plan_code` (unique) | `instrument_types.id` |
| `calibration_events` | Test execution outcomes | `id` (PK, auto), `calibration_code` (unique) | `assets.id`, `calibration_plans.id`, `users.id` |
| `certificates` | Calibration certificates & verification | `id` (PK, auto), `certificate_code` (unique) | `calibration_events.id`, `assets.id`, `users.id` |
| `work_orders` | Maintenance & calibration job orders | `id` (PK, auto), `work_order_code` (unique) | `assets.id`, `users.id` |
| `production_uses` | Live usage validation events | `id` (PK, auto), `usage_code` (unique) | `assets.id`, `users.id` |
| `alerts` | Compliance & anomaly alerts | `id` (PK, auto), `alert_code` (unique) | `assets.id` |
| `audit_records` | Append-only immutable audit trail | `id` (PK, auto), `created_at` | `users.id` |
| `corrective_actions` | CAPA workflow records | `id` (PK, auto), `capa_code` (unique) | `calibration_events.id`, `assets.id`, `users.id` |
| `impact_assessments` | Quality containment records | `id` (PK, auto), `assessment_code` (unique) | `calibration_events.id`, `assets.id`, `users.id` |
| `emergency_extensions` | Grace-period extension permits | `id` (PK, auto), `extension_code` (unique) | `assets.id`, `users.id` |
| `password_reset_tokens`| Secure single-use recovery tokens | `id` (PK, auto), `token_hash` (unique, indexed) | `users.id` |

## 2. Integrity and Cascade Rules

- **Soft vs Hard Deletions**: Core audit and historical event tables (`audit_records`, `calibration_events`, `production_uses`) are strictly append-only.
- **Cascades**: User deactivation disables access without deleting historical audit logs (`actor_id` remains intact).
- **Timezone**: All timestamp columns store standard UTC (`DateTime` with UTC timezone handling via `app.utils.date_utils.utcnow`).
