"""Package raw evidence + findings into a timestamped audit evidence bundle.

Produces a folder containing:
  - raw evidence JSON (what was pulled, and when)
  - findings.csv (every control exception, ready to paste into a CAP tracker)
  - evidence_summary.md (auditor-facing narrative + control coverage table)
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .controls import Finding

CONTROL_COVERAGE = [
    ("ITGC-AM-01", "Access Management", "MFA enforced for all active accounts"),
    ("ITGC-AM-02", "Access Management", "Access revoked timely after termination"),
    ("ITGC-AM-03", "Access Management", "Privileged access scoped to authorized departments"),
    ("ITGC-CM-01", "Change Management", "All changes have a recorded approval"),
    ("ITGC-CM-02", "Change Management", "Requester and approver are segregated"),
    ("ITGC-CM-03", "Change Management", "Changes tested before deployment"),
    ("ITGC-CFG-01", "Configuration Management", "AWS Config rules report compliant resources"),
]


def package_evidence(
    iam_users: list[dict],
    changes: list[dict],
    compliance: list[dict],
    findings: list[Finding],
    out_dir: str | Path,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle_dir = Path(out_dir) / f"evidence-{ts}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    (bundle_dir / "raw_iam_users.json").write_text(json.dumps(iam_users, indent=2))
    (bundle_dir / "raw_change_management.json").write_text(json.dumps(changes, indent=2))
    (bundle_dir / "raw_config_compliance.json").write_text(json.dumps(compliance, indent=2))

    with open(bundle_dir / "findings.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["control_id", "control_area", "severity", "resource", "description", "detail"])
        for finding in findings:
            writer.writerow([
                finding.control_id, finding.control_area, finding.severity,
                finding.resource, finding.description, finding.detail,
            ])

    findings_by_control = {}
    for finding in findings:
        findings_by_control.setdefault(finding.control_id, []).append(finding)

    lines = [
        "# SOX ITGC Evidence Package",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        f"- IAM users reviewed: **{len(iam_users)}**",
        f"- Change records reviewed: **{len(changes)}**",
        f"- Config compliance checks reviewed: **{len(compliance)}**",
        f"- Total exceptions found: **{len(findings)}**",
        "",
        "## Control Coverage",
        "",
        "| Control ID | Area | Objective | Exceptions |",
        "|---|---|---|---|",
    ]
    for control_id, area, objective in CONTROL_COVERAGE:
        n = len(findings_by_control.get(control_id, []))
        status = "✅ 0" if n == 0 else f"⚠️ {n}"
        lines.append(f"| `{control_id}` | {area} | {objective} | {status} |")

    lines += ["", "## Exceptions Detail", ""]
    if findings:
        for finding in findings:
            lines.append(f"### `{finding.control_id}` — {finding.description} ({finding.severity})")
            lines.append(f"- **Resource:** {finding.resource}")
            lines.append(f"- **Detail:** {finding.detail}")
            lines.append("")
    else:
        lines.append("No exceptions identified in this evidence cycle.")

    (bundle_dir / "evidence_summary.md").write_text("\n".join(lines))

    return bundle_dir
