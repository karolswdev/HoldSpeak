"""PHILO-10-06 fences for the closing-use driver (``scripts/philo10_send_job.py``).

Every input is a real producer's output: the retained FINAL run (the two real
sends: Codex's own event logs and rollouts, the hub's recorded exchanges, the
readbacks through the contract, the independent read-backs), the retained
rehearsal, and the tracked exactly-once ledger. The reds are deliberate
mutations of copies of them. Nothing here sends, boots a hub or reads the
network.
"""
# History reads are parked: tests/_parked/history/tests/unit/test_philo10_send_job.py holds this file as it was, with the
# 16 test function(s) that read evidence archived on branch
# archive/evidence-2026-10-04 (pm/ARCHIVE.md).
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo10_send_job", REPO / "scripts/philo10_send_job.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

STORY = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels"
SHOTS = STORY / "assets/story-06-shots"
#: The FINAL run: the two real sends (folder + issue 699), both sessions, the face.
RUN = SHOTS / "final/20260929T184651Z-send-job-real"
LEDGER = STORY / "assets/story-06-real-sends.json"


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _fixture() -> dict[str, Any]:
    return driver.load_fixture()


def _copy_run(tmp_path: Path) -> Path:
    target = tmp_path / RUN.name
    shutil.copytree(RUN, target, ignore=shutil.ignore_patterns("*.sqlite", "rehearsal-transcript.jsonl", "*.png"))
    return target


# ── the driver reuses the Phase 7 fences (one implementation) ────────────


def test_the_driver_uses_the_phase7_fences_unchanged() -> None:
    assert driver.zero_read_findings is driver.p7.zero_read_findings
    assert driver.account_leak_findings is driver.p7.account_leak_findings
    assert driver.redact_run is driver.p7.redact_run


# ── exactly one send per target (the guard, three independent reads) ─────


def test_the_guard_passes_a_target_with_no_send(tmp_path: Path) -> None:
    folder = tmp_path / "HoldSpeak"
    folder.mkdir()
    (folder / "other.md").write_text("another file\n")
    found = driver.exactly_once_findings(_fixture(), ledger=tmp_path / "none.json", folder=folder,
                                         comments=lambda: [{"body": "a comment", "html_url": "u"}])
    assert found == []


def test_the_guard_refuses_a_target_the_ledger_names(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    driver.record_real_press(ledger, {"target": "github", "pressed_at": "2026-09-29T00:00:00+00:00"})
    fixture = _fixture()
    assert driver.exactly_once_findings(fixture, ledger=ledger, folder=tmp_path, targets=("file",)) == []
    found = driver.exactly_once_findings(fixture, ledger=ledger, folder=tmp_path, targets=("github",))
    assert len(found) == 1 and found[0].startswith("github: the ledger records a real send")


def test_the_guard_refuses_a_folder_that_holds_the_bytes(tmp_path: Path) -> None:
    (tmp_path / "2026-09-29-harbor-cutover-r1-abcdef12.md").write_bytes(driver.body_bytes(_fixture()))
    found = driver.exactly_once_findings(_fixture(), ledger=tmp_path / "none.json", folder=tmp_path)
    assert len(found) == 1 and "already holds the fixture's bytes" in found[0]


def test_the_guard_refuses_an_issue_that_carries_the_marker(tmp_path: Path) -> None:
    fixture = _fixture()
    comments = [{"body": "hello", "html_url": "a"}, {"body": f"x\n{fixture['marker']}\n", "html_url": "b"}]
    found = driver.exactly_once_findings(fixture, ledger=tmp_path / "none.json", folder=tmp_path,
                                         comments=lambda: comments)
    assert found == ["github: b already carries the fixture's marker"]


# ── the final run: sessions, receipts, content, read-backs ────────────────


# ── the reds: mutations of copies of the real records ─────────────────────


def _digest() -> str:
    return hashlib.sha256(driver.body_bytes(_fixture())).hexdigest()


