"""PHILO-9-06 fences for the closing-use driver (``scripts/philo9_room_job.py``).

Every input is a real producer's output: the Phase 5 rehearsal's retained
Codex logs (the zero-read fence's red), and this story's retained rehearsal
(Codex's own event logs and rollouts, the hub's recorded exchanges, the
readbacks through the contract). The reds are those records themselves and
deliberate mutations of copies of them.
"""
# History reads are parked: tests/_parked/history/tests/unit/test_philo9_room_job.py holds this file as it was, with the
# 25 test function(s) that read evidence archived on branch
# archive/evidence-2026-10-04 (pm/ARCHIVE.md).
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo9_room_job", REPO / "scripts/philo9_room_job.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

PHASE5_RUN = REPO / (
    "pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/"
    "final/20260925T001407Z-his-words-real"
)
STORY = REPO / "pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract"
SHOTS = STORY / "assets/story-06-shots"
#: Rehearsal one: its own audit refused the agent sessions' pairing (the
#: Codex ``status: failed`` defect) and it found the two catalogue gaps.
FIRST = SHOTS / "attempts/20260928T164015Z-room-job"
#: Rehearsal two, after the gaps were paid: completed, no blocker.
SECOND = SHOTS / "attempts/20260928T165409Z-room-job"
#: The FINAL closing run on merged main (PHILO-9-03's face): four sessions and the face.
RUN = SHOTS / "final/20260928T172621Z-room-job"


def _events(stage_dir: Path) -> list[dict[str, Any]]:
    return driver.read_events(stage_dir / "events.jsonl")


def _copy_run(tmp_path: Path) -> Path:
    target = tmp_path / RUN.name
    shutil.copytree(RUN, target, ignore=shutil.ignore_patterns("*.sqlite", "rehearsal-transcript.jsonl"))
    return target


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


# ── the zero-read fence (the Phase 7 implementation, one copy) ───────────


def test_the_driver_uses_the_phase7_fences_unchanged() -> None:
    assert driver.zero_read_findings is driver.p7.zero_read_findings
    assert driver.account_leak_findings is driver.p7.account_leak_findings


# ── the redaction and the leak fence (law XXX-12) ────────────────────────


# ── the fixture was fixed before the run ─────────────────────────────────


def test_the_story_fixture_words_are_ordinary() -> None:
    for stage, words in driver.load_fixture()["prompts"].items():
        assert driver.prompt_findings(words) == [], stage


# ── the sessions are isolated: fresh roots, distinct ids, no resume ──────


# ── the content checks compare the fixture's values ──────────────────────


def _owner_back() -> dict[str, Any]:
    return _json(RUN / "owner_job" / "readbacks.json")


# ── the face: the Room and the grant row after the job, as rendered ──────


def _room_face() -> dict[str, Any]:
    return _json(RUN / "observations" / "room.json")


