"""OSCAL 1.1.2 assessment results for an ITGC evidence bundle.

One observation per ITGC control (with the SHA-256 of the raw evidence it was tested on) and
one finding per mapped NIST SP 800-53 Rev. 5 control objective: `satisfied` when the ITGC
control has no exceptions, `not-satisfied` otherwise. IDs are deterministic, so the same
evidence always produces the same document.
"""
from __future__ import annotations

import uuid

from .controls import Finding

NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Mihirajmera/itgc-evidence-automation")

# ITGC control -> (evidence file it is tested on, NIST SP 800-53 Rev. 5 controls). My mapping.
CONTROL_MAP = {
    "ITGC-AM-01": ("raw_iam_users.json", ["IA-2(1)", "IA-2(2)"]),
    "ITGC-AM-02": ("raw_iam_users.json", ["AC-2(3)", "PS-4"]),
    "ITGC-AM-03": ("raw_iam_users.json", ["AC-6", "AC-2(7)"]),
    "ITGC-CM-01": ("raw_change_management.json", ["CM-3"]),
    "ITGC-CM-02": ("raw_change_management.json", ["AC-5", "CM-5"]),
    "ITGC-CM-03": ("raw_change_management.json", ["CM-3(2)", "SA-11"]),
    "ITGC-CFG-01": ("raw_config_compliance.json", ["CM-6", "CM-2"]),
}


def _uid(*parts) -> str:
    return str(uuid.uuid5(NS, "|".join(str(p) for p in parts)))


def oscal_id(control: str) -> str:
    """'IA-2(1)' -> 'ia-2.1', the control-id format of the NIST 800-53 OSCAL catalog."""
    return control.lower().replace("(", ".").replace(")", "")


def assessment_results(coverage, findings: list[Finding], hashes: dict[str, str], collected: str) -> dict:
    by_control: dict[str, list[Finding]] = {}
    for f in findings:
        by_control.setdefault(f.control_id, []).append(f)

    observations, oscal_findings, reviewed = [], [], set()
    for control_id, area, objective in coverage:
        evidence_file, nist = CONTROL_MAP.get(control_id, (None, []))
        exceptions = by_control.get(control_id, [])
        state = "satisfied" if not exceptions else "not-satisfied"
        obs = _uid("observation", control_id, hashes.get(evidence_file, ""))
        observations.append({
            "uuid": obs,
            "title": control_id,
            "description": f"{area}: {objective}. {len(exceptions)} exception(s).",
            "methods": ["TEST"],
            "types": ["control-objective"],
            "props": [{"name": "exceptions", "value": str(len(exceptions))}]
                     + [{"name": "exception", "value": f"{f.resource}: {f.description}"} for f in exceptions],
            "relevant-evidence": ([{"href": evidence_file, "description": f"sha256 {hashes[evidence_file]}"}]
                                  if evidence_file in hashes else []),
            "collected": collected,
        })
        for nist_control in nist:
            reviewed.add(oscal_id(nist_control))
            oscal_findings.append({
                "uuid": _uid("finding", control_id, nist_control, state),
                "title": f"{control_id} -> {nist_control}",
                "description": objective,
                "target": {"type": "objective-id", "target-id": f"{oscal_id(nist_control)}_obj",
                           "status": {"state": state}},
                "related-observations": [{"observation-uuid": obs}],
            })

    digest = "|".join(sorted(hashes.values()))
    return {"assessment-results": {
        "uuid": _uid("assessment-results", digest),
        "metadata": {"title": "SOX ITGC control assessment", "last-modified": collected,
                     "version": "1.0", "oscal-version": "1.1.2"},
        "import-ap": {"href": "#"},
        "results": [{
            "uuid": _uid("result", digest),
            "title": "Automated ITGC control testing",
            "description": "Access, change and configuration management controls tested against collected evidence.",
            "start": collected,
            "end": collected,
            "reviewed-controls": {"control-selections": [
                {"include-controls": [{"control-id": c} for c in sorted(reviewed)]}]},
            "observations": observations,
            "findings": oscal_findings,
        }],
    }}
