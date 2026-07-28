"""Evidence source providers.

MockProvider reads from local JSON fixtures so the tool runs end-to-end with zero
credentials, for demos and tests. AWSProvider is a thin boto3-backed implementation
for pointing this at a real AWS account/ServiceNow instance in production — it is not
exercised in this repo since no live credentials are configured here.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class EvidenceProvider(ABC):
    @abstractmethod
    def get_iam_users(self) -> list[dict]: ...

    @abstractmethod
    def get_change_records(self) -> list[dict]: ...

    @abstractmethod
    def get_config_compliance(self) -> list[dict]: ...


class MockProvider(EvidenceProvider):
    """Reads synthetic evidence from local JSON fixtures. Default provider for this repo."""

    def get_iam_users(self) -> list[dict]:
        return json.loads((FIXTURES_DIR / "iam_users.json").read_text())

    def get_change_records(self) -> list[dict]:
        return json.loads((FIXTURES_DIR / "change_management.json").read_text())

    def get_config_compliance(self) -> list[dict]:
        return json.loads((FIXTURES_DIR / "config_compliance.json").read_text())


class AWSProvider(EvidenceProvider):
    """Live AWS-backed provider (IAM, AWS Config). Requires `pip install boto3` and
    valid AWS credentials with iam:ListUsers / config:DescribeComplianceByConfigRule
    permissions. Change management records still come from an external system
    (ServiceNow/Jira) — wire `get_change_records` to that API for your environment.
    """

    def __init__(self, region: str = "us-east-1"):
        import boto3  # imported lazily so boto3 is optional unless this provider is used
        self._iam = boto3.client("iam", region_name=region)
        self._config = boto3.client("config", region_name=region)

    def get_iam_users(self) -> list[dict]:
        users = []
        paginator = self._iam.get_paginator("list_users")
        for page in paginator.paginate():
            for u in page["Users"]:
                mfa = self._iam.list_mfa_devices(UserName=u["UserName"])["MFADevices"]
                users.append({
                    "UserName": u["UserName"],
                    "MFAEnabled": len(mfa) > 0,
                    "LastActivity": str(u.get("PasswordLastUsed", "")),
                })
        return users

    def get_change_records(self) -> list[dict]:
        raise NotImplementedError(
            "Wire this to your change management system (ServiceNow/Jira) API."
        )

    def get_config_compliance(self) -> list[dict]:
        results = []
        rules = self._config.describe_config_rules()["ConfigRules"]
        for rule in rules:
            resp = self._config.get_compliance_details_by_config_rule(
                ConfigRuleName=rule["ConfigRuleName"]
            )
            for r in resp.get("EvaluationResults", []):
                results.append({
                    "ConfigRuleName": rule["ConfigRuleName"],
                    "ComplianceType": r["ComplianceType"],
                    "ResourceId": r["EvaluationResultIdentifier"]["EvaluationResultQualifier"]["ResourceId"],
                    "EvaluatedAt": str(r.get("ResultRecordedTime", "")),
                })
        return results
