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
    # What the owner waits on someone else for: listed, marked, not counted.
    assert answer["waitingCount"] == len(seeded["expectedWaitingRefs"]) == 1
    assert [row["ref"] for row in answer["items"] if row.get("waiting")] == seeded["expectedWaitingRefs"]
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
        decisions=inputs["decisions"],
        self_names=inputs["ownerNames"],
        now=datetime.fromisoformat(seeded["now"]),
    )
    assert _refs(pure["members"]) == _refs(answer["members"])
    assert pure["count"] == answer["count"]
    assert pure["waitingCount"] == answer["waitingCount"]
    assert [row["ref"] for row in pure["waitingItems"]] == seeded["expectedWaitingRefs"]


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
        assignment_read=before["assignmentRead"], meetings=before["meetings"],
        decisions=before["decisions"], self_names=before["ownerNames"], now=now,
    )
    result = compute_needs_you(**kwargs)
    assert sorted(_refs(result["members"])) == sorted(probe["expectedRefs"])
    assert result["count"] == probe["expectedCount"]
    # The mutant that omits deduplication is rejected by the same contract.
    mutant = compute_needs_you(**kwargs, dedup=lambda items, _now: list(items))
    assert mutant["count"] == probe["expectedMutantCount"]


def test_a_room_row_merged_by_the_aggregate_keeps_its_sources() -> None:
    """The Room aggregate merges two projections of one obligation
    (``rank_and_dedup``); the rule then deduplicates the Door and Room rows
    again. The second pass must keep the first pass's ``sources`` and
    ``dedupCount`` (the browser twin flattens the same way): the face shows
    "2 SOURCES" from them. #788 lost them: the merged row came back with
    ``dedupCount`` 1 and one source.
    """
    from holdspeak.services.attention_ranking import rank_and_dedup

    now = datetime(2026, 10, 4, 9, 0, 0)
    projections = [
        {"id": "p1:jira:KAN-7", "projectId": "p1", "source": "jira",
         "title": "KAN-7 Payments cut-over runbook", "why": "OVERDUE · 2D",
         "severity": "danger", "dueAt": "2026-10-02"},
        {"id": "p1:proposal:1", "projectId": "p1", "source": "proposal",
         "title": "Payments cut-over runbook", "why": "PROPOSED", "severity": "info"},
        {"id": "p1:github:9", "projectId": "p1", "source": "github",
         "title": "#9 Review the retry change", "why": "REVIEW", "severity": "warning"},
    ]
    aggregate_items = rank_and_dedup(projections, now)
    merged = next(row for row in aggregate_items if row["title"].startswith("KAN-7"))
    assert merged["dedupCount"] == 2

    result = compute_needs_you(door={}, room_items=aggregate_items, now=now)
    assert result["count"] == 2
    head = next(row for row in result["unmutedItems"] if row["title"].startswith("KAN-7"))
    assert head["dedupCount"] == 2, head
    assert {source["source"] for source in head["sources"]} == {"jira", "proposal"}, head
    single = next(row for row in result["unmutedItems"] if row["title"].startswith("#9"))
    assert single["dedupCount"] == 1 and len(single["sources"]) == 1, single
