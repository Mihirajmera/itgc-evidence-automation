"""SOX ITGC control checks: Access Management, Change Management, Segregation of Duties.

Each check function takes raw evidence records and returns a list of Finding objects.
This is deliberately rule-based and auditable — an auditor should be able to read the
check function and understand exactly why something was flagged.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    control_area: str
    control_id: str
    description: str
    severity: str          # Low, Medium, High
    resource: str
    detail: str


def check_access_management(iam_users: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for u in iam_users:
        if not u.get("MFAEnabled", False):
            findings.append(Finding(
                control_area="Access Management", control_id="ITGC-AM-01",
                description="MFA is not enforced for all user accounts",
                severity="High", resource=u["UserName"],
                detail=f"User {u['UserName']} ({u.get('AccessLevel', 'Unknown')}) has no MFA device registered.",
            ))
        if u.get("TerminationDate"):
            findings.append(Finding(
                control_area="Access Management", control_id="ITGC-AM-02",
                description="Access was not revoked timely after termination",
                severity="High", resource=u["UserName"],
                detail=f"User {u['UserName']} terminated {u['TerminationDate']} but account still present in IAM.",
            ))
        if u.get("AccessLevel") == "Admin" and u.get("Department") not in {"Cloud Infrastructure", "Enterprise IT"}:
            findings.append(Finding(
                control_area="Access Management", control_id="ITGC-AM-03",
                description="Admin access granted outside expected department scope",
                severity="Medium", resource=u["UserName"],
                detail=f"User {u['UserName']} in {u.get('Department')} holds Admin access.",
            ))
    return findings


def check_change_management(changes: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for c in changes:
        if c.get("ApprovedBy") is None:
            findings.append(Finding(
                control_area="Change Management", control_id="ITGC-CM-01",
                description="Change deployed without a recorded approval",
                severity="High", resource=c["ChangeId"],
                detail=f"{c['ChangeId']} ({c['System']}) deployed {c['DeployDate']} with no ApprovedBy.",
            ))
        elif c.get("ApprovedBy") == c.get("RequestedBy"):
            findings.append(Finding(
                control_area="Change Management", control_id="ITGC-CM-02",
                description="Segregation of duties violation: requester approved their own change",
                severity="High", resource=c["ChangeId"],
                detail=f"{c['ChangeId']} requested and approved by {c['RequestedBy']}.",
            ))
        if not c.get("TestedBeforeDeploy", False):
            findings.append(Finding(
                control_area="Change Management", control_id="ITGC-CM-03",
                description="Change deployed without evidence of pre-deployment testing",
                severity="Medium", resource=c["ChangeId"],
                detail=f"{c['ChangeId']} ({c['System']}) has no recorded test evidence.",
            ))
    return findings


def check_config_compliance(compliance: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for r in compliance:
        if r.get("ComplianceType") == "NON_COMPLIANT":
            findings.append(Finding(
                control_area="Configuration Management", control_id="ITGC-CFG-01",
                description=f"AWS Config rule '{r['ConfigRuleName']}' reported non-compliant resource",
                severity="Medium", resource=r["ResourceId"],
                detail=f"Rule {r['ConfigRuleName']} flagged {r['ResourceId']} as NON_COMPLIANT on {r['EvaluatedAt']}.",
            ))
    return findings


def run_all_checks(iam_users, changes, compliance) -> list[Finding]:
    return (
        check_access_management(iam_users)
        + check_change_management(changes)
        + check_config_compliance(compliance)
    )
