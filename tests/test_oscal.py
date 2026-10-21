import hashlib
import json

from evidence_automation.cap_tracker import generate_caps  # noqa: F401  (package imports cleanly)
from evidence_automation.controls import run_all_checks
from evidence_automation.packager import package_evidence
from evidence_automation.providers import MockProvider


def _bundle(tmp_path, name):
    p = MockProvider()
    users, changes, compliance = p.get_iam_users(), p.get_change_records(), p.get_config_compliance()
    findings = run_all_checks(users, changes, compliance)
    return package_evidence(users, changes, compliance, findings, tmp_path, name), findings


def test_oscal_states_follow_exceptions_and_hashes_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1792540800")
    bundle, findings = _bundle(tmp_path, "run")
    doc = json.loads((bundle / "oscal" / "assessment-results.json").read_text(encoding="utf-8"))
    result = doc["assessment-results"]["results"][0]
    failing = {f.control_id for f in findings}
    for finding in result["findings"]:
        control = finding["title"].split(" -> ")[0]
        expected = "not-satisfied" if control in failing else "satisfied"
        assert finding["target"]["status"]["state"] == expected
    hashes = json.loads((bundle / "evidence_hashes.json").read_text(encoding="utf-8"))
    for name, digest in hashes.items():
        assert hashlib.sha256((bundle / name).read_bytes()).hexdigest() == digest
    assert len(result["observations"]) == 7


def test_bundle_is_reproducible(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1792540800")
    a, _ = _bundle(tmp_path, "a")
    b, _ = _bundle(tmp_path, "b")
    for f in sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file()):
        assert (a / f).read_bytes() == (b / f).read_bytes(), f
