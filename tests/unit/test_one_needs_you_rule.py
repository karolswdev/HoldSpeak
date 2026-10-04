"""The one ``needs you`` rule on the hub: the port cannot drift from the browser twin.

``scripts/philo13_needs_you_fixture.py`` mints the oracle week through the real
producers (routes, services, the intel queue). ``web/src/desk/needsYou.test.ts``
asserts that ``computeNeedsYou`` returns ``expectedRefs`` over that week; this
file asserts the same refs from ``needs_you_membership`` -- the pure function
over the exported inputs AND the ``/api/desk/needs-you`` answer itself.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.services.needs_you_membership import compute_needs_you
from scripts.philo13_needs_you_fixture import _inputs, dedup_probe, seed_week


def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home, home / "holdspeak.db"


def _refs(members: list[dict[str, str]]) -> list[str]:
    return [member["ref"] for member in members]


def test_the_hub_answer_is_the_oracle_week(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    seeded = seed_week(db_path, home=home)
    expected = seeded["expectedRefs"]

    db = Database(db_path)
    try:
        inputs = _inputs(db, datetime.fromisoformat(seeded["now"]))
    finally:
        db.close()

    answer = inputs["needsYou"]
    # The route's answer: the six members, and a count that is their number.
    assert sorted(_refs(answer["members"])) == sorted(expected)
    assert answer["count"] == len(expected) == 6
    assert answer["mutedCount"] == 1
    assert answer["sourceErrors"] == {}

    # The pure function over the same inputs the browser twin reads.
    pure = compute_needs_you(
        door=inputs["door"],
        room_items=inputs["roomItems"],
        muted_project_ids=inputs["mutedProjects"],
        assignments=inputs["assignments"],
        assignment_read=inputs["assignmentRead"],
        meetings=inputs["meetings"],
        now=datetime.fromisoformat(seeded["now"]),
    )
    assert _refs(pure["members"]) == _refs(answer["members"])
    assert pure["count"] == answer["count"]


def test_the_hub_rule_deduplicates_as_the_browser_twin_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    probe = dedup_probe(db_path, home=home)
    before = probe["before"]
    now = datetime.fromisoformat(probe["now"])
    kwargs = dict(
        door=before["door"], room_items=before["roomItems"],
        muted_project_ids=before["mutedProjects"], assignments=before["assignments"],
        assignment_read=before["assignmentRead"], meetings=before["meetings"], now=now,
    )
    result = compute_needs_you(**kwargs)
    assert sorted(_refs(result["members"])) == sorted(probe["expectedRefs"])
    assert result["count"] == probe["expectedCount"]
    # The mutant that omits deduplication is rejected by the same contract.
    mutant = compute_needs_you(**kwargs, dedup=lambda items, _now: list(items))
    assert mutant["count"] == probe["expectedMutantCount"]
