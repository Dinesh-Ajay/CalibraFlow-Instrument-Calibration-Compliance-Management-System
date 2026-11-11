# CalibraFlow — Business Rules & Compliance Specification

## 1. Calibration Mathematics & Evaluation Rules

### Rule 1.1: Relative Percentage Error
When the reference standard value $r \neq 0$:
$$\text{Percentage Error} = \frac{|m - r|}{|r|} \times 100$$
Where:
- $m$: Observed measurement on instrument under test.
- $r$: Certified reference standard value.

### Rule 1.2: Absolute Error
When the reference standard value $r = 0$:
$$\text{Absolute Error} = |m - r|$$

### Rule 1.3: Result Determination
- If $\text{Error} \leq \text{Tolerance}$: Result is **PASS**.
  - Operational status remains `ACTIVE`.
  - `last_calibration_date` is updated to event date.
  - `next_due_date` is set to $\text{event\_date} + \text{plan.interval\_months}$.
  - System logs audit entry.
- If $\text{Error} > \text{Tolerance}$: Result is **FAIL**.
  - Operational status transitions to `RESTRICTED` or `BLOCKED`.
  - Calibration status transitions to `FAILED`.
  - Automatic `CorrectiveAction` (CAPA) is created.
  - Linked `ImpactAssessment` requirement is flagged.
  - `CRITICAL` compliance alert is broadcast.

---

## 2. Production Usage Gating Rules (9-Step Policy)

When an operator queries or attempts to deploy an instrument on a production line, the system sequentially evaluates the following deterministic rules:

1. **Rule 2.1 (Existence Check)**:
   - Does asset ID exist in database? If no $\rightarrow$ `BLOCKED: Asset not found`.
2. **Rule 2.2 (Lifecycle State)**:
   - Is operational status `RETIRED`, `SCRAPPED`, or `INACTIVE`? If yes $\rightarrow$ `BLOCKED: Decommissioned asset`.
3. **Rule 2.3 (Recent Calibration Result)**:
   - Was the most recent calibration result `FAIL`? If yes $\rightarrow$ `BLOCKED: Last calibration failed`.
4. **Rule 2.4 (Calibration Window Expiry)**:
   - Is `current_time > next_due_date`?
   - If yes, proceed to Rule 2.5 (Emergency Extension Check).
   - If no, proceed to Rule 2.6 (Certificate Check).
5. **Rule 2.5 (Emergency Extension Evaluation)**:
   - If overdue: Is there an active `EmergencyExtension` where `status = 'APPROVED'` and `current_time <= extension_expiry`?
   - If NO $\rightarrow$ `BLOCKED: Expired, no exception`.
   - If YES $\rightarrow$ `ALLOWED_WITH_EXCEPTION: Emergency extension active (Extension code: EXT-...)`.
6. **Rule 2.6 (Certificate Validation)**:
   - Does the asset require a certificate?
   - If yes: Is there an active certificate with `verification_status = 'VERIFIED'` and `valid_until >= current_time`?
   - If no active certificate $\rightarrow$ `BLOCKED: Missing or invalid certificate`.
7. **Rule 2.7 (Production Line Authorization)**:
   - Is the instrument authorized for deployment on the target line?
   - If mismatch $\rightarrow$ `BLOCKED: Unauthorized production line deployment`.
8. **Rule 2.8 (Corrective Action Containment)**:
   - Are there unresolved high-priority CAPAs on this asset?
   - If yes $\rightarrow$ `BLOCKED: Pending open corrective action`.
9. **Rule 2.9 (Cycle Count Limit)**:
   - Has lifetime cycle count exceeded manufacturer threshold?
   - If yes $\rightarrow$ `BLOCKED: Maximum lifetime usage cycles reached`.

If all applicable checks pass, the gate outputs: `ALLOWED: Within valid window`.

---

## 3. Certificate Traceability Rules

### Rule 3.1: Asset Ownership Integrity
A certificate uploaded for a calibration event MUST match the asset registered to that calibration event:
$$\text{certificate.asset\_id} == \text{calibration\_event.asset\_id}$$
If mismatched, the validation engine flags anomaly `certificate_wrong_asset`, tags the certificate status as `Wrong asset`, and raises a High-priority compliance alert.

### Rule 3.2: QA Sign-off
Certificates uploaded by technicians or third-party vendor laboratories enter `PENDING` verification status. A Quality Engineer MUST sign off before the certificate is marked `VERIFIED`.
