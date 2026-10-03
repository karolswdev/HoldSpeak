"""PHILO-13 H-A2: real producer and route boundaries for the oracle week."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from holdspeak.db import Database
from scripts.philo13_needs_you_fixture import (
    A1_ID,
    A1_ROOM_TASK,
    A1_TASK,
    A2_TASK,
    A3_ID,
    A4_ID,
    D1_ID,
    FAILED_MEETING_ID,
    seed_week,
)


REPO = Path(__file__).resolve().parents[2]


def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "oracle-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home, home / "holdspeak.db"


def _board_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    board = payload["door"]["board"]  # type: ignore[index]
    return [
        row
        for lane in ("overdue", "now", "waiting", "unassigned")
        for row in board[lane]  # type: ignore[index]
    ]


def test_seed_accepts_existing_empty_hub_and_refuses_oracle_reseed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    db = Database(db_path)
    db.close()

    seeded = seed_week(db_path, home=home)
    assert seeded["mode"] == "seed"
    assert set(seeded["before"]) >= {
        "door", "needsYou", "roomItems", "assignments", "meetings", "heartbeat",
    }
    assert seeded["mutation"] == {
        "method": "PATCH",
        "path": f"/api/all-action-items/{A1_ID}",
        "body": {"status": "done"},
    }
    assert seeded["expectedRefs"] == [
        A1_ID, A2_TASK, A3_ID, A4_ID, "blocker:engines", FAILED_MEETING_ID,
    ]
    assert seeded["ids"]["project"].startswith("proj-")
    assert seeded["ids"]["project"] != "philo13-a2-project"
    assert seeded["ids"]["mutedProject"].startswith("proj-")
    assert seeded["producerEvidence"]["oracleWiring"]["roomA2ActionItemId"] == seeded["ids"]["A2"]

    with pytest.raises(FileExistsError, match="oracle meeting IDs"):
        seed_week(db_path, home=home)

    reopened = Database(db_path)
    try:
        assert reopened.meetings.get_meeting("philo13-a2-meeting") is not None
        assert reopened.meetings.get_meeting("philo13-a2-failed-meeting") is not None
        room_item = reopened.projects.get_project_item(seeded["ids"]["A1Room"])
        assert room_item is not None
        assert room_item["title"] == A1_ROOM_TASK
        assert room_item["title"] != A1_TASK
        assert room_item["lifecycle"] == "planned"
        assert room_item["due_at"] > seeded["now"][:10]
    finally:
        reopened.close()


def test_export_reads_same_real_ids_and_mutates_a1_through_http_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    seeded = seed_week(db_path, home=home)

    from scripts.philo13_needs_you_fixture import export_week

    exported = export_week(db_path, home=home)
    assert exported["ids"] == seeded["ids"]
    assert exported["expectedRefs"] == seeded["expectedRefs"]
    assert exported["mutation"]["method"] == "PATCH"
    assert exported["mutation"]["path"] == f"/api/all-action-items/{seeded['ids']['A1']}"
    assert exported["mutation"]["status"] == 200

    before_rows = _board_rows(exported["before"])
    after_rows = _board_rows(exported["after"])
    assert seeded["ids"]["A1"] in {str(row["id"]) for row in before_rows}
    assert seeded["ids"]["A1"] not in {str(row["id"]) for row in after_rows}
    assert exported["before"]["roomItems"]
    a2_room = [row for row in exported["before"]["roomItems"] if row.get("ref") == A2_TASK]
    assert len(a2_room) == 1
    assert a2_room[0]["actionItemId"] == seeded["ids"]["A2"]
    assert A1_ROOM_TASK != A1_TASK
    assert not any(row.get("ref") == A1_ID for row in exported["before"]["roomItems"])
    assert any(str(row["id"]) == seeded["ids"]["A2"] for row in before_rows)
    assert not any(str(row["id"]) == D1_ID for row in before_rows)
    assert exported["before"]["needsYou"]["items"]


def test_dedup_probe_mints_same_title_door_and_room_rows_through_real_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Before this probe, the canonical week has no duplicate producer pair, so
    # a no-dedup browser mutant also returns six and escapes the C4 fence.
    home, db_path = _isolated(tmp_path, monkeypatch)

    from scripts.philo13_needs_you_fixture import dedup_probe

    probe = dedup_probe(db_path, home=home)
    assert probe["mode"] == "dedup-probe"
    assert probe["expectedRefs"] == [
        A1_ID, A2_TASK, A3_ID, A4_ID, "blocker:engines", FAILED_MEETING_ID,
    ]
    assert probe["expectedCount"] == 6
    assert probe["expectedMutantCount"] == 7

    evidence = probe["producerEvidence"]
    door = evidence["doorRoute"]
    room = evidence["roomRoute"]
    assert door["path"] == "/api/door"
    assert door["id"] == evidence["duplicateDoorRef"]
    assert door["title"] == A2_TASK
    assert room["path"] == "/api/desk/needs-you?fresh=1"
    assert room["ref"] == A2_TASK
    assert room["title"] == A2_TASK
    assert room["source"] == "commitment"
    assert room["projectId"] == evidence["duplicateProjectId"]
    assert room["actionItemId"] != evidence["duplicateDoorRef"]
    linked = evidence["linkedMeeting"]
    assert linked["route"] == (
        f"POST /api/projects/{evidence['duplicateProjectId']}/meetings/{linked['meetingId']}"
    )
    assert linked["projectId"] == evidence["duplicateProjectId"]
    assert linked["actionItemId"] == evidence["duplicateDoorRef"]
    assert linked["title"] == A2_TASK
    assert linked["success"] is True

    room_rows = [row for row in probe["before"]["roomItems"] if row.get("title") == A2_TASK]
    assert len(room_rows) == 1
    assert room_rows[0]["projectId"] == evidence["duplicateProjectId"]


def test_cli_stdout_is_json_and_export_keeps_seed_ids(tmp_path: Path) -> None:
    home = tmp_path / "cli-home"
    home.mkdir()
    db_path = home / "holdspeak.db"
    env = {**os.environ, "HOME": str(home), "PYTHONPATH": str(REPO)}

    def run(mode: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, str(REPO / "scripts/philo13_needs_you_fixture.py"), mode,
             "--db", str(db_path), "--home", str(home)],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert not completed.stderr
        return json.loads(completed.stdout)

    seeded = run("seed")
    exported = run("export")
    assert set(seeded) >= {"ids", "before", "mutation", "now", "producerEvidence"}
    assert exported["ids"] == seeded["ids"]
    assert exported["mutation"]["status"] == 200
