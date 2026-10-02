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
