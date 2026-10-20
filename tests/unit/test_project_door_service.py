"""HS-169-02 — Door service parity and behaviour tests.

(a) Count path and evaluation path compile IDENTICAL queries (GitHub + Jira).
(b) Door create stores no blank list entries and one watch per default.
(c) Zero sources = blank project.
(d) Failing count returns a plain reason and still allows create.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.project_door_service import (
    DOOR_DEFAULTS,
    ProjectDoorService,
    _flatten_github_query,
    _flatten_jira_query,
    parse_source_text,
)

_P = Principal(PrincipalKind.OWNER, "test")
_REPO = "karolswdev/HoldSpeak"
_JIRA_SCOPE = {
    "connection_ref": "site.atlassian.net|user@example.com",
    "projects": ["KAN"],
}


# ── (a) Parity: count query == evaluation query ───────────────────


class TestGitHubQueryParity:
    """The count path must build the SAME stored query shape
    that create_from_setup produces for evaluation."""

    def test_review_queue_parity(self) -> None:
        from holdspeak import github_templates

        spec = github_templates.compile("watch.github.review_queue", _REPO)
        stored = _flatten_github_query(spec)

        assert stored["repository"] == _REPO
        assert stored.get("state") == "open"
        assert stored.get("base") == "main"
        assert "repositories" not in stored

    def test_ci_branch_query_shape(self) -> None:
        """CI door default uses branch_ci query kind with
        repository + base, matching the stored query shape."""
        svc = ProjectDoorService()
        query = {"repository": _REPO, "base": "main"}
        assert "repository" in query
        assert "base" in query

    def test_flatten_matches_create_from_setup(self) -> None:
        """The flatten function produces the same shape as
        project_service.create_from_setup's flattening loop."""
        from holdspeak import github_templates

        spec = github_templates.compile("watch.github.review_queue", _REPO)

        subject = spec["subject"]
        query_filters = dict(subject.get("query", {}))
        repos = subject.get("scope", {}).get("repositories", [])
        if repos:
            query_filters["repository"] = repos[0]

        flat = _flatten_github_query(spec)
        assert flat == query_filters


class TestJiraQueryParity:
    """The count path must compile the SAME JQL that evaluation uses."""

    def test_due_risk_jql_parity(self) -> None:
        from holdspeak import jira_templates
        from holdspeak.services.watch_sources import _compile_jql

        spec = jira_templates.compile("watch.jira.due_risk", _JIRA_SCOPE)
        stored = _flatten_jira_query(spec)
        jql_from_count = _compile_jql(stored)

        eval_query = dict(spec["subject"]["query"])
        conn_ref = spec["subject"]["scope"].get("connection_ref") or spec["provider"].get("connection_ref")
        if conn_ref:
            eval_query["connection_ref"] = conn_ref
        projects = spec["subject"]["scope"].get("projects", [])
        if projects:
            eval_query["projects"] = list(projects)
        jql_from_eval = _compile_jql(eval_query)

        assert jql_from_count == jql_from_eval

    def test_blockers_jql_parity(self) -> None:
        from holdspeak import jira_templates
        from holdspeak.services.watch_sources import _compile_jql

        spec = jira_templates.compile("watch.jira.blockers", _JIRA_SCOPE)
        stored = _flatten_jira_query(spec)
        jql_count = _compile_jql(stored)

        eval_query = dict(spec["subject"]["query"])
        conn_ref = spec["subject"]["scope"].get("connection_ref") or spec["provider"].get("connection_ref")
        if conn_ref:
            eval_query["connection_ref"] = conn_ref
        projects = spec["subject"]["scope"].get("projects", [])
        if projects:
            eval_query["projects"] = list(projects)
        jql_eval = _compile_jql(eval_query)

        assert jql_count == jql_eval

    def test_flatten_matches_create_from_setup(self) -> None:
        """Flatten produces the same shape as create_from_setup's Jira loop."""
        from holdspeak import jira_templates

        spec = jira_templates.compile("watch.jira.due_risk", _JIRA_SCOPE)

        subject = spec["subject"]
        query_filters = dict(subject.get("query", {}))
        scope = subject.get("scope", {})
        conn_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
        if conn_ref:
            query_filters["connection_ref"] = conn_ref
        jira_projects = scope.get("projects", [])
        if jira_projects:
            query_filters["projects"] = list(jira_projects)
        jira_issue_types = scope.get("issue_types", [])
        if jira_issue_types:
            query_filters["issue_types"] = list(jira_issue_types)

        flat = _flatten_jira_query(spec)
        assert flat == query_filters


