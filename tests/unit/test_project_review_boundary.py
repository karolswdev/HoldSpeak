"""S52: one open-review query boundary (D06/G52 = B, Muad'Dib 2026-11-07).

The Room's review section reads the open review through the repository
(``DeltaRepository.get_open_review``); ``ProjectService`` never holds or
calls ``ProjectDeltaService``.  Delta keeps the one remaining edge (it
needs the Project service for ``create_item`` inside ``decide_proposal``)
and its ``_find_open_review`` wrapper delegates to the same selector.

Cases map to the story's acceptance matrix (C52-01..C52-11) where the
proof is a unit test; the atomic-command and MCP-resource proofs stay in
their existing files, unchanged.
"""

from __future__ import annotations

from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime.room_composition import compose_room_services
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "review-boundary-test")
ABSENT = {"state": "absent", "reason": "not_yet_built"}


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = Database(tmp_path / "review-boundary.db")
    yield database
    reset_database()


def _project(svc: ProjectService, name: str = "Boundary") -> str:
    return svc.create_project(OWNER, {"name": name})["id"]


def _delta_rows(db: Database, project_id: str, review_id: str, *, proposals: int,
                status: str = "open", opened_at: str = "2026-01-10T10:00:00+00:00") -> None:
    db.project_observations.insert_review(
        review_id=review_id, project_id=project_id, status=status, opened_at=opened_at,
    )
    for i in range(proposals):
        db.project_observations.insert_proposal(
            proposal_id=f"pprop_{review_id}_{i}", project_id=project_id,
            review_window_key=review_id, proposal_kind="add_item",
            target_ref=f"ref-{i}", title=f"proposal {i}",
        )


def _delta_needs(room: dict[str, Any]) -> list[dict[str, Any]]:
    return [n for n in room["needsYou"].get("items", []) if n.get("source") == "delta"]


# ── C52-01: the repository owns the selector ─────────────────────────────

class TestRepositorySelector:
    def test_none_without_reviews(self, db) -> None:
        pid = _project(ProjectService(db))
        assert db.project_observations.get_open_review(pid) is None

    def test_newest_open_first_and_accepted_excluded(self, db) -> None:
        pid = _project(ProjectService(db))
        _delta_rows(db, pid, "prev_old", proposals=0, opened_at="2026-01-01T00:00:00+00:00")
        _delta_rows(db, pid, "prev_acc", proposals=0, status="accepted",
                    opened_at="2026-02-01T00:00:00+00:00")
        _delta_rows(db, pid, "prev_new", proposals=0, opened_at="2026-01-20T00:00:00+00:00")
        row = db.project_observations.get_open_review(pid)
        assert row is not None and row["id"] == "prev_new"
        # Same row as the list query it delegates to.
        assert row == db.project_observations.list_reviews(pid, status="open", limit=1)[0]

    def test_scoped_to_the_project(self, db) -> None:
        svc = ProjectService(db)
        a, b = _project(svc, "A"), _project(svc, "B")
        _delta_rows(db, a, "prev_a", proposals=0)
        assert db.project_observations.get_open_review(b) is None
        assert db.project_observations.get_open_review(f"  {a}  ")["id"] == "prev_a"

    def test_errors_propagate(self, db, monkeypatch) -> None:
        def boom(*a: Any, **k: Any) -> Any:
            raise RuntimeError("db gone")
        monkeypatch.setattr(db.project_observations, "list_reviews", boom)
        with pytest.raises(RuntimeError):
            db.project_observations.get_open_review("p")


# ── C52-02 / C52-03: availability is a flag, not a held service ─────────

class TestAvailabilityGates:
    def test_bare_service_is_absent_and_adds_no_delta_row(self, db) -> None:
        svc = ProjectService(db)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_x", proposals=2)
        room = svc.room(OWNER, pid)
        assert room["review"] == ABSENT
        assert _delta_needs(room) == []

    def test_explicit_true_with_no_review_is_a_real_zero(self, db) -> None:
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        review = svc.room(OWNER, pid)["review"]
        assert review == {"state": "ok", "last_accepted_at": None,
                          "pending_count": 0, "open_review_id": None}

    def test_legacy_keyword_infers_availability_without_retaining_it(self, db) -> None:
        class Falsey:
            def __bool__(self) -> bool:
                return False

            def _find_open_review(self, project_id: str) -> Any:
                raise AssertionError("the Room must not call the Delta service")

        stand_in = Falsey()
        svc = ProjectService(db, delta_service=stand_in)
        assert svc._review_available is True
        assert not hasattr(svc, "_delta_service")
        pid = _project(svc)
        _delta_rows(db, pid, "prev_y", proposals=1)
        assert svc.room(OWNER, pid)["review"]["open_review_id"] == "prev_y"

    def test_explicit_boolean_wins_over_legacy_keyword(self, db) -> None:
        assert ProjectService(db, review_available=False,
                              delta_service=object())._review_available is False
        assert ProjectService(db, review_available=True,
                              delta_service=None)._review_available is True
        assert ProjectService(db, delta_service=None)._review_available is False


# ── C52-04 / C52-11: the Room reads through the repository only ─────────

