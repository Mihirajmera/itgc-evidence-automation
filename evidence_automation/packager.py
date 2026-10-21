"""Package raw evidence + findings into a timestamped audit evidence bundle.

Produces a folder containing:
  - raw evidence JSON (what was pulled, and when)
  - findings.csv (every control exception, ready to paste into a CAP tracker)
  - evidence_summary.md (auditor-facing narrative + control coverage table)
  - evidence_hashes.json (SHA-256 of every raw evidence file)
  - oscal/assessment-results.json (OSCAL 1.1.2, one finding per mapped NIST 800-53 control)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .controls import Finding
from .oscal import assessment_results


def _now() -> datetime:
    """Now, or SOURCE_DATE_EPOCH when set, so a committed sample bundle is reproducible."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    return datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)


def _write(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8", newline="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    name: str | None = None,
) -> Path:
    now = _now()
    bundle_dir = Path(out_dir) / (name or f"evidence-{now:%Y%m%d-%H%M%S}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    hashes = {
        "raw_iam_users.json": _write(bundle_dir / "raw_iam_users.json", json.dumps(iam_users, indent=2, sort_keys=True)),
        "raw_change_management.json": _write(bundle_dir / "raw_change_management.json",
                                             json.dumps(changes, indent=2, sort_keys=True)),
        "raw_config_compliance.json": _write(bundle_dir / "raw_config_compliance.json",
                                             json.dumps(compliance, indent=2, sort_keys=True)),
    }
    _write(bundle_dir / "evidence_hashes.json", json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    (bundle_dir / "oscal").mkdir(exist_ok=True)
    _write(bundle_dir / "oscal" / "assessment-results.json",
           json.dumps(assessment_results(CONTROL_COVERAGE, findings, hashes, now.isoformat()), indent=2) + "\n")

    with open(bundle_dir / "findings.csv", "w", newline="", encoding="utf-8") as f:
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
        f"_Generated {now.isoformat(timespec='seconds')}_",
        "",
        f"- IAM users reviewed: **{len(iam_users)}**",
        f"- Change records reviewed: **{len(changes)}**",
        f"- Config compliance checks reviewed: **{len(compliance)}**",
        f"- Total exceptions found: **{len(findings)}**",
        "",
        "Raw evidence is hashed in `evidence_hashes.json`; `oscal/assessment-results.json` maps each "
        "control to NIST SP 800-53 for GRC platforms that import OSCAL.",
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

    _write(bundle_dir / "evidence_summary.md", "\n".join(lines) + "\n")

    return bundle_dir
