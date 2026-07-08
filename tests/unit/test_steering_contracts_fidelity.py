"""Contract fidelity (HSM-26-01): the REAL Phase-87/88 responses validate
against the DeskOS-belt presence contracts.

The mobile contracts (`pm/roadmap/holdspeak-mobile/contracts/schemas/`)
are what the iPad renders from — "inherits, never redesigns". This
test builds the ACTUAL hub response objects from the real code and
validates them against those schemas, so a route that drifts from its
contract fails here, not on glass.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO / "pm" / "roadmap" / "holdspeak-mobile" / "contracts" / "schemas"


def _validator(schema_name: str):
    from referencing import Registry, Resource

    resources = [
        (json.loads(p.read_text())["$id"], Resource.from_contents(json.loads(p.read_text())))
        for p in SCHEMA_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(resources)
    schema_id = f"https://holdspeak.dev/contracts/v0/{schema_name}.schema.json"
    schema = registry.get_or_retrieve(schema_id).value.contents
    return jsonschema.Draft202012Validator(schema, registry=registry)


def _assert_valid(schema_name: str, instance: dict) -> None:
    errors = sorted(
        _validator(schema_name).iter_errors(instance), key=lambda e: list(e.path)
    )
    assert not errors, (
        f"{schema_name} drifted from its contract:\n  "
        + "\n  ".join(f"{'/'.join(map(str, e.path))}: {e.message}" for e in errors)
    )


def _runner(pane_id="%5"):
    return lambda argv, cwd=None: SimpleNamespace(
        stdout=f"{pane_id}\n", returncode=0, stderr=""
    )


def test_arming_grant_matches_the_contract() -> None:
    from holdspeak import coder_steering

    coder_steering.clear_grants()
    result = coder_steering.arm("claude:x", "hs:0.0", runner=_runner("%5"))
    _assert_valid("arming-grant", result)
    coder_steering.clear_grants()


def test_steer_result_matches_the_contract() -> None:
    from holdspeak import coder_steering

    coder_steering.clear_grants()
    coder_steering.arm("claude:x", "hs:0.0", runner=_runner("%9"))
    delivered = coder_steering.deliver(
        "claude:x", "hi", current_target="hs:0.0", agent="claude", submit=False,
        grounding_refs=["rails:story:HS-88-05"], runner=_runner("%9"),
        transport=lambda **k: None, audit=lambda **k: 7,
    )
    _assert_valid("steer-result", delivered)
    # A revoking refusal is the same contract.
    refused = coder_steering.deliver(
        "claude:x", "hi", current_target="hs:0.0", agent="claude",
        runner=_runner("%13"), transport=lambda **k: None, audit=lambda **k: 8,
    )
    _assert_valid("steer-result", refused)
    coder_steering.clear_grants()


def test_steering_audit_entry_matches_the_contract(tmp_path) -> None:
    # Build a REAL audit row through the db (SQLite stamps the ts), so the
    # test catches a ts that is not the contract's UTC-Z instant.
    from holdspeak.db.core import Database, reset_database

    reset_database()
    db = Database(tmp_path / "hs.db")
    db.steering.record(
        session_key="claude:x", agent="claude", pane_id="%5", text="hi",
        grounding=["rails:story:HS-88-05"], submit=False, outcome="delivered",
    )
    row = db.steering.list()[0].to_dict()
    _assert_valid("steering-audit-entry", row)
    # The contract's §2 rule: instants are UTC Z, not SQLite's naive format.
    assert row["ts"].endswith("Z") and "T" in row["ts"], row["ts"]
    reset_database()


def test_rails_grounding_block_ref_shape_matches_the_contract() -> None:
    # The wire ref the picker sends and the hydrator resolves.
    ref = {"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-05"}
    _assert_valid("rails-grounding-ref", ref)


def test_rails_journal_entry_matches_the_contract() -> None:
    from holdspeak import rails_observer

    batch = rails_observer.summarize_batch(
        [{"ts": "2026-07-08T10:00:00Z", "event": "story_status", "story": "HS-1", "repo": "code"}],
        summarize_fn=lambda s, u: "HS-1 shipped.",
    )
    # Mirror the route's entry shape.
    entry = {
        "id": "note_abc",
        "title": "Rails journal",
        "body_markdown": rails_observer.journal_body(batch),
        "created_at": "2026-07-08T10:00:00Z",
    }
    _assert_valid("rails-journal-entry", entry)


def test_remote_events_envelope_matches_the_contract() -> None:
    envelope = {
        "node": "walk-remote",
        "ts": "2026-07-08T10:00:00Z",
        "events": [{"ts": "2026-07-08T09:59:00Z", "event": "story_status", "story": "HS-1", "detail": {"to": "done"}}],
    }
    _assert_valid("rails-remote-events-envelope", envelope)
    # The contract rejects a file body, matching the route's runtime refusal.
    leaky = {"node": "beta", "events": [{"event": "x", "body_markdown": "the file"}]}
    errors = list(_validator("rails-remote-events-envelope").iter_errors(leaky))
    assert errors, "the envelope contract must reject a file-body event"


def test_peek_envelope_shape_matches_the_contract() -> None:
    # The route's envelope (built here the way api_coder_peek builds it).
    envelope = {
        "key": "claude:x", "agent": "claude", "stale": False,
        "awaiting_response": True, "question": "merge?", "updated_at": "2026-07-08T10:00:00Z",
        "grant": {"armed": True, "expires_in_seconds": 842},
        "peek": {"status": "live", "hash": "a" * 64, "lines": ["$ ok"]},
    }
    _assert_valid("coder-session-peek", envelope)


def test_the_committed_fixtures_validate() -> None:
    # The conformance fixtures the mobile validator ships must also pass here
    # (one source of truth, two runners).
    fixtures = json.loads(
        (SCHEMA_DIR.parent / "fixtures" / "steering-and-rails-sample.json").read_text()
    )
    for entry, schema in (
        ("coder_session_peek", "coder-session-peek"),
        ("arming_grant", "arming-grant"),
        ("steer_request", "steer-request"),
        ("steer_result_delivered", "steer-result"),
        ("steering_audit_entry", "steering-audit-entry"),
        ("rails_journal_entry", "rails-journal-entry"),
    ):
        _assert_valid(schema, fixtures[entry])