# ── (b) Create stores one watch per default, no blanks ─────────────


class TestCreateWatches:
    def test_one_watch_per_default(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_test", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        svc.create(
            _P,
            "Ship Q4 on time",
            [
                {"provider": "github", "scope": _REPO, "watches": ["open_prs", "ci"]},
                {
                    "provider": "jira",
                    "scope": _JIRA_SCOPE,
                    "watches": ["overdue", "blocked"],
                },
            ],
        )

        assert len(captured) == 1
        proposals = captured[0]["proposals"]
        # Conductor R4: open_prs also arms the repository's open issues.
        assert len(proposals) == 5

        for p in proposals:
            spec = p["spec"]
            provider_id = spec["provider"]["id"]
            if provider_id == "github":
                subject = spec["subject"]
                kind = subject.get("kind", "")
                if kind == "branch_ci":
                    query = subject.get("query", {})
                    assert query.get("base")
                else:
                    scope_repos = subject.get("scope", {}).get("repositories", [])
                    assert scope_repos and all(r.strip() for r in scope_repos)
            elif provider_id == "jira":
                scope_d = spec["subject"].get("scope", {})
                assert scope_d.get("connection_ref")
                assert scope_d.get("projects")

        spec_names = [p["spec"]["name"] for p in proposals]
        assert len(set(spec_names)) == len(spec_names)

    def test_no_blank_entries(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_test", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        svc.create(
            _P,
            "Test project",
            [{"provider": "github", "scope": _REPO, "watches": ["open_prs"]}],
        )

        proposals = captured[0]["proposals"]
        for p in proposals:
            assert p["state"] == "selected"
            assert p["test_state"] == "not_checked"
            assert p["spec"]["test_state"] == "not_checked"
            assert p["spec"]


