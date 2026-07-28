import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evidence_automation.controls import (
    check_access_management, check_change_management, check_config_compliance,
)


def test_flags_missing_mfa():
    users = [{"UserName": "u1", "MFAEnabled": False, "AccessLevel": "Standard", "Department": "IT"}]
    findings = check_access_management(users)
    assert any(f.control_id == "ITGC-AM-01" for f in findings)


def test_no_finding_when_mfa_enabled_and_active():
    users = [{"UserName": "u1", "MFAEnabled": True, "AccessLevel": "Standard",
              "Department": "Enterprise IT", "TerminationDate": None}]
    findings = check_access_management(users)
    assert findings == []


def test_flags_self_approved_change():
    changes = [{"ChangeId": "C1", "System": "X", "ApprovedBy": "a", "RequestedBy": "a",
                "TestedBeforeDeploy": True, "DeployDate": "2026-01-01"}]
    findings = check_change_management(changes)
    assert any(f.control_id == "ITGC-CM-02" for f in findings)


def test_flags_unapproved_change():
    changes = [{"ChangeId": "C2", "System": "X", "ApprovedBy": None, "RequestedBy": "a",
                "TestedBeforeDeploy": True, "DeployDate": "2026-01-01"}]
    findings = check_change_management(changes)
    assert any(f.control_id == "ITGC-CM-01" for f in findings)


def test_flags_non_compliant_config():
    compliance = [{"ConfigRuleName": "rule-x", "ComplianceType": "NON_COMPLIANT",
                   "ResourceId": "res-1", "EvaluatedAt": "2026-01-01"}]
    findings = check_config_compliance(compliance)
    assert len(findings) == 1
    assert findings[0].control_id == "ITGC-CFG-01"
