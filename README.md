# 🗂️ SOX ITGC Audit Evidence Automation

[![CI](https://github.com/Mihirajmera/itgc-evidence-automation/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Mihirajmera/itgc-evidence-automation/actions/workflows/python-ci.yml)
[![CodeQL](https://github.com/Mihirajmera/itgc-evidence-automation/actions/workflows/codeql.yml/badge.svg)](https://github.com/Mihirajmera/itgc-evidence-automation/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Mihirajmera/itgc-evidence-automation/badge)](https://scorecard.dev/viewer/?uri=github.com/Mihirajmera/itgc-evidence-automation)
[![Release](https://img.shields.io/github/v/release/Mihirajmera/itgc-evidence-automation?color=0891b2)](https://github.com/Mihirajmera/itgc-evidence-automation/releases)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-IAM%20%7C%20Config-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

Automates the most time-consuming part of a SOX IT General Controls (ITGC) audit cycle:
pulling access management, change management, and configuration compliance evidence,
running it against control objectives, and packaging the result into an audit-ready
evidence bundle with an auto-generated Corrective Action Plan (CAP) register.

## Why this exists

A recurring theme in ITGC audit prep is manually screenshotting IAM consoles, exporting
change tickets, and cross-referencing them against control objectives by hand. This tool
replaces that with a repeatable pipeline: pull evidence → evaluate against control
rules → package for the auditor → auto-generate CAPs for every exception, with an SLA
clock already attached based on severity.

## OSCAL output

Every bundle now includes `oscal/assessment-results.json` ([sample](evidence_packages/sample-run/oscal/assessment-results.json)) in the same format as my other tools: one observation per ITGC control, carrying the SHA-256 of the raw evidence it was tested on (`evidence_hashes.json`), and one finding per mapped **NIST SP 800-53 Rev. 5** control (`satisfied` with no exceptions, `not-satisfied` otherwise). GRC platforms that import OSCAL can ingest it directly. IDs are deterministic and `SOURCE_DATE_EPOCH` fixes timestamps, so the same evidence always yields the same bundle.

| ITGC control | NIST 800-53 |
|---|---|
| ITGC-AM-01 MFA enforced | IA-2(1), IA-2(2) |
| ITGC-AM-02 Timely revocation | AC-2(3), PS-4 |
| ITGC-AM-03 Privileged access scoped | AC-6, AC-2(7) |
| ITGC-CM-01 Changes approved | CM-3 |
| ITGC-CM-02 Requester ≠ approver | AC-5, CM-5 |
| ITGC-CM-03 Changes tested | CM-3(2), SA-11 |
| ITGC-CFG-01 Config rules compliant | CM-6, CM-2 |

The mapping is my own judgment ([`evidence_automation/oscal.py`](evidence_automation/oscal.py)).

## Architecture

```mermaid
flowchart TD
    subgraph Sources
        IAM[IAM Users<br/>access + MFA + termination status]
        CM[Change Management<br/>approvals + testing evidence]
        CFG[AWS Config<br/>compliance evaluations]
    end

    IAM --> P[EvidenceProvider]
    CM --> P
    CFG --> P

    P --> AM[ITGC-AM checks<br/>Access Management]
    P --> CMK[ITGC-CM checks<br/>Change Management]
    P --> CFGK[ITGC-CFG checks<br/>Configuration]

    AM --> F[Findings]
    CMK --> F
    CFGK --> F

    F --> B[Evidence Bundle<br/>raw JSON + findings.csv + summary.md]
    F --> C[CAP Register<br/>severity-based SLA due dates]

    style P fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style F fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style B fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style C fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

The `EvidenceProvider` interface (`evidence_automation/providers.py`) is pluggable:
- **`MockProvider`** (default, used in this repo) reads synthetic fixtures from
  [`fixtures/`](fixtures/) so the whole pipeline runs with zero credentials.
- **`AWSProvider`** is a real `boto3`-backed implementation (IAM + AWS Config) for
  pointing this at an actual AWS account — wire `get_change_records` to your
  ServiceNow/Jira API to complete it.

## Controls implemented

| Control ID | Area | Objective |
|---|---|---|
| `ITGC-AM-01` | Access Management | MFA enforced for all active accounts |
| `ITGC-AM-02` | Access Management | Access revoked timely after termination |
| `ITGC-AM-03` | Access Management | Privileged access scoped to authorized departments |
| `ITGC-CM-01` | Change Management | All changes have a recorded approval |
| `ITGC-CM-02` | Change Management | Requester and approver are segregated (SoD) |
| `ITGC-CM-03` | Change Management | Changes tested before deployment |
| `ITGC-CFG-01` | Configuration Management | AWS Config rules report compliant resources |

## Installation & Quick Start

You can install the tool locally as a package:

```bash
pip install -e .
```

Once installed, run it using the `itgc-evidence-automation` CLI command:

```bash
# Run against local mock fixtures and output to evidence_packages/
itgc-evidence-automation
```

This runs against the synthetic fixtures in `fixtures/` and writes a timestamped bundle
to `evidence_packages/evidence-<timestamp>/` containing:
- `raw_*.json` — the evidence as pulled, for traceability
- `findings.csv` — every control exception
- `cap_register.csv` — auto-generated CAPs with owner + SLA-based due date
- `evidence_summary.md` — auditor-facing narrative and control coverage table

## Sample run

```
Evidence bundle: evidence_packages/evidence-20260728-190232
Findings: 12  |  CAPs generated: 12
  [High  ] ITGC-AM-01  r.patel: MFA is not enforced for all user accounts
  [High  ] ITGC-AM-02  k.obrien: Access was not revoked timely after termination
  [High  ] ITGC-CM-02  CHG-1002: Segregation of duties violation: requester approved their own change
  ...
```

## Project structure

```
itgc-evidence-automation/
├── cli.py
├── evidence_automation/
│   ├── providers.py      # MockProvider (fixtures) + AWSProvider (boto3, IAM/Config)
│   ├── controls.py        # ITGC control check logic -> Finding objects
│   ├── packager.py        # bundles raw evidence + findings into an audit package
│   └── cap_tracker.py     # generates CAPs with severity-based SLA due dates
├── fixtures/               # synthetic IAM / change management / Config data
├── evidence_packages/      # generated output (gitignored)
└── tests/
    └── test_controls.py
```

## 🤖 CI/CD & Testing

This project uses `pytest` for testing, and is configured with automated CI/CD checks:
- **CI/CD Pipeline**: A GitHub Actions workflow (`.github/workflows/python-ci.yml`) runs automatically on push/pull requests to check formatting (`flake8`), run security analysis (`bandit`), and run tests (`pytest`).

To install dev dependencies and run tests locally:

```bash
pip install -e .[dev]
pytest
```

## Roadmap

- [ ] ServiceNow Change Request API adapter for `get_change_records`
- [ ] Multi-cycle evidence diffing (show what changed since last quarter's evidence pull)
- [ ] PDF export of `evidence_summary.md` for auditor handoff

## About

Built by [Mihir Ajmera](https://linkedin.com/in/mihirajmera) — GRC Engineer specializing
in SOX ITGC testing, control evidence collection, and audit readiness automation.
