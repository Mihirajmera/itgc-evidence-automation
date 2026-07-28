# SOX ITGC Evidence Package

_Generated 2026-07-28T19:02:32_

- IAM users reviewed: **8**
- Change records reviewed: **5**
- Config compliance checks reviewed: **5**
- Total exceptions found: **12**

## Control Coverage

| Control ID | Area | Objective | Exceptions |
|---|---|---|---|
| `ITGC-AM-01` | Access Management | MFA enforced for all active accounts | ⚠️ 2 |
| `ITGC-AM-02` | Access Management | Access revoked timely after termination | ⚠️ 2 |
| `ITGC-AM-03` | Access Management | Privileged access scoped to authorized departments | ⚠️ 1 |
| `ITGC-CM-01` | Change Management | All changes have a recorded approval | ⚠️ 1 |
| `ITGC-CM-02` | Change Management | Requester and approver are segregated | ⚠️ 1 |
| `ITGC-CM-03` | Change Management | Changes tested before deployment | ⚠️ 2 |
| `ITGC-CFG-01` | Configuration Management | AWS Config rules report compliant resources | ⚠️ 3 |

## Exceptions Detail

### `ITGC-AM-01` — MFA is not enforced for all user accounts (High)
- **Resource:** r.patel
- **Detail:** User r.patel (Standard) has no MFA device registered.

### `ITGC-AM-02` — Access was not revoked timely after termination (High)
- **Resource:** k.obrien
- **Detail:** User k.obrien terminated 2026-04-15 but account still present in IAM.

### `ITGC-AM-03` — Admin access granted outside expected department scope (Medium)
- **Resource:** k.obrien
- **Detail:** User k.obrien in Data Platform holds Admin access.

### `ITGC-AM-01` — MFA is not enforced for all user accounts (High)
- **Resource:** d.okafor
- **Detail:** User d.okafor (Standard) has no MFA device registered.

### `ITGC-AM-02` — Access was not revoked timely after termination (High)
- **Resource:** former.contractor
- **Detail:** User former.contractor terminated 2026-03-12 but account still present in IAM.

### `ITGC-CM-02` — Segregation of duties violation: requester approved their own change (High)
- **Resource:** CHG-1002
- **Detail:** CHG-1002 requested and approved by r.patel.

### `ITGC-CM-01` — Change deployed without a recorded approval (High)
- **Resource:** CHG-1003
- **Detail:** CHG-1003 (IAM Policy Update) deployed 2026-06-18 with no ApprovedBy.

### `ITGC-CM-03` — Change deployed without evidence of pre-deployment testing (Medium)
- **Resource:** CHG-1003
- **Detail:** CHG-1003 (IAM Policy Update) has no recorded test evidence.

### `ITGC-CM-03` — Change deployed without evidence of pre-deployment testing (Medium)
- **Resource:** CHG-1005
- **Detail:** CHG-1005 (Payments API) has no recorded test evidence.

### `ITGC-CFG-01` — AWS Config rule 'iam-user-mfa-enabled' reported non-compliant resource (Medium)
- **Resource:** r.patel
- **Detail:** Rule iam-user-mfa-enabled flagged r.patel as NON_COMPLIANT on 2026-07-28.

### `ITGC-CFG-01` — AWS Config rule 'iam-user-mfa-enabled' reported non-compliant resource (Medium)
- **Resource:** d.okafor
- **Detail:** Rule iam-user-mfa-enabled flagged d.okafor as NON_COMPLIANT on 2026-07-28.

### `ITGC-CFG-01` — AWS Config rule 'access-keys-rotated' reported non-compliant resource (Medium)
- **Resource:** svc-account-etl
- **Detail:** Rule access-keys-rotated flagged svc-account-etl as NON_COMPLIANT on 2026-07-28.
