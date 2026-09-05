"""HS-161-02: GitHub Watch templates -- truth table, validation,
setup service integration, readiness gating, clarify paths, PROV-011.

Acceptance criteria tested:
- All five templates compile to valid WatchSpec@1 drafts
- Every compiled output passes watch_validation (definition of "compiles")
- Template table is closed (unknown ID refused)
- suggest() consults the live adapter (readiness gating truth table)
- connected => candidates; owner_action_required/degraded/unavailable => none
- clarify_repo_scope: discovered list path
- clarify_repo_scope: typed fallback path
- PROV-011: no invented repo identities
- Persistence symmetry with natives
- INT-008: candidate shape mirrors native shape
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.github_templates import (
    GITHUB_TEMPLATES,
    TEMPLATE_IDS,
    compile as compile_template,
)
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.github_provider import (
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_OWNER_ACTION_REQUIRED,
    STATE_UNAVAILABLE,
    GitHubProviderAdapter,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import (
    CADENCE_PRESETS,
    Q_OUTCOME,
    Q_SIGNALS,
    ProjectSetupService,
)
from holdspeak.watch_validation import validate_rules


OWNER = Principal(PrincipalKind.OWNER, "gh-tmpl-test-owner")


# ── Fake runner (reuses test_github_provider pattern) ────────────────

def _fake_runner(
    stdout: str = "", stderr: str = "", returncode: int = 0,
) -> Any:
    """Return a runner callable producing a fixed CompletedProcess."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    return runner


def _connected_runner() -> Any:
    """A runner that answers auth-status as connected."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, list) and "auth" in cmd and "status" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0,
                stdout="Logged in to github.com account testuser (keyring)\n",
                stderr="",
            )
        if isinstance(cmd, list) and "repo" in cmd and "list" in cmd:
            repos = [
                {"name": "platform", "owner": {"login": "acme"}, "visibility": "private"},
                {"name": "api", "owner": {"login": "acme"}, "visibility": "private"},
            ]
            return subprocess.CompletedProcess(
                args=cmd, returncode=0,
                stdout=json.dumps(repos),
                stderr="",
            )
        if isinstance(cmd, list) and "pr" in cmd and "list" in cmd:
            # validate_repo probe
            return subprocess.CompletedProcess(
                args=cmd, returncode=0,
                stdout="[]",
                stderr="",
            )
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="", stderr="",
        )
    return runner


def _disconnected_runner(state: str) -> Any:
    """A runner that answers auth-status as not connected."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, list) and "auth" in cmd and "status" in cmd:
            if state == STATE_OWNER_ACTION_REQUIRED:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1,
                    stdout="", stderr="You are not logged in to github.com\n",
                )
            if state == STATE_UNAVAILABLE:
                raise FileNotFoundError("gh not found")
            # degraded
            return subprocess.CompletedProcess(
                args=cmd, returncode=1,
                stdout="", stderr="unexpected error\n",
            )
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="", stderr="",
        )
    return runner


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path):
    """Setup rig with connected GitHub adapter."""
    reset_database()
    db = Database(tmp_path / "gh-tmpl-test.db")
    runner = _connected_runner()
    adapter = GitHubProviderAdapter(db=db, runner=runner)
    project_svc = ProjectService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=None,
        github_adapter=adapter,
    )
    yield db, project_svc, setup_svc, adapter
    reset_database()


@pytest.fixture
def rig_no_adapter(tmp_path):
    """Setup rig without GitHub adapter (159 behavior)."""
    reset_database()
    db = Database(tmp_path / "no-adapter-test.db")
    project_svc = ProjectService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=None,
    )
    yield db, project_svc, setup_svc
    reset_database()


def _seed_meeting(db: Database, meeting_id: str = "m-001",
                  title: str = "Weekly standup") -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 1, 10, 0),
        title=title,
        capture_status="finalized",
    ))


# ── Template truth table ─────────────────────────────────────────────