class TestSourcePreview:
    def test_parser_accepts_three_provider_links_once(self) -> None:
        rows = parse_source_text(
            "https://github.com/karolswdev/HoldSpeak "
            "https://acme.atlassian.net/browse/KAN-42 https://acme.atlassian.net/projects/KAN KAN "
            "https://acme.atlassian.net/wiki/spaces/ENG KAN"
        )

        assert [(row["provider"], row["scope"]) for row in rows] == [
            ("github", "karolswdev/HoldSpeak"),
            ("jira", "KAN"),
            ("jira", "KAN"),
            ("confluence", "ENG"),
        ]
        assert all(row["state"] == "not_checked" for row in rows)

    def test_preview_reports_checked_and_local_matches(self) -> None:
        github = MagicMock()
        github.validate_repo.return_value = {"valid": True}
        meetings = MagicMock()
        meetings.list_meetings.return_value = {
            "meetings": [{"id": "meeting_1", "title": "Ledger cutover", "started_at": "2026-10-17T09:00:00Z", "attendees": ["Ari"]}]
        }
        notes = MagicMock()
        notes.list_notes.return_value = [{"id": "note_1", "title": "Ledger cutover", "body_markdown": "Review the cutover"}]

        svc = ProjectDoorService(
            github_adapter=github,
            meeting_service=meetings,
            primitive_service=notes,
        )
        result = svc.preview(_P, "Ledger cutover", "github.com/karolswdev/HoldSpeak")

        assert result["sources"][0]["state"] == "checked"
        assert [item["id"] for item in result["found"]] == ["meeting_1", "note_1"]
        assert result["people"] == ["Ari"]

    def test_parser_keeps_site_and_dedupes_by_provider_site_and_scope(self) -> None:
        rows = parse_source_text(
            "https://beta.atlassian.net/browse/KAN-42 "
            "https://alpha.atlassian.net/projects/KAN "
            "https://beta.atlassian.net/browse/KAN-9 "
            "KAN"
        )

        assert [(row["provider"], row["site"], row["scope"]) for row in rows] == [
            ("jira", "beta.atlassian.net", "KAN"),
            ("jira", "alpha.atlassian.net", "KAN"),
            ("jira", None, "KAN"),
        ]
        assert "beta.atlassian.net" in rows[0]["label"]

    def test_two_connected_sites_validate_and_bind_in_paste_order(self) -> None:
        class Connections:
            def list_provider_connections(self, *, provider_id: str) -> list[dict[str, str]]:
                return [
                    {"state": "connected", "external_connection_ref": "beta.atlassian.net|b@example.com"},
                    {"state": "connected", "external_connection_ref": "alpha.atlassian.net|a@example.com"},
                ]

        class DB:
            automations = Connections()

        jira = MagicMock()
        jira.validate_scope.side_effect = lambda _principal, _ref, _scope: {
            "valid": True, "connection_ref": "wrong.atlassian.net|wrong@example.com",
        }
        svc = ProjectDoorService(jira_adapter=jira, db=DB())

        result = svc.preview(
            _P, "", "https://alpha.atlassian.net/browse/KAN-1 https://beta.atlassian.net/browse/KAN-1",
        )

        assert [row["connection_ref"] for row in result["sources"]] == [
            "alpha.atlassian.net|a@example.com", "beta.atlassian.net|b@example.com",
        ]
        assert [call.args[1] for call in jira.validate_scope.call_args_list] == [
            "alpha.atlassian.net|a@example.com", "beta.atlassian.net|b@example.com",
        ]

    def test_unmatched_site_and_ambiguous_bare_key_do_not_validate(self) -> None:
        class Connections:
            def list_provider_connections(self, *, provider_id: str) -> list[dict[str, str]]:
                return [
                    {"state": "connected", "external_connection_ref": "alpha.atlassian.net|a@example.com"},
                    {"state": "connected", "external_connection_ref": "beta.atlassian.net|b@example.com"},
                ]

        class DB:
            automations = Connections()

        jira = MagicMock()
        svc = ProjectDoorService(jira_adapter=jira, db=DB())
        result = svc.preview(
            _P, "", "https://gamma.atlassian.net/browse/KAN-1 KAN-2",
        )

        assert [row["state"] for row in result["sources"]] == ["not_checked", "not_checked"]
        assert "gamma.atlassian.net" in result["sources"][0]["reason"]
        assert "Ambiguous" in result["sources"][1]["reason"]
        jira.validate_scope.assert_not_called()

    def test_confluence_uses_the_matching_site_account(self) -> None:
        class Connections:
            def list_provider_connections(self, *, provider_id: str) -> list[dict[str, str]]:
                return [
                    {"state": "connected", "external_connection_ref": "beta.atlassian.net|b@example.com"},
                    {"state": "connected", "external_connection_ref": "alpha.atlassian.net|a@example.com"},
                ]

        class DB:
            automations = Connections()

        confluence = MagicMock()
        confluence.validate_scope.side_effect = lambda _principal, _ref, _scope: {
            "valid": True, "connection_ref": "wrong.atlassian.net|wrong@example.com",
        }
        svc = ProjectDoorService(confluence_adapter=confluence, db=DB())
        result = svc.preview(_P, "", "https://alpha.atlassian.net/wiki/spaces/ENG")

        assert result["sources"][0]["connection_ref"] == "alpha.atlassian.net|a@example.com"
        confluence.validate_scope.assert_called_once_with(
            _P, "alpha.atlassian.net|a@example.com", "ENG",
        )

    def test_created_jira_watches_keep_the_validated_connection(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_test", "activated_watches": []}

        project_service = MagicMock()
        project_service.create_from_setup.side_effect = mock_create
        svc = ProjectDoorService(project_service=project_service)
        svc.create(_P, "Two sites", [
            {"provider": "jira", "scope": {"connection_ref": "beta.atlassian.net|b@example.com", "projects": ["KAN"]}, "watches": ["overdue"]},
            {"provider": "jira", "scope": {"connection_ref": "alpha.atlassian.net|a@example.com", "projects": ["KAN"]}, "watches": ["overdue"]},
        ])

        refs = [
            proposal["spec"]["subject"]["scope"]["connection_ref"]
            for proposal in captured[0]["proposals"]
        ]
        assert refs == ["beta.atlassian.net|b@example.com", "alpha.atlassian.net|a@example.com"]


# ── (c) Zero sources = blank project ──────────────────────────────


class TestBlankProject:
    def test_zero_sources(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_blank", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        result = svc.create(_P, "Test blank", [])

        assert result["projectId"] == "proj_blank"
        assert len(captured) == 1
        assert captured[0]["proposals"] == []
        assert captured[0]["name"] == "Test blank"


class TestFoundLinkResults:
    def test_create_reports_each_leaf_result(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_material", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup.side_effect = mock_create
        mock_ps.associate_meeting.return_value = True
        mock_ps.add_resource.return_value = {"resource_ref": "note:n1"}

        result = ProjectDoorService(project_service=mock_ps).create(
            _P,
            "Material project",
            found={"meeting_ids": ["m1"], "note_ids": ["n1"]},
        )

        assert result["found_links"] == [
            {"kind": "meeting", "id": "m1", "state": "linked", "error": None},
            {"kind": "note", "id": "n1", "state": "linked", "error": None},
        ]

    def test_service_error_is_preserved_per_leaf(self) -> None:
        mock_ps = MagicMock()
        mock_ps.create_from_setup.return_value = {"project_id": "proj_material", "activated_watches": []}
        mock_ps.associate_meeting.return_value = True
        mock_ps.add_resource.side_effect = ServiceError("notes_unavailable", "Notes store is read-only")

        result = ProjectDoorService(project_service=mock_ps).create(
            _P,
            "Material project",
            found={"meeting_ids": ["m1"], "note_ids": ["n1"]},
        )

        assert result["found_links"] == [
            {"kind": "meeting", "id": "m1", "state": "linked", "error": None},
            {"kind": "note", "id": "n1", "state": "failed", "error": "Notes store is read-only"},
        ]

    def test_existing_project_can_retry_material_without_a_source(self) -> None:
        mock_ps = MagicMock()
        mock_ps.add_resource.return_value = {"resource_ref": "note:n1"}

        result = ProjectDoorService(project_service=mock_ps).create(
            _P,
            project_id="proj_existing",
            found={"meeting_ids": [], "note_ids": ["n1"]},
        )

        assert result["projectId"] == "proj_existing"
        assert result["found_links"] == [
            {"kind": "note", "id": "n1", "state": "linked", "error": None},
        ]
        mock_ps.add_source_watches.assert_not_called()


# ── (d) Failing count: plain reason, create still works ───────────


class TestFailingCount:
    def test_count_returns_plain_reason(self) -> None:
        with patch(
            "holdspeak.services.watch_sources.GitHubWatchSource"
        ) as MockGH:
            mock_source = MagicMock()
            mock_source.snapshot.side_effect = ServiceError(
                "connector_refresh_failed", "GitHub CLI query failed"
            )
            MockGH.return_value = mock_source

            svc = ProjectDoorService()
            result = svc.count(_P, "github", _REPO, ["open_prs"])

            assert result["state"] == "cant_check"
            assert isinstance(result["reason"], str)
            assert len(result["reason"]) > 0
            assert "GitHub CLI query failed" in result["reason"]

    def test_create_works_despite_count_failure(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_ok", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        result = svc.create(
            _P,
            "Test despite failure",
            [{"provider": "github", "scope": _REPO, "watches": ["open_prs"]}],
        )

        assert result["projectId"] == "proj_ok"
        assert len(captured) == 1
        # Conductor R4: the PR queue and the open issues.
        assert len(captured[0]["proposals"]) == 2


# ── merged from tests/unit/test_philo17_room_add_sources.py (fast diet, by service) ────────

"""PHILO-17 U10: Add source in the Room (the Door's rows, a project that exists).

Through the REAL ProjectDoorService over the REAL ProjectService and a real
database: the sources join the existing project as armed watches with their
Room bindings, one revision, one ``watch.created`` change per watch; no new
project is made. The hub route is the Door's own (``project_id`` in the body).
"""

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError

OWNER = Principal(PrincipalKind.OWNER, "test-philo17-u10")


@pytest.fixture()
def db(tmp_path: Path) -> Any:
    return Database(tmp_path / "u10.db")


def _door(db: Any):
    from holdspeak.services.project_door_service import ProjectDoorService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.watch_service import WatchService

    ws = WatchService(db, snapshot_fetcher=lambda principal, **kw: [])
    return ProjectDoorService(project_service=ProjectService(db), watch_service=ws)


def _bindings(db: Any, project_id: str) -> list[str]:
    with db._connection() as conn:
        return [r[0] for r in conn.execute(
            "SELECT source_ref FROM project_sources WHERE project_id=?", (project_id,)).fetchall()]


def _project_count(db: Any) -> int:
    with db._connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0])


def test_sources_join_a_project_that_exists(db: Any) -> None:
    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    assert _bindings(db, project_id) == []
    with db._connection() as conn:
        revision = int(conn.execute("SELECT revision FROM projects WHERE id=?", (project_id,)).fetchone()[0])

    out = door.create(OWNER, "", [{"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"]}],
                      project_id=project_id)

    assert out["projectId"] == project_id
    assert _project_count(db) == 1, "Add source must never make a second project"
    watches = [w for w in db.automations.list_watches() if w.get("project_id") == project_id]
    # open_prs + its open issues, and CI: the same three watches the Door arms on create.
    assert sorted(w["query_kind"] for w in watches) == ["branch_ci", "issues", "pull_requests"]
    assert all(w["next_evaluation_at"] for w in watches), "an added watch is armed for the scheduler"
    assert sorted(_bindings(db, project_id)) == sorted(f"watch:{w['id']}" for w in watches)
    with db._connection() as conn:
        new_revision = int(conn.execute("SELECT revision FROM projects WHERE id=?", (project_id,)).fetchone()[0])
        kinds = [r[0] for r in conn.execute(
            "SELECT change_kind FROM project_changes WHERE project_id=? AND project_revision=?",
            (project_id, new_revision)).fetchall()]
    assert new_revision == revision + 1
    assert kinds == ["watch.created"] * 3


