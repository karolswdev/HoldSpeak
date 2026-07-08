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

# HS-72-01 — the Primitive Framework sync kinds + the ChangeSet envelope.
CHANGESET = "https://holdspeak.dev/contracts/v0/changeset.schema.json"
PRIMITIVE_SCHEMAS = {
    "note": "https://holdspeak.dev/contracts/v0/note.schema.json",
    "kb": "https://holdspeak.dev/contracts/v0/kb.schema.json",
    "recipe": "https://holdspeak.dev/contracts/v0/recipe.schema.json",
    "chain": "https://holdspeak.dev/contracts/v0/chain.schema.json",
    "workflow": "https://holdspeak.dev/contracts/v0/workflow.schema.json",
    "directory": "https://holdspeak.dev/contracts/v0/directory.schema.json",
    "directory_membership": "https://holdspeak.dev/contracts/v0/directory-membership.schema.json",
    "profile": "https://holdspeak.dev/contracts/v0/profile.schema.json",
    "model": "https://holdspeak.dev/contracts/v0/model-manifest.schema.json",
}

# HSM-26-01 — the presence-class steering + rails shapes (Phase 87/88), keyed
# by the fixture entry that must validate against each schema.
STEERING_RAILS_SCHEMAS = {
    "coder_session_peek": "https://holdspeak.dev/contracts/v0/coder-session-peek.schema.json",
    "coder_session_peek_not_modified": "https://holdspeak.dev/contracts/v0/coder-session-peek.schema.json",
    "arming_grant": "https://holdspeak.dev/contracts/v0/arming-grant.schema.json",
    "steer_request": "https://holdspeak.dev/contracts/v0/steer-request.schema.json",
    "steer_result_delivered": "https://holdspeak.dev/contracts/v0/steer-result.schema.json",
    "steer_result_refused": "https://holdspeak.dev/contracts/v0/steer-result.schema.json",
    "steering_audit_entry": "https://holdspeak.dev/contracts/v0/steering-audit-entry.schema.json",
    "rails_grounding_ref": "https://holdspeak.dev/contracts/v0/rails-grounding-ref.schema.json",
    "rails_journal_entry": "https://holdspeak.dev/contracts/v0/rails-journal-entry.schema.json",
    "rails_remote_events_envelope": "https://holdspeak.dev/contracts/v0/rails-remote-events-envelope.schema.json",
}


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

    # HS-72-01 — the primitive kinds + the ChangeSet envelope (the sync wire).
    primitives = json.loads((FIXTURE_DIR / "primitives-sample.json").read_text())
    for kind, schema_id in PRIMITIVE_SCHEMAS.items():
        errs = _errors(_validator(schema_id, registry), primitives[kind])
        if errs:
            ok = False
            print(f"FAIL  {kind}: {len(errs)} error(s)")
            for e in errs:
                print(f"        - {e}")
        else:
            print(f"PASS  {kind}: validates against its schema (0 errors)")
    cs_errs = _errors(_validator(CHANGESET, registry), primitives["changeset"])
    if cs_errs:
        ok = False
        print(f"FAIL  changeset: {len(cs_errs)} error(s)")
        for e in cs_errs:
            print(f"        - {e}")
    else:
        print("PASS  changeset: envelope (incl. a tombstone) validates (0 errors)")

    # Negative (security invariant): a profile smuggling an api key MUST fail.
    leaky = dict(primitives["profile"])
    leaky["api_key"] = "sk-should-never-sync"
    leak_errs = _errors(_validator(PRIMITIVE_SCHEMAS["profile"], registry), leaky)
    if leak_errs:
        print(f"PASS  negative: profile with api_key rejected ({len(leak_errs)} error(s), as expected)")
    else:
        ok = False
        print("FAIL  negative: a profile carrying api_key passed validation (key-never-syncs broken)")

    # Negative (availability invariant): a model manifest smuggling a binary-shaped
    # field (path/url) MUST fail — the manifest syncs, the binary never does (HSM-16-08).
    smuggle = dict(primitives["model"])
    smuggle["path"] = "/Users/x/Models/gguf/q.gguf"
    smuggle_errs = _errors(_validator(PRIMITIVE_SCHEMAS["model"], registry), smuggle)
    if smuggle_errs:
        print(f"PASS  negative: model manifest with a path rejected ({len(smuggle_errs)} error(s), as expected)")
    else:
        ok = False
        print("FAIL  negative: a model manifest carrying a path passed validation (binary-never-syncs broken)")

    # Timestamps: every instant must be UTC Z-terminated (HSM-0-03 §2).
    tz_bad = _utc_z_violations(fixture) + _utc_z_violations(mir) + _utc_z_violations(primitives)
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
    for fname in ("meeting-sample.json", "mir-and-actuator-sample.json", "primitives-sample.json"):
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

    # HSM-26-01 — the presence-class steering + rails shapes (Phase 87/88).
    steering = json.loads((FIXTURE_DIR / "steering-and-rails-sample.json").read_text())
    for entry, schema_id in STEERING_RAILS_SCHEMAS.items():
        errs = _errors(_validator(schema_id, registry), steering[entry])
        if errs:
            ok = False
            print(f"FAIL  {entry}: {len(errs)} error(s)")
            for e in errs:
                print(f"        - {e}")
        else:
            print(f"PASS  {entry}: validates against its schema (0 errors)")

    # Negative (consent invariant): a steer request missing `text` MUST fail.
    steer_v = _validator(STEERING_RAILS_SCHEMAS["steer_request"], registry)
    no_text = {"submit": True}
    if _errors(steer_v, no_text):
        print("PASS  negative: steer request without text rejected (as expected)")
    else:
        ok = False
        print("FAIL  negative: a steer request without text passed validation")

    # Negative (reach invariant): a remote-events envelope smuggling a file
    # body MUST fail — the reach is events only (no repo contents cross).
    env_v = _validator(STEERING_RAILS_SCHEMAS["rails_remote_events_envelope"], registry)
    leaky_env = {"node": "beta", "events": [{"event": "x", "body_markdown": "the story file"}]}
    if _errors(env_v, leaky_env):
        print("PASS  negative: remote envelope carrying a file body rejected (as expected)")
    else:
        ok = False
        print("FAIL  negative: a remote envelope with a file body passed validation")

    # Timestamps: the steering/rails instants are UTC Z-terminated too.
    sr_tz = _utc_z_violations(steering)
    if sr_tz:
        ok = False
        print(f"FAIL  utc-z (steering/rails): {len(sr_tz)} violation(s)")
        for e in sr_tz:
            print(f"        - {e}")
    else:
        print("PASS  utc-z (steering/rails): all instants are UTC Z-terminated")

    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