class TestTemplateTruthTable:
    """All five templates compile to valid WatchSpec@1 drafts."""

    def test_six_templates_exist(self) -> None:
        """HS-169-04: branch_ci added as the 6th template."""
        assert len(GITHUB_TEMPLATES) == 6
        assert TEMPLATE_IDS == {
            "watch.github.review_queue",
            "watch.github.ci_health",
            "watch.github.merge_flow",
            "watch.github.delivery_drift",
            "watch.github.release_readiness",
            "watch.github.branch_ci",
        }

    @pytest.mark.parametrize("tmpl", GITHUB_TEMPLATES, ids=lambda t: t.template_id)
    def test_template_compiles_valid(self, tmpl) -> None:
        """Every template compiles to a WatchSpec@1 that passes validation."""
        spec = compile_template(tmpl.template_id, "acme/platform")
        assert spec["schema"] == "WatchSpec@1"
        assert spec["provider"]["id"] == "github"
        # HS-169-04: branch_ci has its own subject kind
        assert spec["subject"]["kind"] in ("pull_request", "branch_ci")
        assert "acme/platform" in spec["subject"]["scope"]["repositories"]
        assert spec["trigger"]["kind"] == "poll"

        # The critical assertion: validates through watch_validation
        errors = validate_rules(spec["rules"])
        assert errors == [], f"Validation errors: {errors}"

    def test_review_queue_conditions(self) -> None:
        spec = compile_template("watch.github.review_queue", "acme/platform")
        clauses = spec["rules"][0]["condition"]["clauses"]
        fields = {c["field"] for c in clauses}
        assert "review_requested" in fields
        assert "review_decision" in fields
        assert spec["trigger"]["every_minutes"] == 15  # active_work

    def test_ci_health_conditions(self) -> None:
        spec = compile_template("watch.github.ci_health", "acme/platform")
        clauses = spec["rules"][0]["condition"]["clauses"]
        assert any(c["field"] == "checks" and c["value"] == "failure" for c in clauses)
        assert any(c["field"] == "checks" and c["value"] == "success" for c in clauses)
        actions = spec["rules"][0]["actions"]
        kinds = {a["kind"] for a in actions}
        assert "project.observe" in kinds
        assert "project.steward.run_once" in kinds

    def test_merge_flow_conditions(self) -> None:
        spec = compile_template("watch.github.merge_flow", "acme/platform")
        clauses = spec["rules"][0]["condition"]["clauses"]
        fields = {c["field"] for c in clauses}
        assert "state" in fields
        assert "merged" in fields
        assert spec["trigger"]["every_minutes"] == 35  # normal

    def test_delivery_drift_conditions(self) -> None:
        spec = compile_template("watch.github.delivery_drift", "acme/platform")
        clauses = spec["rules"][0]["condition"]["clauses"]
        assert any(c["field"] == "updated_at" and c["comparison"] == "older_than" for c in clauses)
        actions = spec["rules"][0]["actions"]
        kinds = {a["kind"] for a in actions}
        assert "door.add_item" in kinds
        assert spec["trigger"]["every_minutes"] == 1440  # daily

    def test_release_readiness_conditions(self) -> None:
        spec = compile_template("watch.github.release_readiness", "acme/platform")
        clauses = spec["rules"][0]["condition"]["clauses"]
        fields = {c["field"] for c in clauses}
        assert "head_sha" in fields
        assert "checks" in fields
        assert "review_decision" in fields
        actions = spec["rules"][0]["actions"]
        kinds = {a["kind"] for a in actions}
        assert "project.update.draft" in kinds

    def test_unknown_template_refused(self) -> None:
        with pytest.raises(ValueError, match="Unknown template"):
            compile_template("watch.github.bogus", "acme/platform")

    def test_empty_repo_scope_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one repository"):
            compile_template("watch.github.ci_health", [])

    def test_multi_repo_scope(self) -> None:
        spec = compile_template(
            "watch.github.ci_health",
            ["acme/platform", "acme/api"],
        )
        repos = spec["subject"]["scope"]["repositories"]
        assert repos == ["acme/platform", "acme/api"]

    def test_cadence_override(self) -> None:
        spec = compile_template(
            "watch.github.ci_health", "acme/platform",
            options={"cadence": "daily"},
        )
        assert spec["trigger"]["every_minutes"] == 1440

    def test_base_branch_override(self) -> None:
        spec = compile_template(
            "watch.github.ci_health", "acme/platform",
            options={"base": "develop"},
        )
        assert spec["subject"]["query"]["base"] == "develop"


# ── Readiness gating truth table ─────────────────────────────────────


