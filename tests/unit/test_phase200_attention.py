"""HS-200-15 -- actionable attention with controlled notifications.

Planned suite: ``phase200_attention``.

  AC2  the ranking is a pure function over observable facts, with a
       deterministic tie-break (TestRanking).
  AC3  duplicate projections of one obligation collapse to ONE row with
       traceable sources (TestDedup).
  AC1/2/3 the aggregate wires both (TestAggregateWiring).
  AC4  the five notification transitions are explicit, each a fence
       (TestNotificationTransitions): changed item with the SAME count,
       quiet hours (hold, then deliver once), mute, restart, recovery
       after a failed source.
  AC5  a failed source never clears known work and an empty PARTIAL
       result is never an all-clear (TestNoFalseAllClear).

Run:
    HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \\
        tests/unit/test_phase200_attention.py
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.attention_ranking import (
    RANK_CLASSES,
    attention_class,
    dedup_items,
    normalize_title,
    projection_ref,
    rank_and_dedup,
    rank_items,
    sort_key,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "attention_ranking.json"
from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate

NOW = datetime(2026, 9, 7, 9, 12, 0)
OWNER = Principal(PrincipalKind.OWNER, "test")


def _item(
    ident: str,
    *,
    title: str = "",
    why: str = "",
    since: str = "",
    due_at: str | None = None,
    severity: str = "info",
    project: str = "p1",
    source: str = "github",
) -> dict[str, Any]:
    return {
        "id": ident,
        "projectId": project,
        "projectName": project.upper(),
        "title": title or ident,
        "why": why,
        "since": since,
        "ageToken": since,
        "dueAt": due_at,
        "severity": severity,
        "source": source,
    }


# ── AC2: the ranking ────────────────────────────────────────────────


class TestRanking:
    def test_the_five_classes_in_the_ratified_order(self) -> None:
        assert RANK_CLASSES == ("overdue", "due_today", "not_run", "no_due_date", "waiting")

    def test_classes_rank_overdue_then_due_today_then_not_run_then_no_due_then_waiting(self) -> None:
        items = [
            _item("w", why="WAITING ON YOUR REVIEW · 3d", since="2026-09-04T09:00:00"),
            _item("n", why="CI RED", since="2026-09-07T08:32:00"),
            _item("r", why="NOT RUN · 2 DAYS", since="2026-09-05T09:00:00"),
            _item("t", why="DUE TODAY", due_at="2026-09-07T17:00:00"),
            _item("o", why="OVERDUE · 2 DAYS", due_at="2026-09-05"),
        ]
        ranked = rank_items(items, NOW)
        assert [row["id"] for row in ranked] == ["o", "t", "r", "n", "w"]
        assert [row["rankClass"] for row in ranked] == list(RANK_CLASSES)
        assert [row["rank"] for row in ranked] == [1, 2, 3, 4, 5]

    def test_a_due_date_decides_before_the_reason_token(self) -> None:
        # A row whose reason says WAITING but whose due date is yesterday
        # is overdue: the observable fact outranks the phrase.
        assert attention_class(_item("x", why="WAITING", due_at="2026-09-06"), NOW) == "overdue"
        assert attention_class(_item("x", why="WAITING", due_at="2026-09-07"), NOW) == "due_today"
        assert attention_class(_item("x", why="WAITING", due_at="2026-09-09"), NOW) == "waiting"

    def test_within_class_orders_are_the_ratified_ones(self) -> None:
        overdue = rank_items([
            _item("a", why="OVERDUE · 1 DAYS", due_at="2026-09-06"),
            _item("b", why="OVERDUE · 4 DAYS", due_at="2026-09-03"),
        ], NOW)
        assert [r["id"] for r in overdue] == ["b", "a"], "most overdue first"

        due_today = rank_items([
            _item("a", due_at="2026-09-07T16:00:00"),
            _item("b", due_at="2026-09-07T10:00:00"),
        ], NOW)
        assert [r["id"] for r in due_today] == ["b", "a"], "earliest due time first"

        not_run = rank_items([
            _item("a", why="NOT RUN", since="2026-09-06T09:00:00"),
            _item("b", why="NOT RUN", since="2026-09-02T09:00:00"),
        ], NOW)
        assert [r["id"] for r in not_run] == ["b", "a"], "oldest meeting first"

        no_due = rank_items([
            _item("a", why="CI RED", since="2026-09-06T09:00:00"),
            _item("b", why="CHECKS FAILING", since="2026-09-07T08:32:00"),
        ], NOW)
        assert [r["id"] for r in no_due] == ["b", "a"], "most recently changed first"

        waiting = rank_items([
            _item("a", why="WAITING", since="2026-09-06T09:00:00"),
            _item("b", why="WAITING", since="2026-09-04T09:00:00"),
        ], NOW)
        assert [r["id"] for r in waiting] == ["b", "a"], "longest waiting first"

    def test_severity_is_not_a_sort_key(self) -> None:
        # A danger row with no due date never outranks an info row that is
        # overdue: severity rides the token, it does not reorder a class.
        ranked = rank_items([
            _item("loud", why="CI RED", severity="danger", since="2026-09-07T09:00:00"),
            _item("quiet", why="OVERDUE · 1 DAYS", severity="info", due_at="2026-09-06"),
        ], NOW)
        assert [r["id"] for r in ranked] == ["quiet", "loud"]

    def test_tie_break_is_the_stable_id_and_the_order_is_deterministic(self) -> None:
        items = [_item(f"id-{n:02d}", why="CI RED", since="2026-09-07T08:00:00")
                 for n in range(12)]
        expected = [f"id-{n:02d}" for n in range(12)]
        for seed in range(5):
            shuffled = list(items)
            random.Random(seed).shuffle(shuffled)
            assert [r["id"] for r in rank_items(shuffled, NOW)] == expected

    def test_an_unknown_time_sorts_last_in_its_class(self) -> None:
        ranked = rank_items([
            _item("unknown", why="WAITING", since=""),
            _item("known", why="WAITING", since="2026-09-01T09:00:00"),
        ], NOW)
        assert [r["id"] for r in ranked] == ["known", "unknown"]

    def test_rank_items_does_not_mutate_its_input(self) -> None:
        source = [_item("a", why="CI RED")]
        before = dict(source[0])
        rank_items(source, NOW)
        assert source[0] == before

    def test_sort_key_is_the_complete_key(self) -> None:
        rank, within, ident = sort_key(_item("z", why="OVERDUE", due_at="2026-09-05"), NOW)
        assert rank == 0 and ident == "z"
        assert within == datetime(2026, 9, 5).timestamp()


# ── AC3: the dedup ──────────────────────────────────────────────────


class TestDedup:
    def test_three_projections_of_one_obligation_are_one_row(self) -> None:
        watch = _item("p1:jira:KAN-7", title="KAN-7 Payments cut-over runbook",
                      why="OVERDUE · 2 DAYS", due_at="2026-09-05",
                      severity="danger", source="jira")
        meeting = _item("proposal:abc", title="Payments cut-over runbook",
                        why="PROPOSED · Standup", since="2026-09-06T11:31:00",
                        source="proposal")
        person = _item("p1:commitment:runbook", title="payments  cut-over runbook",
                       why="WAITING ON PRIYA", since="2026-09-04T09:00:00",
                       source="commitment")
        rows = dedup_items([meeting, person, watch], NOW)
        assert len(rows) == 1, rows
        row = rows[0]
        # The head is the most urgent projection; the row keeps ITS id.
        assert row["id"] == "p1:jira:KAN-7"
        assert row["dedupCount"] == 3
        assert [s["source"] for s in row["sources"]] == ["jira", "proposal", "commitment"]
        assert {s["id"] for s in row["sources"]} == {
            "p1:jira:KAN-7", "proposal:abc", "p1:commitment:runbook",
        }
        assert row["severity"] == "danger"

    def test_the_same_title_in_two_projects_is_two_obligations(self) -> None:
        rows = dedup_items([
            _item("a", title="CI failing on main", project="p1"),
            _item("b", title="CI failing on main", project="p2"),
        ], NOW)
        assert len(rows) == 2
        assert all(r["dedupCount"] == 1 for r in rows)

    def test_a_projection_without_a_project_joins_the_one_project_that_names_it(self) -> None:
        rows = dedup_items([
            _item("door", title="Priya confirms the freeze window", project="",
                  why="OVERDUE · 1D", source="action_item"),
            _item("p1:cmt", title="Priya confirms the freeze window", project="p1",
                  why="DUE TODAY", due_at="2026-09-07", source="commitment"),
        ], NOW)
        assert len(rows) == 1
        assert rows[0]["dedupCount"] == 2

    def test_a_projection_without_a_project_stands_alone_when_several_projects_name_it(self) -> None:
        rows = dedup_items([
            _item("door", title="Cut-over sequencing", project=""),
            _item("p1", title="Cut-over sequencing", project="p1"),
            _item("p2", title="Cut-over sequencing", project="p2"),
        ], NOW)
        assert len(rows) == 3

    def test_normalisation_strips_a_leading_ref_case_and_spacing(self) -> None:
        assert normalize_title("KAN-7 Payments cut-over runbook") == "payments cut-over runbook"
        assert normalize_title("#612 Rig settles  animations") == "rig settles animations"
        assert normalize_title("  Rig Settles Animations ") == "rig settles animations"
        assert normalize_title("") == ""
        # `lower`, not `casefold`: mirrors JavaScript's toLowerCase (P1-1).
        assert normalize_title("Straße cutover") == "straße cutover"
        assert projection_ref({"title": "KAN-7 Runbook"}) == "KAN-7"
        assert projection_ref({"title": "#612 Rig"}) == "#612"
        assert projection_ref({"title": "Runbook"}) == ""

    def test_counsel_probe_1_distinct_obligations_never_merge(self) -> None:
        """Counsel P0-1: KAN-7 and KAN-12 share a title and a source; they
        are two tickets.  #612 and #640 likewise.  4 obligations in, 4 out."""
        rows = dedup_items([
            _item("p1:jira:KAN-7", title="KAN-7 Rotate the staging credentials",
                  why="OVERDUE · 2 DAYS", due_at="2026-09-05", source="jira", severity="danger"),
            _item("p1:jira:KAN-12", title="KAN-12 Rotate the staging credentials",
                  why="OVERDUE · 1 DAYS", due_at="2026-09-06", source="jira", severity="danger"),
            _item("p1:github:612", title="#612 Fix flaky test",
                  why="WAITING ON YOUR REVIEW · 3d", since="2026-09-04T09:00:00", source="github"),
            _item("p1:github:640", title="#640 Fix flaky test",
                  why="WAITING ON YOUR REVIEW · 1d", since="2026-09-06T09:00:00", source="github"),
        ], NOW)
        assert [r["id"] for r in rows] == [
            "p1:jira:KAN-7", "p1:jira:KAN-12", "p1:github:612", "p1:github:640",
        ]
        assert all(r["dedupCount"] == 1 for r in rows)

    def test_the_true_cross_source_case_is_one_row_with_two_openable_sources(self) -> None:
        rows = dedup_items([
            _item("p1:jira:KAN-7", title="KAN-7 Rotate the staging credentials",
                  why="OVERDUE · 2 DAYS", due_at="2026-09-05", source="jira", severity="danger"),
            _item("p1:jira:KAN-12", title="KAN-12 Rotate the staging credentials",
                  why="OVERDUE · 1 DAYS", due_at="2026-09-06", source="jira", severity="danger"),
            _item("proposal:1", title="Rotate the staging credentials",
                  why="PROPOSED · STANDUP", since="2026-09-06T11:40:00", source="proposal"),
        ], NOW)
        # The proposal (no ref) joins the FIRST cluster it may merge with;
        # KAN-12 stays its own obligation.
        assert [r["id"] for r in rows] == ["p1:jira:KAN-7", "p1:jira:KAN-12"]
        head = rows[0]
        assert head["dedupCount"] == 2
        assert [s["source"] for s in head["sources"]] == ["jira", "proposal"]
        # Every projection keeps its own title and its own way in.
        assert [s["title"] for s in head["sources"]] == [
            "KAN-7 Rotate the staging credentials", "Rotate the staging credentials",
        ]
        assert head["sources"][0]["id"] == "p1:jira:KAN-7"
        assert head["sources"][1]["id"] == "proposal:1"

    def test_same_ref_across_sources_merges_and_different_refs_do_not(self) -> None:
        same = dedup_items([
            _item("a", title="KAN-7 Runbook", source="jira"),
            _item("b", title="KAN-7 Runbook", source="commitment"),
        ], NOW)
        assert len(same) == 1 and same[0]["dedupCount"] == 2
        different = dedup_items([
            _item("a", title="KAN-7 Runbook", source="jira"),
            _item("b", title="KAN-9 Runbook", source="commitment"),
        ], NOW)
        assert len(different) == 2

    def test_the_shared_fixture_ranks_and_groups_as_the_browser_does(self) -> None:
        """Counsel P1-1: ONE fixture, consumed by this suite and by
        web/src/desk/attention.test.ts."""
        import json
        fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
        now = datetime.fromisoformat(fx["now"])
        rows = rank_and_dedup(fx["items"], now)
        assert [r["id"] for r in rows] == fx["expected_order"]
        groups = {r["id"]: [s["id"] for s in r["sources"]] for r in rows}
        assert groups == fx["expected_groups"]
        for raw, expected in fx["normalize"].items():
            assert normalize_title(raw) == expected

    def test_a_merged_row_is_remembered_only_when_every_projection_is(self) -> None:
        fresh = _item("a", title="One thing", why="CI RED", since="2026-09-07T08:00:00")
        remembered = {**_item("b", title="one thing", why="WAITING",
                              since="2026-09-01T08:00:00", source="commitment"),
                      "fromLastObservation": True, "observedAt": "2026-09-07T08:41:00"}
        [row] = dedup_items([fresh, remembered], NOW)
        assert "fromLastObservation" not in row

        older = {**_item("c", title="one thing", why="WAITING",
                         since="2026-09-02T08:00:00", source="proposal"),
                 "fromLastObservation": True, "observedAt": "2026-09-06T08:41:00"}
        [row] = dedup_items([remembered, older], NOW)
        assert row["fromLastObservation"] is True
        assert row["observedAt"] == "2026-09-07T08:41:00"

    def test_every_row_carries_its_sources_even_when_alone(self) -> None:
        [row] = dedup_items([_item("solo", title="Solo", why="CI RED")], NOW)
        assert row["dedupCount"] == 1
        assert row["sources"][0]["id"] == "solo"


