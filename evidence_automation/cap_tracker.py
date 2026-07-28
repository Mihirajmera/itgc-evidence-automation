"""Track Corrective Action Plans (CAPs) generated from findings."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .controls import Finding

SEVERITY_SLA_DAYS = {"High": 15, "Medium": 30, "Low": 60}


@dataclass
class CAP:
    cap_id: str
    control_id: str
    description: str
    severity: str
    owner: str
    due_date: str
    status: str = "Open"


DEFAULT_OWNERS = {
    "Access Management": "IAM Team",
    "Change Management": "Release Management",
    "Configuration Management": "Cloud Infrastructure",
}


def generate_caps(findings: list[Finding]) -> list[CAP]:
    caps = []
    for i, finding in enumerate(findings, start=1):
        sla_days = SEVERITY_SLA_DAYS.get(finding.severity, 30)
        due = (date.today() + timedelta(days=sla_days)).isoformat()
        caps.append(CAP(
            cap_id=f"CAP-ITGC-{i:04d}",
            control_id=finding.control_id,
            description=finding.description,
            severity=finding.severity,
            owner=DEFAULT_OWNERS.get(finding.control_area, "Unassigned"),
            due_date=due,
        ))
    return caps


def write_cap_register(caps: list[CAP], out_path: str | Path) -> None:
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cap_id", "control_id", "description", "severity", "owner", "due_date", "status"])
        for cap in caps:
            writer.writerow([cap.cap_id, cap.control_id, cap.description, cap.severity, cap.owner, cap.due_date, cap.status])