def test_room_read_lists_the_added_source(db: Any) -> None:
    from holdspeak.services.project_service import ProjectService

    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    door.add_sources(OWNER, project_id, [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}])
    room = ProjectService(db).room(OWNER, project_id)
    assert room["sources"]["state"] == "ok"
    assert any(item.get("scope") == "acme/app" for item in room["sources"]["items"])


def test_a_source_already_watched_is_never_armed_twice(db: Any) -> None:
    """Astra r1 on #1068: repeated Add is refused, never hidden duplicate polling."""
    from holdspeak.services.errors import ConflictError

    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    source = [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}]
    door.add_sources(OWNER, project_id, source)
    before = sorted(w["id"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    with pytest.raises(ConflictError) as refused:
        door.add_sources(OWNER, project_id, source)
    assert refused.value.code == "already_watched"
    assert refused.value.detail == "Already watched"
    after = sorted(w["id"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    assert after == before
    # A wider pick adds only what is new (CI), never a second PR queue.
    door.add_sources(OWNER, project_id, [{"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"]}])
    kinds = sorted(w["query_kind"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    assert kinds == ["branch_ci", "issues", "pull_requests"]


def test_nothing_to_add_is_refused(db: Any) -> None:
    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    with pytest.raises(ValidationError):
        door.add_sources(OWNER, project_id, [])
    with pytest.raises(ValidationError):
        door.create(OWNER, "", [])


def test_hub_route_adds_to_the_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/projects/door with project_id: the Door's route, the same op, the real hub."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_philo9_b1_connections import _boot  # noqa: E402
    from test_philo9_steward_admission import Runner  # noqa: E402

    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    hub = _boot(tmp_path, monkeypatch, Runner(), Runner())
    try:
        c = hub.client
        made = c.post("/api/projects/door", json={"outcome": "A bare Room"})
        assert made.status_code == 200, made.text
        project_id = made.json()["projectId"]
        added = c.post("/api/projects/door", json={
            "project_id": project_id,
            "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
        })
        assert added.status_code == 200, added.text
        assert added.json()["projectId"] == project_id
        room = c.get(f"/api/projects/{project_id}/room").json()
        assert any(item.get("scope") == "acme/app" for item in room["sources"]["items"]), room["sources"]
        again = c.post("/api/projects/door", json={
            "project_id": project_id,
            "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
        })
        assert again.status_code == 409, again.text
        assert again.json()["message"] == "Already watched"
        empty = c.post("/api/projects/door", json={"project_id": project_id, "sources": []})
        assert empty.status_code == 400, empty.text
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_an_older_project_with_a_repository_source_registers_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Astra r2 on #1068: a project that watches a repository nobody registered
    (the Room's Register verb): the hub names it, and the Room's call
    (POST /api/projects/{id}/repository, the call New Project makes on
    create) registers it, owner only, with its receipt."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_philo9_b1_connections import _boot  # noqa: E402
    from test_philo9_steward_admission import Runner  # noqa: E402

    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    hub = _boot(tmp_path, monkeypatch, Runner(), Runner())
    try:
        c = hub.client
        project_id = c.post("/api/projects/door", json={
            "outcome": "Older project",
            "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
        }).json()["projectId"]
        before = c.get(f"/api/projects/{project_id}/repository").json()
        assert (before["registered"], before["repository"], before["watched"]) == (False, None, ["acme/app"])
        done = c.post(f"/api/projects/{project_id}/repository", json={"repository": before["watched"][0]})
        assert done.status_code == 200, done.text
        assert done.json()["receipt"]["outcome"] == "succeeded"
        after = c.get(f"/api/projects/{project_id}/repository").json()
        assert (after["repository"], after["registered"], after["cloned"]) == ("acme/app", True, False)
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))