# ── the aggregate wires both ────────────────────────────────────────


def _room_with(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "observed_at": "2026-09-07T09:00:00",
        "needsYou": {"state": "ok", "items": items, "count": len(items)},
        "sources": {"state": "ok", "items": [], "count": 0},
        "meetings": {"state": "ok", "items": []},
        "commitments": {"state": "ok", "items": []},
    }


class TestAggregateWiring:
    def test_items_come_back_ranked_with_class_sources_and_facts(self) -> None:
        def list_projects(principal, filters):
            return [{"id": "p1", "name": "Q4 Platform"}]

        def room(principal, project_id):
            return _room_with([
                {"source": "github", "title": "#612 Rig settles animations",
                 "why": "WAITING ON YOUR REVIEW · 3d", "since": "2026-09-04T09:00:00",
                 "url": "https://x/612", "severity": "warning"},
                {"source": "jira", "title": "KAN-7 Payments cut-over runbook",
                 "why": "OVERDUE · 2 DAYS", "since": "2026-09-05",
                 "due_at": "2026-09-05", "url": "https://x/KAN-7", "severity": "danger"},
                {"source": "github", "title": "CI failing on main", "why": "CI RED",
                 "since": "2026-09-07T08:32:00", "url": "https://x/ci",
                 "severity": "danger"},
            ])

        agg = build_aggregate(list_projects=list_projects, room=room,
                              principal=OWNER, now=NOW, last_known=LastKnownStore())
        ids = [row["id"] for row in agg["items"]]
        assert ids == [
            "p1:jira:KAN-7 Payments cut-over runbook",
            "p1:github:CI failing on main",
            "p1:github:#612 Rig settles animations",
        ]
        assert [row["rankClass"] for row in agg["items"]] == [
            "overdue", "no_due_date", "waiting",
        ]
        first = agg["items"][0]
        assert first["dueAt"] == "2026-09-05"
        assert first["since"] == "2026-09-05"
        assert first["rank"] == 1
        assert first["dedupCount"] == 1 and first["sources"][0]["source"] == "jira"

    def test_two_projections_of_one_obligation_collapse_on_the_wire(self) -> None:
        def list_projects(principal, filters):
            return [{"id": "p1", "name": "Q4 Platform"}]

        def room(principal, project_id):
            return _room_with([
                {"source": "jira", "title": "KAN-7 Payments cut-over runbook",
                 "why": "OVERDUE · 2 DAYS", "since": "2026-09-05",
                 "due_at": "2026-09-05", "severity": "danger"},
                {"source": "proposal", "kind": "proposal",
                 "title": "Payments cut-over runbook", "why": "PROPOSED · Standup",
                 "since": "2026-09-06T11:31:00", "severity": "info",
                 "proposal_id": "prop-1", "proposal_kind": "action"},
            ])

        agg = build_aggregate(list_projects=list_projects, room=room,
                              principal=OWNER, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 1
        [row] = agg["items"]
        assert row["dedupCount"] == 2
        assert {s["id"] for s in row["sources"]} == {
            "p1:jira:KAN-7 Payments cut-over runbook", "proposal:prop-1",
        }

    def test_a_carried_row_from_a_failed_source_keeps_its_place_in_the_ranking(self) -> None:
        store = LastKnownStore()
        healthy = _room_with([
            {"source": "jira", "title": "KAN-7 Runbook", "why": "OVERDUE · 2 DAYS",
             "since": "2026-09-05", "due_at": "2026-09-05", "severity": "danger"},
        ])

        def list_projects(principal, filters):
            return [{"id": "p1", "name": "A"}, {"id": "p2", "name": "B"}]

        def room_ok(principal, project_id):
            if project_id == "p1":
                return healthy
            return _room_with([{"source": "github", "title": "CI failing on main",
                                "why": "CI RED", "since": "2026-09-07T08:32:00",
                                "severity": "danger"}])

        build_aggregate(list_projects=list_projects, room=room_ok,
                        principal=OWNER, now=NOW, last_known=store)

        def room_p1_down(principal, project_id):
            if project_id == "p1":
                raise RuntimeError("jira rejected the query")
            return room_ok(principal, project_id)

        agg = build_aggregate(list_projects=list_projects, room=room_p1_down,
                              principal=OWNER, now=NOW, last_known=store)
        assert agg["complete"] is False
        assert [r["id"] for r in agg["items"]][0] == "p1:jira:KAN-7 Runbook"
        assert agg["items"][0]["fromLastObservation"] is True
        assert agg["items"][0]["rankClass"] == "overdue"


# ── AC4: the five notification transitions ─────────────────────────


def _agg(items: list[dict[str, Any]], *, complete: bool = True,
         coverage: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    unmuted = [it for it in items if not it.get("muted")]
    projects = sorted({str(it["projectId"]) for it in unmuted})
    return {
        "count": len(unmuted),
        "mutedCount": len(items) - len(unmuted),
        "projects": projects,
        "items": items,
        "next": None,
        "computedAt": NOW.isoformat(),
        "stale": False,
        "sweepId": None,
        "coverage": coverage if coverage is not None else [
            {"source_id": f"project:{p}", "kind": "project", "state": "available",
             "observed_at": NOW.isoformat(), "label": p, "project_id": p,
             "reason": None, "repair": None}
            for p in sorted({str(it["projectId"]) for it in items})
        ],
        "complete": complete,
    }


def _row(ident: str, project: str = "p1", *, muted: bool = False) -> dict[str, Any]:
    return {"id": ident, "projectId": project, "projectName": project.upper(),
            "ref": ident, "title": ident, "why": "CI RED", "since": "",
            "source": "github", "severity": "danger", "muted": muted}


def _failed_project_coverage(project: str) -> dict[str, Any]:
    return {"source_id": f"project:{project}", "kind": "project", "state": "failed",
            "observed_at": "2026-09-07T08:41:00", "label": project,
            "project_id": project, "reason": "jira rejected the query",
            "repair": {"token": "READ FAILED", "verb": "Retry",
                       "href": f"/projects/{project}"}}


class _Clock:
    """An injectable instant: quiet hours are decided from THIS, not the wall."""

    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "attention.db")


def _service(db: Database, calls: list[tuple[str, str]], *, clock: _Clock | None = None,
             quiet: tuple[int, int] = (2, 3)):
    from holdspeak.services.heartbeat_service import HeartbeatService

    # Keep implicit sweeps outside the test's quiet window. Tests that prove
    # quiet-hours behavior inject their own clock below.
    if clock is None:
        clock = _Clock(datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc))

    def notifier(title: str, body: str, *, click_url=None) -> bool:
        calls.append((title, body))
        return True

    ws = MagicMock()
    ws.evaluate_due.return_value = []
    svc = HeartbeatService(db, watch_service=ws, notifier=notifier,
                           clock=clock, local_zone=timezone.utc)
    svc.update_settings({"notify": "edge",
                         "quiet_hours": {"start": quiet[0], "end": quiet[1]}})
    return svc