class TestRoomReadsThroughRepository:
    def test_open_review_counts_pending_and_names_the_window(self, db, monkeypatch) -> None:
        def never(*a: Any, **k: Any) -> Any:
            raise AssertionError("ProjectDeltaService._find_open_review called on a Room read")
        monkeypatch.setattr(ProjectDeltaService, "_find_open_review", never)
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_open", proposals=3)
        room = svc.room(OWNER, pid)
        assert room["review"]["open_review_id"] == "prev_open"
        assert room["review"]["pending_count"] == 3
        rows = _delta_needs(room)
        assert len(rows) == 1 and rows[0]["title"] == "3 proposals waiting"

    def test_one_proposal_is_singular(self, db) -> None:
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_one", proposals=1)
        assert _delta_needs(svc.room(OWNER, pid))[0]["title"] == "1 proposal waiting"

    def test_pending_count_is_the_open_lifecycle_only(self, db) -> None:
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_mix", proposals=2)
        db.project_observations.insert_proposal(
            proposal_id="pprop_done", project_id=pid, review_window_key="prev_mix",
            proposal_kind="add_item", target_ref="r", title="t", lifecycle="accepted",
        )
        assert svc.room(OWNER, pid)["review"]["pending_count"] == 2


    def test_pending_count_is_the_returned_rows_capped_at_200(self, db) -> None:
        # The count is the length of the existing proposal query (default
        # limit 200), not a database total; S52 moves the read, not the policy.
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_cap", proposals=201)
        room = svc.room(OWNER, pid)
        assert room["review"]["pending_count"] == 200
        assert _delta_needs(room)[0]["title"] == "200 proposals waiting"

# ── C52-05: fault shapes stay exactly as they were ───────────────────────

class TestFaultShapes:
    def test_selector_fault_leaves_zero_and_no_id(self, db, monkeypatch) -> None:
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_f", proposals=2)

        def boom(*a: Any, **k: Any) -> Any:
            raise RuntimeError("selector down")
        monkeypatch.setattr(db.project_observations, "get_open_review", boom)
        review = svc.room(OWNER, pid)["review"]
        assert review["state"] == "ok"
        assert (review["open_review_id"], review["pending_count"]) == (None, 0)

    def test_proposal_fault_keeps_the_id_with_zero(self, db, monkeypatch) -> None:
        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_g", proposals=2)

        def boom(*a: Any, **k: Any) -> Any:
            raise RuntimeError("proposals down")
        monkeypatch.setattr(db.project_observations, "list_proposals", boom)
        review = svc.room(OWNER, pid)["review"]
        assert (review["open_review_id"], review["pending_count"]) == ("prev_g", 0)
        assert _delta_needs(svc.room(OWNER, pid)) == []


    def test_later_room_fields_fault_degrades_only_the_review_section(
            self, db, monkeypatch) -> None:
        # The review helper's own room-fields read sits outside its inner
        # catch: it reaches the outer section wrapper.  The Room's earlier
        # orientation read of the same fields is left to succeed.
        import sys

        svc = ProjectService(db, review_available=True)
        pid = _project(svc)
        _delta_rows(db, pid, "prev_h", proposals=1)
        real = db.projects.get_project_room_fields
        hits: list[str] = []

        def targeted(project_id: str) -> Any:
            if sys._getframe(1).f_code.co_name == "_read_room_review":
                hits.append(project_id)
                raise RuntimeError("room fields down")
            return real(project_id)
        monkeypatch.setattr(db.projects, "get_project_room_fields", targeted)
        room = svc.room(OWNER, pid)
        assert hits, "the fault must hit the review helper's read"
        assert room["review"] == {"state": "degraded", "error_code": "review_read_failed"}
        assert room["project"]["id"] == pid

# ── C52-07 (wrapper) / C52-08 (composition identity) ────────────────────

class TestDeltaWrapperAndComposition:
    def test_find_open_review_delegates_to_the_repository(self, db, monkeypatch) -> None:
        seen: list[str] = []
        monkeypatch.setattr(
            db.project_observations, "get_open_review",
            lambda project_id: seen.append(project_id) or {"id": "prev_w"},
        )
        delta = ProjectDeltaService(db, collector=None)
        assert delta._find_open_review("p1") == {"id": "prev_w"}
        assert seen == ["p1"]

    def test_missing_project_is_built_with_review_available(self, db) -> None:
        class Root:
            project_service = None
            project_delta_service = None
            project_update_service = None
            project_door_service = None
            watch_service = None
            project_steward_service = None
            connections_service = None
            suggested_source_service = None
            channel_service = None

            def emit_desk_changed(self, *a: Any) -> None:
                pass

        root, ctx = Root(), Root()
        compose_room_services(root, ctx, db, None)
        assert root.project_service is ctx.project_service
        assert root.project_service._review_available is True
        assert not hasattr(root.project_service, "_delta_service")
        # The one remaining edge: Delta → Project, for create_item.
        assert root.project_delta_service._project_service is root.project_service

    def test_held_instances_are_kept_and_attachment_is_not_forced(self, db) -> None:
        project = ProjectService(db, review_available=True)
        delta = ProjectDeltaService(db, collector=None)

        class Root:
            project_service = project
            project_delta_service = delta
            project_update_service = None
            project_door_service = None
            watch_service = None
            project_steward_service = None
            connections_service = None
            suggested_source_service = None
            channel_service = None

            def emit_desk_changed(self, *a: Any) -> None:
                pass

        root = Root()
        compose_room_services(root, Root(), db, None)
        assert root.project_service is project
        assert root.project_delta_service is delta
        assert delta._project_service is None

    def test_existing_bare_project_is_not_backfilled_when_delta_is_built(self, db) -> None:
        project = ProjectService(db)

        class Root:
            project_service = project
            project_delta_service = None
            project_update_service = None
            project_door_service = None
            watch_service = None
            project_steward_service = None
            connections_service = None
            suggested_source_service = None
            channel_service = None

            def emit_desk_changed(self, *a: Any) -> None:
                pass

        root = Root()
        compose_room_services(root, Root(), db, None)
        assert root.project_service is project
        assert project._review_available is False
        assert root.project_delta_service._project_service is project