class TestReadinessGating:
    """suggest() consults the live adapter; readiness gating truth table."""

    def test_connected_yields_github_candidates(self, rig) -> None:
        """connected => five github candidates appear."""
        db, _ps, svc, _adapter = rig
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Ship routing"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals
            if p.get("provider_id") == "github"
        ]
        # HS-168-02: suggest keeps _MAX_PROPOSALS_PER_PROVIDER (4) per source so
        # no connected provider is starved; five templates exist, four persist.
        from holdspeak.services.project_setup_service import _MAX_PROPOSALS_PER_PROVIDER
        assert len(github_proposals) == _MAX_PROPOSALS_PER_PROVIDER == 4

    def test_owner_action_required_yields_zero_github(self, tmp_path) -> None:
        """owner_action_required => zero github candidates."""
        reset_database()
        db = Database(tmp_path / "oar-test.db")
        runner = _disconnected_runner(STATE_OWNER_ACTION_REQUIRED)
        adapter = GitHubProviderAdapter(db=db, runner=runner)
        svc = ProjectSetupService(
            db, project_service=ProjectService(db),
            github_adapter=adapter,
        )
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        assert len(github_proposals) == 0
        reset_database()

    def test_degraded_yields_zero_github(self, tmp_path) -> None:
        """degraded => zero github candidates."""
        reset_database()
        db = Database(tmp_path / "deg-test.db")
        runner = _disconnected_runner(STATE_DEGRADED)
        adapter = GitHubProviderAdapter(db=db, runner=runner)
        svc = ProjectSetupService(
            db, project_service=ProjectService(db),
            github_adapter=adapter,
        )
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        assert len(github_proposals) == 0
        reset_database()

    def test_no_adapter_yields_zero_github(self, rig_no_adapter) -> None:
        """No adapter => 159 behavior, zero github candidates."""
        db, _ps, svc = rig_no_adapter
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        assert len(github_proposals) == 0

    def test_meeting_template_retired_from_suggestions(self, rig) -> None:
        """HS-169-04: the meeting template is retired; no native meeting
        proposals appear even when meetings exist on the desk."""
        db, _ps, svc, _adapter = rig
        _seed_meeting(db, "m-1", "Sprint review")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        meeting_proposals = [
            p for p in proposals
            if (p.get("spec") or {}).get("subject", {}).get("kind") == "meetings"
        ]
        assert len(meeting_proposals) == 0


# ── Candidate shape (INT-008) ────────────────────────────────────────


class TestCandidateShape:
    """INT-008: each recommendation names source, scope, conditions,
    action, cadence, readiness, and rationale."""

    def test_github_candidate_has_int008_fields(self, rig) -> None:
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Ship it"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        assert len(github_proposals) > 0

        for p in github_proposals:
            spec = p["spec"]
            rationale = p["rationale"]

            # Source
            assert rationale["source"] == "github"
            assert "template_id" in rationale

            # Scope (needs-scope at suggest time)
            assert spec["subject"]["kind"] == "pull_request"
            assert rationale["readiness"] == "needs_scope"

            # Conditions
            assert len(rationale["conditions"]) > 0
            assert spec["rules"]

            # Action
            assert rationale["action"]
            assert spec["action"]

            # Cadence
            assert rationale["cadence"]
            assert spec["trigger"]

            # Rationale text
            assert rationale["fact"]
            assert rationale["detail"]


# ── Persistence symmetry ─────────────────────────────────────────────


class TestPersistenceSymmetry:
    """GitHub proposals persist identically to native proposals
    (watch_setup_proposals table)."""

    def test_github_proposals_persisted(self, rig) -> None:
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]

        # Verify they're in the DB
        for p in github_proposals:
            row = db.automations.get_setup_proposal(p["id"])
            assert row is not None
            assert row["provider_id"] == "github"
            assert row["spec_schema"] == "WatchSpec@1"
            assert row["state"] == "proposed"

    def test_github_proposal_select_deselect(self, rig) -> None:
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        selected = svc.select_proposal(OWNER, session["id"], gh_p["id"])
        assert selected["state"] == "selected"

        deselected = svc.deselect_proposal(OWNER, session["id"], gh_p["id"])
        assert deselected["state"] == "proposed"


# ── Clarify: repo-scope paths ────────────────────────────────────────