def _sweep(svc, agg: dict[str, Any]) -> dict[str, Any]:
    with patch.object(svc, "_build_aggregate_via_canonical", return_value=agg):
        return svc.run_sweep(OWNER)["notify"]


class TestNotificationTransitions:
    def test_a_changed_item_with_the_same_count_notifies(self, db: Database) -> None:
        """The audit's defect: 3 -> 3 with one item swapped was silent."""
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        first = _sweep(svc, _agg([_row("a"), _row("b"), _row("c")]))
        assert first["outcome"] == "sent"
        calls.clear()

        second = _sweep(svc, _agg([_row("a"), _row("b"), _row("d")]))
        assert second["outcome"] == "sent", second
        assert second["count"] == 3 and len(calls) == 1
        assert second.get("newItems") == 1 and first.get("newItems") == 3
        assert calls[0][1] == "3 need you · 1 new", calls[0]

        # And the SAME set again is silent.
        calls.clear()
        third = _sweep(svc, _agg([_row("a"), _row("b"), _row("d")]))
        assert third["outcome"] == "held_no_edge" and not calls

    def test_quiet_hours_hold_then_deliver_once(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        clock = _Clock(datetime(2026, 9, 7, 23, 0, tzinfo=timezone.utc))
        svc = _service(db, calls, clock=clock, quiet=(22, 8))
        items = _agg([_row("a"), _row("b")])

        held = _sweep(svc, items)
        assert held["outcome"] == "held_quiet_hours" and not calls
        held_again = _sweep(svc, items)
        assert held_again["outcome"] == "held_quiet_hours" and not calls

        clock.at = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
        delivered = _sweep(svc, items)
        assert delivered["outcome"] == "sent" and len(calls) == 1
        once = _sweep(svc, items)
        assert once["outcome"] == "held_no_edge" and len(calls) == 1

    def test_quiet_hours_hold_even_a_same_count_change_and_deliver_it_once(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        clock = _Clock(datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc))
        svc = _service(db, calls, clock=clock, quiet=(22, 8))
        assert _sweep(svc, _agg([_row("a"), _row("b")]))["outcome"] == "sent"
        calls.clear()

        clock.at = datetime(2026, 9, 7, 23, 30, tzinfo=timezone.utc)
        assert _sweep(svc, _agg([_row("a"), _row("z")]))["outcome"] == "held_quiet_hours"
        assert not calls
        clock.at = datetime(2026, 9, 8, 8, 15, tzinfo=timezone.utc)
        assert _sweep(svc, _agg([_row("a"), _row("z")]))["outcome"] == "sent"
        assert calls == [("HoldSpeak", "2 need you · 1 new")]

    def test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        assert _sweep(svc, _agg([_row("a", "p1"), _row("x", "p2")]))["outcome"] == "sent"
        calls.clear()

        # p1 muted: a new p1 item arrives, nothing fires.
        muted = _agg([_row("a", "p1", muted=True), _row("b", "p1", muted=True), _row("x", "p2")])
        assert _sweep(svc, muted)["outcome"] == "held_no_edge" and not calls

        # p1 unmuted: `a` was notified before the mute and stays quiet;
        # `b` arrived while muted and is new.
        unmuted = _agg([_row("a", "p1"), _row("b", "p1"), _row("x", "p2")])
        receipt = _sweep(svc, unmuted)
        assert receipt["outcome"] == "sent", receipt
        assert calls == [("HoldSpeak", "3 need you across 2 projects · 1 new")]
        assert receipt.get("newItems") == 1

    def test_restart_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc1 = _service(db, calls)
        items = _agg([_row("a"), _row("b"), _row("c")])
        assert _sweep(svc1, items)["outcome"] == "sent"
        calls.clear()

        svc2 = _service(db, calls)  # a new instance over the same database
        assert _sweep(svc2, items)["outcome"] == "held_no_edge"
        assert not calls
        # ... a genuinely new item after the restart still fires ...
        assert _sweep(svc2, _agg([_row("a"), _row("b"), _row("c"), _row("d")]))["outcome"] == "sent"
        assert calls == [("HoldSpeak", "4 need you · 1 new")]
        # ... and it is the SET that survived the restart, not just a count.
        assert set(svc2.get_settings().get("last_notified_items", {})) == {"a", "b", "c", "d"}

    def test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        assert _sweep(svc, _agg([_row("a", "p1"), _row("b", "p1")]))["outcome"] == "sent"
        calls.clear()

        # p1's source fails on a fresh process: nothing carried, count 0.
        failed = _agg([], complete=False, coverage=[_failed_project_coverage("p1")])
        during = _sweep(svc, failed)
        assert during["outcome"] == "held_coverage_incomplete", during
        assert during["complete"] is False and not calls
        # The notified set is NOT pruned for an unobserved Project.
        assert set(svc.get_settings()["last_notified_items"]) == {"a", "b"}

        # A new item elsewhere DURING the failure still notifies, even
        # though the count (1) is below the last notified count (2).
        elsewhere = _agg([_row("z", "p2")], complete=False,
                         coverage=[_failed_project_coverage("p1"),
                                   {"source_id": "project:p2", "kind": "project",
                                    "state": "available", "observed_at": NOW.isoformat(),
                                    "label": "p2", "project_id": "p2",
                                    "reason": None, "repair": None}])
        receipt = _sweep(svc, elsewhere)
        assert receipt["outcome"] == "sent" and receipt["count"] == 1, receipt
        calls.clear()

        # p1 recovers with the same items: nothing new, nothing re-notified.
        recovered = _sweep(svc, _agg([_row("a", "p1"), _row("b", "p1"), _row("z", "p2")]))
        assert recovered["outcome"] == "held_no_edge" and not calls

    def test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        assert _sweep(svc, _agg([_row("a"), _row("b")]))["outcome"] == "sent"
        assert _sweep(svc, _agg([_row("a")]))["outcome"] == "held_no_edge"
        assert set(svc.get_settings()["last_notified_items"]) == {"a"}
        calls.clear()
        assert _sweep(svc, _agg([_row("a"), _row("b")]))["outcome"] == "sent"
        assert calls == [("HoldSpeak", "2 need you · 1 new")]

    def test_the_set_edge_is_a_pure_object(self) -> None:
        from holdspeak.desktop_notify import ItemSetEdge

        edge = ItemSetEdge(notified={"a": "p1"})
        assert edge.new_ids({"a": "p1", "b": "p1"}) == ["b"]
        assert edge.should_fire({"a": "p1"}) is False
        edge.mark_fired({"a": "p1", "b": "p1"})
        # p1 is KNOWN but not observed: its ids are kept.
        edge.prune(present={"b"}, observed_projects={"p2"}, known_projects={"p1", "p2"})
        assert set(edge.notified) == {"a", "b"}, "an unobserved Project keeps its ids"
        edge.prune(present={"b"}, observed_projects={"p1"}, known_projects={"p1"})
        assert set(edge.notified) == {"b"}
        edge.prune(present=set(), observed_projects=None)
        assert edge.notified == {}

    def test_counsel_probe_2_pruning_drops_archived_projects_and_resolved_door_cards(self) -> None:
        """Counsel P1-3: an id whose Project no longer exists, and a projectless
        id that left the aggregate, are pruned; a Project whose source is
        cant_check / stale keeps its set."""
        from holdspeak.desktop_notify import ItemSetEdge

        edge = ItemSetEdge()
        edge.mark_fired({"p1:jira:a": "p1", "p9:jira:z": "p9", "door:card1": "",
                         "p3:jira:k": "p3"})
        # p9 archived (not in coverage at all); door card resolved; p3's
        # watch is cant_check (known, not observed).
        edge.prune(present={"p1:jira:a"}, observed_projects={"p1"},
                   known_projects={"p1", "p3"})
        assert sorted(edge.notified) == ["p1:jira:a", "p3:jira:k"]

    def test_counsel_probe_3_escalation_of_a_known_id_notifies(self) -> None:
        """Counsel P1-4: DUE TODAY -> OVERDUE on the same id is news."""
        from holdspeak.desktop_notify import ItemSetEdge

        edge = ItemSetEdge(notified={"p1:jira:KAN-7": {"project": "p1", "class": "due_today"}})
        assert edge.new_ids({"p1:jira:KAN-7": {"project": "p1", "class": "overdue"}}) == []
        assert edge.escalated_ids({"p1:jira:KAN-7": {"project": "p1", "class": "overdue"}}) == ["p1:jira:KAN-7"]
        assert edge.should_fire({"p1:jira:KAN-7": {"project": "p1", "class": "overdue"}}) is True
        # waiting -> due_today escalates; overdue -> due_today does not; the
        # same class again does not.
        waiting = ItemSetEdge(notified={"x": {"project": "p1", "class": "waiting"}})
        assert waiting.escalated_ids({"x": {"project": "p1", "class": "due_today"}}) == ["x"]
        assert waiting.escalated_ids({"x": {"project": "p1", "class": "no_due_date"}}) == []
        down = ItemSetEdge(notified={"x": {"project": "p1", "class": "overdue"}})
        assert down.escalated_ids({"x": {"project": "p1", "class": "due_today"}}) == []

    def test_escalation_fires_through_the_sweep_and_says_so(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        today = {**_row("k"), "why": "DUE TODAY", "rankClass": "due_today"}
        assert _sweep(svc, _agg([today, _row("b")]))["outcome"] == "sent"
        calls.clear()
        overdue = {**_row("k"), "why": "OVERDUE · 1 DAY", "rankClass": "overdue"}
        receipt = _sweep(svc, _agg([overdue, _row("b")]))
        assert receipt["outcome"] == "sent" and receipt["escalatedItems"] == 1, receipt
        assert calls == [("HoldSpeak", "2 need you · 1 escalated")]
        calls.clear()
        # Said once: the same overdue row again is silent.
        assert _sweep(svc, _agg([overdue, _row("b")]))["outcome"] == "held_no_edge"
        # New AND escalated in one sweep says both.
        later = {**_row("b"), "why": "DUE TODAY", "rankClass": "due_today"}
        receipt = _sweep(svc, _agg([overdue, later, _row("c")]))
        assert calls == [("HoldSpeak", "3 need you · 1 new · 1 escalated")], calls

    def test_counsel_probe_2b_archived_project_ids_leave_the_settings(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        assert _sweep(svc, _agg([_row("a", "p1"), _row("z", "p9")]))["outcome"] == "sent"
        for _ in range(3):
            _sweep(svc, _agg([_row("a", "p1")]))
        assert set(svc.get_settings()["last_notified_items"]) == {"a"}
        # ... but a Project whose source is cant_check keeps its set.
        assert _sweep(svc, _agg([_row("a", "p1"), _row("k", "p3")]))["outcome"] == "sent"
        gone = _agg([_row("a", "p1")], complete=False,
                    coverage=[{"source_id": "project:p1", "kind": "project", "state": "available",
                               "observed_at": NOW.isoformat(), "label": "p1", "project_id": "p1",
                               "reason": None, "repair": None},
                              {"source_id": "project:p3", "kind": "project", "state": "available",
                               "observed_at": NOW.isoformat(), "label": "p3", "project_id": "p3",
                               "reason": None, "repair": None},
                              {"source_id": "watch:w3", "kind": "watch", "state": "failed",
                               "observed_at": None, "label": "jira", "project_id": "p3",
                               "reason": "jira rejected", "repair": {"token": "CANT CHECK",
                                                                      "verb": "Reconnect",
                                                                      "href": "/settings"}}])
        _sweep(svc, gone)
        assert set(svc.get_settings()["last_notified_items"]) == {"a", "k"}

    def test_the_policy_row_is_written_only_when_the_set_or_outcome_changed(self, db: Database) -> None:
        """Counsel P1-5."""
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        items = _agg([_row("a"), _row("b")])
        writes: list[int] = []
        original = svc._persist_edge

        def counting(*args, **kwargs):
            writes.append(1)
            return original(*args, **kwargs)

        with patch.object(svc, "_persist_edge", side_effect=counting):
            assert _sweep(svc, items)["outcome"] == "sent"
            assert len(writes) == 1
            for _ in range(3):
                assert _sweep(svc, items)["outcome"] == "held_no_edge"
            assert len(writes) == 2, "one write for the outcome change, none for the same state"
            assert _sweep(svc, _agg([_row("a"), _row("b"), _row("c")]))["outcome"] == "sent"
            assert len(writes) == 3


# ── AC5: no false all-clear ─────────────────────────────────────────


class TestNoFalseAllClear:
    def test_a_failed_source_keeps_its_last_known_items_stamped_with_their_observation(self) -> None:
        store = LastKnownStore()

        def list_projects(principal, filters):
            return [{"id": "p1", "name": "Q4 Platform"}]

        healthy = _room_with([{"source": "jira", "title": "KAN-7 Runbook",
                               "why": "OVERDUE · 2 DAYS", "since": "2026-09-05",
                               "due_at": "2026-09-05", "severity": "danger"}])
        healthy["observed_at"] = "2026-09-07T08:41:00"
        build_aggregate(list_projects=list_projects, room=lambda p, pid: healthy,
                        principal=OWNER, now=NOW, last_known=store)

        def down(principal, project_id):
            raise RuntimeError("jira rejected the query")

        agg = build_aggregate(list_projects=list_projects, room=down,
                              principal=OWNER, now=NOW, last_known=store)
        assert agg["complete"] is False
        assert agg["count"] == 1
        [row] = agg["items"]
        assert row["fromLastObservation"] is True
        assert row["observedAt"] == "2026-09-07T08:41:00"
        assert row["severity"] == "danger", "a missing source cannot lower a known item"

    def test_an_empty_partial_result_is_not_complete(self) -> None:
        def list_projects(principal, filters):
            return [{"id": "p1", "name": "Q4 Platform"}]

        def down(principal, project_id):
            raise RuntimeError("jira rejected the query")

        agg = build_aggregate(list_projects=list_projects, room=down,
                              principal=OWNER, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 0 and agg["complete"] is False
        assert agg["coverage"][0]["state"] == "failed"
