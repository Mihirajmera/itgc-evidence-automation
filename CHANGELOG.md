# Changelog

## Unreleased

- Evidence bundles include OSCAL 1.1.2 assessment results (one finding per mapped NIST 800-53 control) and SHA-256 hashes of the raw evidence.
- Reproducible bundles: deterministic OSCAL IDs, `SOURCE_DATE_EPOCH` for timestamps, `--name` for the bundle folder, LF line endings.

## 1.0.0 (2026-10-17)

First tagged release. SOX ITGC evidence collection for access, change and configuration controls, with an audit bundle and Corrective Action Plan register.

- CI on Python 3.11 / current Terraform tooling with every GitHub Action pinned to a commit SHA
- Dependencies pinned by version and hash (`requirements.in` → `requirements.txt`)
- CodeQL, OpenSSF Scorecard and Dependabot
- Security policy with private vulnerability reporting