class TestClarifyRepoScope:
    """clarify_repo_scope: discovered list + typed fallback paths."""

    def test_clarify_discovered_list(self, rig) -> None:
        """Discovered list path: adapter.discover() enumerates repos."""
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        # Clarify without specifying a repo -> discovery path
        result = svc.clarify_repo_scope(OWNER, session["id"], gh_p["id"])
        assert result["scope_state"] == "scoped"
        assert "acme/platform" in result["repositories"]
        assert "acme/api" in result["repositories"]

        # Verify the proposal spec was updated
        updated = db.automations.get_setup_proposal(gh_p["id"])
        spec = updated["spec"]
        assert spec["subject"]["scope"]["repositories"] == ["acme/platform", "acme/api"]

    def test_clarify_typed_fallback(self, rig) -> None:
        """Typed fallback path: adapter.validate_repo() checks one repo."""
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        result = svc.clarify_repo_scope(
            OWNER, session["id"], gh_p["id"], repo="acme/platform",
        )
        assert result["scope_state"] == "scoped"
        assert result["repositories"] == ["acme/platform"]

    def test_clarify_typed_invalid_repo(self, tmp_path) -> None:
        """Typed fallback: invalid repo returns scope_state=invalid."""
        reset_database()
        db = Database(tmp_path / "invalid-repo-test.db")

        def invalid_runner(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list) and "auth" in cmd:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0,
                    stdout="Logged in to github.com account testuser (keyring)\n",
                    stderr="",
                )
            # pr list validation fails
            return subprocess.CompletedProcess(
                args=cmd, returncode=1,
                stdout="", stderr="repository not found\n",
            )

        adapter = GitHubProviderAdapter(db=db, runner=invalid_runner)
        svc = ProjectSetupService(
            db, project_service=ProjectService(db),
            github_adapter=adapter,
        )
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        result = svc.clarify_repo_scope(
            OWNER, session["id"], gh_p["id"], repo="acme/nonexistent",
        )
        assert result["scope_state"] == "invalid"
        assert result["repositories"] == []
        reset_database()

    def test_clarify_no_adapter_raises(self, rig_no_adapter) -> None:
        """clarify_repo_scope without adapter raises ServiceError."""
        db, _ps, svc = rig_no_adapter
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})

        # Create a fake github proposal manually
        proposal_id = f"wprop_{__import__('uuid').uuid4().hex[:12]}"
        db.automations.create_setup_proposal(
            proposal_id=proposal_id,
            session_id=session["id"],
            provider_id="github",
            spec_schema="WatchSpec@1",
            spec_json=json.dumps({"subject": {"kind": "pull_request"}}),
            state="proposed",
        )

        with pytest.raises(ServiceError, match="GitHub adapter not configured"):
            svc.clarify_repo_scope(OWNER, session["id"], proposal_id)


# ── PROV-011: no invented repo identities ────────────────────────────


class TestProv011:
    """PROV-011: a candidate never names a repo the adapter did not
    surface/validate."""

    def test_suggest_candidates_carry_empty_scope(self, rig) -> None:
        """At suggest time, github candidates carry empty scope (needs_scope).
        They do NOT invent repository names."""
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        github_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        for p in github_proposals:
            scope = p["spec"]["subject"].get("scope", {})
            # No repositories key or empty repositories
            repos = scope.get("repositories", [])
            assert repos == [], (
                f"PROV-011 violation: candidate {p['id']} names repos "
                f"{repos} without discovery/validation"
            )

    def test_clarify_only_names_discovered_repos(self, rig) -> None:
        """After clarify (discovery path), repos come from adapter.discover()."""
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        result = svc.clarify_repo_scope(OWNER, session["id"], gh_p["id"])
        # Only repos from the fake runner's discover response
        for repo in result["repositories"]:
            assert repo in ("acme/platform", "acme/api"), (
                f"PROV-011 violation: repo {repo!r} not from adapter"
            )

    def test_clarify_typed_only_names_validated_repo(self, rig) -> None:
        """After typed clarify, repo comes from adapter.validate_repo()."""
        db, _ps, svc, _adapter = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        gh_p = [p for p in proposals if p.get("provider_id") == "github"][0]

        result = svc.clarify_repo_scope(
            OWNER, session["id"], gh_p["id"], repo="acme/platform",
        )
        assert result["repositories"] == ["acme/platform"]

    def test_compile_does_not_invent_repos(self) -> None:
        """compile() requires caller-provided repos; never invents them."""
        # The caller provides the repo -- compile() just places it
        spec = compile_template("watch.github.ci_health", "caller/provided")
        assert spec["subject"]["scope"]["repositories"] == ["caller/provided"]


# ── Adapter threading ────────────────────────────────────────────────


class TestAdapterThreading:
    """The github_adapter parameter is threaded through construction."""

    def test_adapter_none_preserves_159_behavior(self, rig_no_adapter) -> None:
        """github_adapter=None preserves existing 159 behavior."""
        db, _ps, svc = rig_no_adapter
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        # Only native proposals
        for p in proposals:
            assert p["provider_id"] == "native"

    def test_adapter_injected_via_constructor(self, rig) -> None:
        """github_adapter is accessible on the service instance."""
        _db, _ps, svc, adapter = rig
        assert svc._github_adapter is adapter


# ── Cadence preset consistency ───────────────────────────────────────


class TestCadenceConsistency:
    """github_templates.CADENCE_PRESETS matches project_setup_service.CADENCE_PRESETS."""

    def test_cadence_presets_match(self) -> None:
        from holdspeak.github_templates import CADENCE_PRESETS as GH_PRESETS
        for key in ("active_work", "normal", "daily", "weekdays"):
            assert key in GH_PRESETS
            assert key in CADENCE_PRESETS
            # Values match
            for field in ("kind", "every_minutes"):
                assert GH_PRESETS[key].get(field) == CADENCE_PRESETS[key].get(field), (
                    f"Cadence preset {key!r}.{field} mismatch: "
                    f"templates={GH_PRESETS[key].get(field)} vs "
                    f"setup={CADENCE_PRESETS[key].get(field)}"
                )
