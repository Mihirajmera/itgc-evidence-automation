#!/usr/bin/env python3
"""CLI entry point for SOX ITGC evidence automation.

Usage:
    python cli.py                      # runs against local mock fixtures
    python cli.py --out evidence_packages
"""
from __future__ import annotations

import argparse

from evidence_automation.providers import MockProvider
from evidence_automation.controls import run_all_checks
from evidence_automation.packager import package_evidence
from evidence_automation.cap_tracker import generate_caps, write_cap_register


def main() -> None:
    parser = argparse.ArgumentParser(description="SOX ITGC audit evidence automation")
    parser.add_argument("--out", default="evidence_packages", help="output directory for evidence bundles")
    args = parser.parse_args()

    provider = MockProvider()
    iam_users = provider.get_iam_users()
    changes = provider.get_change_records()
    compliance = provider.get_config_compliance()

    findings = run_all_checks(iam_users, changes, compliance)
    bundle_dir = package_evidence(iam_users, changes, compliance, findings, args.out)

    caps = generate_caps(findings)
    write_cap_register(caps, bundle_dir / "cap_register.csv")

    print(f"Evidence bundle: {bundle_dir}")
    print(f"Findings: {len(findings)}  |  CAPs generated: {len(caps)}")
    for f in findings:
        print(f"  [{f.severity:6}] {f.control_id}  {f.resource}: {f.description}")


if __name__ == "__main__":
    main()
