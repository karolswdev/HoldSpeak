"""PHILO-16 (C) -- Runs on: what the Switchboard reads and writes.

The board writes one group's whole chain per drop through the existing
``/api/inference/assignments/set`` (CAS), and reads the revision it must
present from the roster: tombstones included, so a job that only inherits
the Default for AI work can be patched without a lost-update guess.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from tests.unit.test_phase143_inference_assignments import _profile
from tests.unit.test_web_inference_assignment_routes import _client

OWNER = {"x-principal": "owner"}


def _rows(client: TestClient) -> dict[str, dict]:
    roster = client.get("/api/inference/assignments", headers=OWNER).json()
    return {row["id"]: row for row in roster["rows"]}


def test_roster_rows_carry_the_revision_a_write_must_present(tmp_path: Path) -> None:
    client = _client(tmp_path)
    rows = _rows(client)
    assert rows["global"]["expected_revision"] == 0
    assert all(row["expected_revision"] == 0 for row in rows.values())


def test_one_drop_writes_an_ordered_chain_for_a_group_in_one_call(tmp_path: Path) -> None:
    client = _client(tmp_path)
    db = client.app.state.assignment_test_db
    _profile(db, "runson-first")
    _profile(db, "runson-fallback")
    rows = _rows(client)
    saved = client.post(
        "/api/inference/assignments/set",
        headers=OWNER,
        json={
            "command_id": "runson-chain",
            "expected_revision": rows["thoughts_notes"]["expected_revision"],
            "scope": {"kind": "group", "group_id": "thoughts_notes"},
            "entries": [
                {"profile_id": "runson-first", "profile_revision": 1},
                {"profile_id": "runson-fallback", "profile_revision": 1},
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    assert [e["profile_id"] for e in saved.json()["entries"]] == ["runson-first", "runson-fallback"]
    after = _rows(client)["thoughts_notes"]
    assert after["inherited_from"] == "group"
    assert after["expected_revision"] == 1
    assert [e["profile_id"] for e in after["assignment"]["entries"]] == ["runson-first", "runson-fallback"]


def test_a_cleared_group_answers_its_tombstone_revision_not_zero(tmp_path: Path) -> None:
    """Undo of a first patch clears the group; the next patch must present
    the tombstone's revision, which the roster now says."""
    client = _client(tmp_path)
    db = client.app.state.assignment_test_db
    _profile(db, "runson-one")
    scope = {"kind": "group", "group_id": "thoughts_notes"}
    first = client.post(
        "/api/inference/assignments/set", headers=OWNER,
        json={"command_id": "runson-a", "expected_revision": 0, "scope": scope,
              "entries": [{"profile_id": "runson-one", "profile_revision": 1}]},
    )
    assert first.status_code == 200, first.text
    cleared = client.post(
        "/api/inference/assignments/clear", headers=OWNER,
        json={"command_id": "runson-undo", "expected_revision": 1, "scope": scope,
              "capability_id": "ask.answer"},
    )
    assert cleared.status_code == 200, cleared.text
    row = _rows(client)["thoughts_notes"]
    assert row["inherited_from"] is None
    assert row["expected_revision"] == 2
    # The stale guess (0) is refused: no lost update.
    stale = client.post(
        "/api/inference/assignments/set", headers=OWNER,
        json={"command_id": "runson-stale", "expected_revision": 0, "scope": scope,
              "entries": [{"profile_id": "runson-one", "profile_revision": 1}]},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "inference_assignment_revision_conflict"
    again = client.post(
        "/api/inference/assignments/set", headers=OWNER,
        json={"command_id": "runson-b", "expected_revision": row["expected_revision"],
              "scope": scope, "entries": [{"profile_id": "runson-one", "profile_revision": 1}]},
    )
    assert again.status_code == 200, again.text
    assert again.json()["revision"] == 3
