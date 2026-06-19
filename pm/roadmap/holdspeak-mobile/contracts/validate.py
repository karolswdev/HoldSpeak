#!/usr/bin/env python3
"""Validate the conformance fixtures against the holdspeak-contracts JSON Schemas.

HSM-0-02 / HSM-0-04. Loads every schema in ./schemas into a referencing registry
(keyed by $id so cross-file $refs resolve), validates each fixture entity against
its schema, and runs a negative check so a contract violation fails loudly.

Run:  uv run --with jsonschema python pm/roadmap/holdspeak-mobile/contracts/validate.py
Exit: 0 = all checks passed; 1 = a check failed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

# A bare ISO datetime (no timezone) — the contract (HSM-0-03 §2) forbids this on
# the wire; instants must be UTC with a Z suffix.
_BARE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$")
_ISO_LIKE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _utc_z_violations(node: object, path: str = "") -> list[str]:
    """Any ISO-datetime-shaped string that is not UTC Z-terminated is a violation."""
    out: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _utc_z_violations(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += _utc_z_violations(v, f"{path}/{i}")
    elif isinstance(node, str) and _ISO_LIKE.match(node) and not node.endswith("Z"):
        if _BARE_ISO.match(node) or not node.endswith("Z"):
            out.append(f"{path.lstrip('/')}: instant not UTC-Z ({node!r})")
    return out

HERE = Path(__file__).parent
SCHEMA_DIR = HERE / "schemas"
FIXTURE_DIR = HERE / "fixtures"

MEETING = "https://holdspeak.dev/contracts/v0/meeting.schema.json"
ARTIFACT = "https://holdspeak.dev/contracts/v0/artifact.schema.json"
INTEL_JOB = "https://holdspeak.dev/contracts/v0/intel-job.schema.json"
ACTUATOR = "https://holdspeak.dev/contracts/v0/actuator-proposal.schema.json"
INTENT_WINDOW = "https://holdspeak.dev/contracts/v0/intent-window.schema.json"


def _registry() -> Registry:
    resources = []
    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(schema_path.read_text())
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validator(schema_id: str, registry: Registry) -> Draft202012Validator:
    schema = registry.get_or_retrieve(schema_id).value.contents
    return Draft202012Validator(schema, registry=registry)


def _errors(validator: Draft202012Validator, instance: object) -> list[str]:
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(instance)]


def main() -> int:
    registry = _registry()
    fixture = json.loads((FIXTURE_DIR / "meeting-sample.json").read_text())
    mir = json.loads((FIXTURE_DIR / "mir-and-actuator-sample.json").read_text())
    meeting_v = _validator(MEETING, registry)
    artifact_v = _validator(ARTIFACT, registry)
    intel_job_v = _validator(INTEL_JOB, registry)
    actuator_v = _validator(ACTUATOR, registry)
    window_v = _validator(INTENT_WINDOW, registry)

    ok = True

    # Positive: the real desktop serialization validates with zero errors.
    for name, validator, instance in (
        ("meeting", meeting_v, fixture["meeting"]),
        ("artifact", artifact_v, fixture["artifact"]),
        ("intel_job", intel_job_v, fixture["intel_job"]),
        ("actuator_proposal", actuator_v, mir["actuator_proposal"]),
        ("intent_window[balanced]", window_v, mir["intent_window_balanced"]),
        ("intent_window[architect]", window_v, mir["intent_window_architect"]),
    ):
        errs = _errors(validator, instance)
        if errs:
            ok = False
            print(f"FAIL  {name}: {len(errs)} error(s)")
            for e in errs:
                print(f"        - {e}")
        else:
            print(f"PASS  {name}: validates against its schema (0 errors)")

    # Timestamps: every instant must be UTC Z-terminated (HSM-0-03 §2).
    tz_bad = _utc_z_violations(fixture) + _utc_z_violations(mir)
    if tz_bad:
        ok = False
        print(f"FAIL  utc-z: {len(tz_bad)} non-UTC-Z instant(s)")
        for e in tz_bad:
            print(f"        - {e}")
    else:
        print("PASS  utc-z: all instants are UTC Z-terminated")

    # Round-trip stability: each fixture is canonical (parse -> re-serialize ==
    # on-disk), so committed fixtures don't drift. The typed Swift Codable
    # round-trip is Phase 1's job; this is the JSON-canonical-form guard.
    rt_ok = True
    for fname in ("meeting-sample.json", "mir-and-actuator-sample.json"):
        raw = (FIXTURE_DIR / fname).read_text()
        canonical = json.dumps(json.loads(raw), indent=2) + "\n"
        if raw != canonical:
            rt_ok = False
            print(f"FAIL  round-trip: {fname} is not canonical (would drift on re-serialize)")
    print("PASS  round-trip: fixtures are canonical / stable" if rt_ok else "")
    ok = ok and rt_ok

    # MIR profile dimension: the two windows carry distinct profiles, both valid.
    pb = mir["intent_window_balanced"]["profile"]
    pa = mir["intent_window_architect"]["profile"]
    if pb != pa:
        print(f"PASS  mir-profile: distinct profiles carried ({pb} vs {pa})")
    else:
        ok = False
        print(f"FAIL  mir-profile: windows do not differ ({pb})")

    # Negative: a corrupted payload (bad enum + missing required) must fail.
    bad = json.loads(json.dumps(fixture["artifact"]))
    bad["status"] = "totally_invalid_status"
    del bad["title"]
    neg = _errors(artifact_v, bad)
    if neg:
        print(f"PASS  negative: corrupted artifact rejected ({len(neg)} error(s), as expected)")
    else:
        ok = False
        print("FAIL  negative: corrupted artifact passed validation (schema too loose)")

    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
