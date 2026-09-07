"""HS-200-07 (C4) — coverage and partial results.

The aggregate carries a coverage record for EVERY expected source, an
empty result is an all-clear only when coverage is complete, a failed
source keeps its last-known unresolved items, and concurrent refreshes
do one build.

Run:
    HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \\
        tests/unit/test_phase200_attention_coverage.py
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Any

import pytest

from holdspeak.services.needs_you_aggregate import (
    COVERAGE_KINDS,
    COVERAGE_STATES,
    LastKnownStore,
    NeedsYouCache,
    build_aggregate,
)

NOW = datetime(2026, 9, 6, 10, 0, 0)


# ── Fakes: the two callables build_aggregate depends on ──────────────


def _needs_item(title: str, severity: str = "danger", source: str = "github") -> dict:
    return {
        "source": source,
        "title": title,
        "why": f"WAITING ON YOU · {title}",
        "since": "2026-09-04T10:00:00",
        "url": f"https://example.invalid/{title}",
        "severity": severity,
    }


def _room(
    project_id: str,
    *,
    items: list[dict] | None = None,
    needs_state: str = "ok",
    observed_at: str = "2026-09-06T09:00:00",
    sources: list[dict] | None = None,
    meetings_state: str = "ok",
    commitments_state: str = "ok",
) -> dict:
    needs: dict[str, Any]
    if needs_state == "ok":
        needs = {"state": "ok", "items": items or [], "count": len(items or [])}
    else:
        needs = {"state": needs_state, "error_code": "needsYou_read_failed"}
    return {
        "project_id": project_id,
        "observed_at": observed_at,
        "needsYou": needs,
        "sources": {"state": "ok", "items": sources or [], "count": len(sources or [])},
        "meetings": ({"state": "ok", "items": []} if meetings_state == "ok"
                     else {"state": meetings_state, "error_code": "meetings_read_failed"}),
        "commitments": ({"state": "ok", "items": []} if commitments_state == "ok"
                        else {"state": commitments_state,
                              "error_code": "commitments_read_failed"}),
    }


def _watch(
    watch_id: str,
    *,
    state: str = "live",
    checked_at: str | None = "2026-09-06T09:30:00",
    provider: str = "github",
    scope: str = "karolswdev/HoldSpeak",
    plain_reason: str | None = None,
) -> dict:
    return {
        "watchId": watch_id,
        "provider": provider,
        "scope": scope,
        "state": state,
        "checkedAt": checked_at,
        "plainReason": plain_reason,
        "tokens": [],
    }


class Desk:
    """A fake ProjectService pair: list_projects + room, with failures."""

    def __init__(self, rooms: dict[str, dict], *, names: dict[str, str] | None = None) -> None:
        self._rooms = rooms
        self._names = names or {pid: pid.upper() for pid in rooms}
        self.raises: dict[str, BaseException] = {}
        self.list_raises: BaseException | None = None
        self.room_calls = 0

    def list_projects(self, principal: Any, filters: dict[str, Any] | None = None) -> list[dict]:
        if self.list_raises is not None:
            raise self.list_raises
        return [{"id": pid, "name": self._names[pid]} for pid in self._rooms]

    def room(self, principal: Any, project_id: str) -> dict:
        self.room_calls += 1
        if project_id in self.raises:
            raise self.raises[project_id]
        return self._rooms[project_id]


def _coverage_by_id(aggregate: dict) -> dict[str, dict]:
    return {row["source_id"]: row for row in aggregate["coverage"]}


# ── AC1: a failed / forbidden / stale / unavailable Project stays ────


class TestCoverageProjection:
    def test_one_failed_room_among_healthy_rooms_stays_in_coverage(self):
        desk = Desk({
            "alpha": _room("alpha", items=[_needs_item("PR 612")]),
            "beta": _room("beta", items=[]),
        }, names={"alpha": "Q4 Platform", "beta": "Governance"})
        desk.raises["beta"] = RuntimeError("watch table locked")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["project:alpha"]["state"] == "available"
        assert cov["project:beta"]["state"] == "failed", cov["project:beta"]
        assert cov["project:beta"]["label"] == "Governance"
        assert cov["project:beta"]["repair"] == {
            "token": "READ FAILED", "verb": "Retry", "href": "/projects/beta",
        }
        assert agg["complete"] is False

    def test_forbidden_room_is_forbidden_not_failed(self):
        desk = Desk({"alpha": _room("alpha", items=[])})
        desk.raises["alpha"] = PermissionError("principal may not read this Room")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["state"] == "forbidden"
        assert row["repair"]["token"] == "FORBIDDEN"
        assert row["repair"]["verb"] == "Open source"
        assert agg["complete"] is False

    def test_degraded_needs_you_section_is_a_failed_source(self):
        desk = Desk({"alpha": _room("alpha", needs_state="degraded")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["state"] == "failed"
        assert row["reason"] == "needsYou_read_failed"

    def test_every_failure_is_named_when_all_rooms_fail(self):
        desk = Desk({
            "alpha": _room("alpha"), "beta": _room("beta"), "gamma": _room("gamma"),
        })
        for pid in ("alpha", "beta", "gamma"):
            desk.raises[pid] = RuntimeError("connector down")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        assert agg["count"] == 0
        assert agg["complete"] is False
        assert len(agg["coverage"]) == 3
        assert {row["state"] for row in agg["coverage"]} == {"failed"}

    def test_project_list_unavailable_replays_every_remembered_source(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")])},
                    names={"alpha": "Q4 Platform"})
        first = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                principal=None, now=NOW, last_known=memory)
        assert first["complete"] is True

        desk.list_raises = RuntimeError("database is locked")
        second = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                 principal=None, now=NOW, last_known=memory)

        assert second["complete"] is False
        states = {row["source_id"]: row["state"] for row in second["coverage"]}
        assert states["projects"] == "failed"
        assert states["project:alpha"] == "failed"
        assert [row["title"] for row in second["items"]] == ["PR 612"]
        assert second["items"][0]["fromLastObservation"] is True

    def test_meeting_and_commitment_sections_are_expected_sources(self):
        desk = Desk({"alpha": _room("alpha", items=[], commitments_state="degraded")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["meeting:alpha"]["state"] == "available"
        assert cov["commitment:alpha"]["state"] == "failed"
        assert cov["commitment:alpha"]["kind"] == "commitment"
        assert agg["complete"] is False

    def test_watch_states_map_to_coverage_states(self):
        old = (NOW - timedelta(hours=30)).isoformat()
        desk = Desk({"alpha": _room("alpha", items=[], sources=[
            _watch("w-live"),
            _watch("w-stale", checked_at=old),
            _watch("w-paused", state="paused"),
            _watch("w-broken", state="cant_check",
                   plain_reason="The GitHub token expired"),
            _watch("w-never", checked_at=None),
        ])})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["watch:w-live"]["state"] == "available"
        assert cov["watch:w-stale"]["state"] == "stale"
        assert cov["watch:w-stale"]["observed_at"] == old
        assert cov["watch:w-paused"]["state"] == "unavailable"
        assert cov["watch:w-paused"]["repair"]["token"] == "PAUSED"
        assert cov["watch:w-broken"]["state"] == "failed"
        assert cov["watch:w-broken"]["reason"] == "The GitHub token expired"
        assert cov["watch:w-broken"]["repair"]["verb"] == "Reconnect"
        assert cov["watch:w-never"]["state"] == "unavailable"
        assert cov["watch:w-never"]["observed_at"] is None
        assert agg["complete"] is False

    def test_every_record_uses_the_contract_vocabulary(self):
        desk = Desk({"alpha": _room("alpha", items=[], sources=[_watch("w1")])})
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        for row in agg["coverage"]:
            assert row["state"] in COVERAGE_STATES, row
            assert row["kind"] in COVERAGE_KINDS, row
            assert "observed_at" in row and "repair" in row and "reason" in row


# ── AC2: aggregate computation time is not source freshness ──────────


class TestFreshnessIsNotComputationTime:
    def test_computed_at_is_the_aggregate_clock_not_the_source_clock(self):
        desk = Desk({"alpha": _room("alpha", items=[],
                                    observed_at="2026-09-05T07:00:00")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        assert agg["computedAt"] == NOW.isoformat()
        assert _coverage_by_id(agg)["project:alpha"]["observed_at"] == "2026-09-05T07:00:00"
        assert agg["computedAt"] != agg["coverage"][0]["observed_at"]

    def test_a_failed_source_keeps_the_time_of_its_last_success(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")],
                                    observed_at="2026-09-06T09:00:00")})
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        desk.raises["alpha"] = RuntimeError("connector down")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=datetime(2026, 9, 6, 11, 0),
                              last_known=memory)

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["observed_at"] == "2026-09-06T09:00:00"
        assert agg["computedAt"] == "2026-09-06T11:00:00"


# ── AC3: an empty partial result is not an all-clear ─────────────────


class TestEmptyResults:
    def test_empty_and_complete_is_an_all_clear(self):
        desk = Desk({"alpha": _room("alpha", items=[])})
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 0
        assert agg["complete"] is True

    def test_empty_and_partial_is_incomplete_coverage(self):
        desk = Desk({"alpha": _room("alpha", items=[]), "beta": _room("beta")})
        desk.raises["beta"] = RuntimeError("connector down")
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 0
        assert agg["complete"] is False
        assert any(row["state"] != "available" for row in agg["coverage"])


# ── AC4: known items stay traceable across failure and recovery ──────


class TestSeverityCannotDropByDisappearance:
    def test_a_failed_source_keeps_its_last_known_unresolved_items(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("CI red", "danger")])})
        first = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                principal=None, now=NOW, last_known=memory)
        assert first["count"] == 1

        desk.raises["alpha"] = RuntimeError("connector down")
        second = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                 principal=None, now=NOW, last_known=memory)

        assert second["count"] == 1, "a vanished source cannot drop a known item"
        item = second["items"][0]
        assert item["severity"] == "danger", "severity cannot fall by disappearance"
        assert item["fromLastObservation"] is True
        assert item["observedAt"] == "2026-09-06T09:00:00"

    def test_recovery_reconciles_by_stable_id_without_duplicates(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("CI red", "danger")])})
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        desk.raises["alpha"] = RuntimeError("connector down")
        carried = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                  principal=None, now=NOW, last_known=memory)
        carried_id = carried["items"][0]["id"]

        # The source recovers, still holding the same item.
        del desk.raises["alpha"]
        recovered = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                    principal=None, now=NOW, last_known=memory)

        assert recovered["count"] == 1, "the recovered item is not counted twice"
        assert recovered["items"][0]["id"] == carried_id
        assert "fromLastObservation" not in recovered["items"][0]
        assert recovered["complete"] is True

    def test_a_resolved_item_leaves_on_recovery(self):
        memory = LastKnownStore()
        rooms = {"alpha": _room("alpha", items=[_needs_item("CI red")])}
        desk = Desk(rooms)
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        rooms["alpha"] = _room("alpha", items=[])

        recovered = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                    principal=None, now=NOW, last_known=memory)

        assert recovered["count"] == 0
        assert recovered["complete"] is True

    def test_item_ids_are_stable_across_builds(self):
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")])})
        one = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        two = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert one["items"][0]["id"] == two["items"][0]["id"]
        assert one["items"][0]["id"] == "alpha:github:PR 612"


# ── AC5: invalidation and concurrent refresh, bounded ────────────────


class TestCacheCoverage:
    def _builder(self, payload: dict, *, delay: float = 0.0):
        calls = {"n": 0}

        def build() -> dict:
            calls["n"] += 1
            if delay:
                time.sleep(delay)
            return dict(payload)

        return build, calls

    def test_concurrent_refresh_does_one_build_and_keeps_coverage(self):
        payload = {
            "count": 0, "projects": [], "items": [], "next": None,
            "computedAt": NOW.isoformat(), "stale": False, "sweepId": None,
            "coverage": [{"source_id": "project:alpha", "kind": "project",
                          "state": "failed", "observed_at": None,
                          "label": "Q4", "project_id": "alpha",
                          "reason": "down", "repair": {"token": "READ FAILED",
                                                       "verb": "Retry",
                                                       "href": "/projects/alpha"}}],
            "complete": False,
        }
        builder, calls = self._builder(payload, delay=0.05)
        cache = NeedsYouCache(builder, max_age_s=60.0)

        results: list[dict] = []
        errors: list[BaseException] = []

        def read() -> None:
            try:
                results.append(cache.get())
            except BaseException as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [threading.Thread(target=read) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, errors
        assert len(results) == 8
        assert calls["n"] == 1, f"single flight: expected 1 build, got {calls['n']}"
        assert cache.build_count == 1
        for result in results:
            assert result["complete"] is False
            assert len(result["coverage"]) == 1, "no source dropped by the race"

    def test_invalidate_then_a_failing_rebuild_serves_the_last_coverage_as_stale(self):
        payload = {
            "count": 1, "projects": ["alpha"],
            "items": [{"id": "alpha:github:CI red", "severity": "danger"}],
            "next": None, "computedAt": NOW.isoformat(), "stale": False,
            "sweepId": None,
            "coverage": [{"source_id": "project:alpha", "kind": "project",
                          "state": "available", "observed_at": "2026-09-06T09:00:00",
                          "label": "Q4", "project_id": "alpha", "reason": None,
                          "repair": None}],
            "complete": True,
        }
        state = {"fail": False}

        def builder() -> dict:
            if state["fail"]:
                raise RuntimeError("database is locked")
            return dict(payload)

        cache = NeedsYouCache(builder, max_age_s=60.0)
        assert cache.get()["complete"] is True

        state["fail"] = True
        cache.invalidate(sweep_id="sweep-2")
        served = cache.get()

        assert served["stale"] is True, "a stale read says so"
        assert served["count"] == 1, "invalidation did not drop the known item"
        assert served["coverage"][0]["observed_at"] == "2026-09-06T09:00:00"

    def test_a_failing_first_build_raises_rather_than_inventing_an_all_clear(self):
        def builder() -> dict:
            raise RuntimeError("database is locked")

        cache = NeedsYouCache(builder, max_age_s=60.0)
        with pytest.raises(RuntimeError):
            cache.get()

    def test_peek_reports_stale_after_invalidate(self):
        payload = {"count": 0, "projects": [], "items": [], "next": None,
                   "computedAt": NOW.isoformat(), "stale": False, "sweepId": None,
                   "coverage": [], "complete": True}
        builder, _ = self._builder(payload)
        cache = NeedsYouCache(builder, max_age_s=60.0)
        cache.get()
        cache.invalidate()
        peeked = cache.peek()
        assert peeked is not None and peeked["stale"] is True
