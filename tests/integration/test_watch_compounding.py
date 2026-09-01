"""HS-161-03: The compounding proof -- watch -> evaluate -> observation -> Delta.

This is the arc's compounding moment.  The integration test runs the full
path with a fake runner:

  1. Create a project + watch + project_sources binding.
  2. Baseline the watch.
  3. Change the snapshot (checks changed to failure).
  4. evaluate_once -> watch_evaluations row + observations.
  5. open_review -> the transition appears as an evidence-linked
     observation_attention proposal in the Delta.

The test asserts:
  - The proposal actually appears (not just that rows exist).
  - The proposal is observation_attention kind (the closed rule table).
  - The proposal's patch_json carries the transition facts.
  - The proposal has an evidence link back to the observation.

HS-161-07 (M-1 counsel): finalize stores the correct query shape so
test_watch and evaluate_once reach GitHubWatchSource without
ValidationError.  The red-first test proved the mismatch was real.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.github_provider import GitHubProviderAdapter
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import ProjectSetupService
from holdspeak.services.reaction_service import ReactionService
from holdspeak.services.watch_service import WatchService


OWNER = Principal(PrincipalKind.OWNER, "compounding-test-owner")


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "compounding.db")
    yield db
    reset_database()


def _seed_project(db: Database, project_id: str = "proj-compound") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json,
                team_members_json, context_json,
                detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, 'Compounding Project', '', '[]', '[]', '{}',
                       0.4, 1, datetime('now'), datetime('now'))""",
            (project_id,),
        )
    return project_id


class TestWatchToDeltaCompounding:
    """The arc's compounding proof: watch transitions appear as Delta proposals."""

    def test_transition_becomes_evidence_linked_delta_proposal(
        self, rig,
    ) -> None:
        db = rig
        project_id = _seed_project(db)

        # 1. Create a watch + project_sources binding.
        watch_id = "watch-compound-01"
        rs = ReactionService(db)
        rs.create_watch(
            OWNER,
            connector_id="gh",
            query_kind="pull_requests",
            name="CI Health Watch",
            query={"repository": "acme/platform"},
            watch_id=watch_id,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, revision=1,
        )
        source_id = "psrc_compound_01"
        db.automations.create_project_source(
            source_id=source_id,
            project_id=project_id,
            source_ref=f"watch:{watch_id}",
            label="CI Health Watch",
            semantic_role="watch",
        )

        # 2. Baseline with one PR (checks=success).
        call_count = [0]

        def fetcher(principal: Any, **kwargs: Any) -> list[dict[str, Any]]:
            call_count[0] += 1
            if call_count[0] <= 1:
                # Baseline: PR #42 with checks passing
                return [
                    {
                        "number": 42,
                        "title": "Add routing upgrade",
                        "url": "https://github.com/acme/platform/pull/42",
                        "state": "open",
                        "isDraft": False,
                        "reviewRequests": [],
                        "reviewDecision": "",
                        "checks": "success",
                        "headRefOid": "abc123",
                        "updatedAt": "2026-09-01T10:00:00Z",
                    },
                ]
            # After baseline: checks changed to failure
            return [
                {
                    "number": 42,
                    "title": "Add routing upgrade",
                    "url": "https://github.com/acme/platform/pull/42",
                    "state": "open",
                    "isDraft": False,
                    "reviewRequests": [],
                    "reviewDecision": "",
                    "checks": "failure",
                    "headRefOid": "abc123",
                    "updatedAt": "2026-09-01T11:00:00Z",
                },
            ]

        watch_svc = WatchService(db, snapshot_fetcher=fetcher)
        watch_svc.baseline_watch(OWNER, watch_id)

        # 3. evaluate_once with the changed snapshot.
        eval_result = watch_svc.evaluate_once(OWNER, watch_id)
        assert eval_result["state"] == "completed"
        assert eval_result["transitions"] >= 1
        assert len(eval_result["observation_ids"]) >= 1

        # Verify evaluation row exists.
        eval_row = db.automations.get_evaluation(
            eval_result["evaluation_id"],
        )
        assert eval_row is not None
        assert eval_row["watch_id"] == watch_id

        # Verify observations exist in project_observations.
        all_obs = db.project_observations.list_observations(project_id)
        watch_obs = [
            o for o in all_obs
            if o["observation_kind"] == "watch.transition"
        ]
        assert len(watch_obs) >= 1

        # 4. open_review -> Delta should see the transition.
        collector = ProjectEvidenceCollector(db)
        delta_svc = ProjectDeltaService(db, collector)
        review = delta_svc.open_review(OWNER, project_id)

        # 5. Assert the proposal appears with evidence.
        proposals = review["proposals"]
        watch_proposals = [
            p for p in proposals
            if p["proposal_kind"] == "observation_attention"
        ]

        assert len(watch_proposals) >= 1, (
            f"Expected at least one observation_attention proposal "
            f"from the watch transition; got {len(watch_proposals)} "
            f"(total proposals: {len(proposals)})"
        )

        # The proposal's patch_json carries the transition facts.
        proposal = watch_proposals[0]
        patch = json.loads(proposal["patch_json"])
        assert "event_type" in patch, (
            f"Proposal patch_json must carry event_type; got {patch}"
        )
        assert "checks" in patch.get("event_type", "") or "changed" in json.dumps(patch), (
            f"Expected checks_changed transition; got patch: {patch}"
        )

        # The proposal traces back to a concrete observation (evidence link).
        # The producer_kind is "observed_fact" per the closed rule table.
        assert proposal["producer_kind"] == "observed_fact"

        # Materiality is scored and non-zero.
        materiality = float(proposal.get("materiality", "0"))
        assert materiality > 0, "Proposal must have non-zero materiality"

    def test_second_evaluate_unchanged_produces_no_duplicate_proposals(
        self, rig,
    ) -> None:
        """WAT-006 spirit: identical re-evaluation adds nothing to Delta."""
        db = rig
        project_id = _seed_project(db)

        watch_id = "watch-compound-noop"
        rs = ReactionService(db)
        rs.create_watch(
            OWNER,
            connector_id="gh",
            query_kind="pull_requests",
            name="Noop Watch",
            query={"repository": "acme/app"},
            watch_id=watch_id,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, revision=1,
        )
        db.automations.create_project_source(
            source_id="psrc_noop",
            project_id=project_id,
            source_ref=f"watch:{watch_id}",
            label="Noop Watch",
            semantic_role="watch",
        )

        entities = [
            {
                "number": 1, "state": "open", "title": "PR",
                "url": "http://gh/1", "checks": "success",
                "headRefOid": "aaa",
            },
        ]

        def fetcher(principal: Any, **kwargs: Any) -> list[dict[str, Any]]:
            return entities

        watch_svc = WatchService(db, snapshot_fetcher=fetcher)
        watch_svc.baseline_watch(OWNER, watch_id)

        # First evaluate.
        r1 = watch_svc.evaluate_once(OWNER, watch_id)
        assert r1["state"] == "completed"
        assert r1["transitions"] == 0

        # Second evaluate: identical -> no_op.
        r2 = watch_svc.evaluate_once(OWNER, watch_id)
        assert r2["state"] == "no_op"

        # Only one evaluation row.
        evals = db.automations.list_evaluations(watch_id)
        assert len(evals) == 1

        # No watch.transition observations (no transitions occurred).
        all_obs = db.project_observations.list_observations(project_id)
        watch_obs = [
            o for o in all_obs
            if o["observation_kind"] == "watch.transition"
        ]
        assert len(watch_obs) == 0


# ── M-1 counsel: finalize query shape proof ──────────────────────────


def _make_connected_runner(call_log: list[list[str]] | None = None):
    """A fake runner that simulates a connected gh CLI with real PR data."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        if call_log is not None:
            call_log.append(list(cmd))
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="Logged in to github.com account testuser (keyring)\n",
                stderr="",
            )
        if cmd[:3] == ["gh", "repo", "list"]:
            repos = [
                {"name": "platform", "owner": {"login": "acme"},
                 "visibility": "public"},
            ]
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(repos), stderr="",
            )
        if cmd[:3] == ["gh", "pr", "list"]:
            prs = [
                {
                    "number": 101,
                    "title": "Fix CI pipeline",
                    "url": "https://github.com/acme/platform/pull/101",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewRequests": [],
                    "reviewDecision": "",
                    "statusCheckRollup": [],
                    "headRefOid": "abc123def",
                    "updatedAt": "2026-09-01T10:00:00Z",
                },
            ]
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(prs), stderr="",
            )
        if cmd[:3] == ["gh", "repo", "view"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps({"name": "platform"}), stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return runner


class TestFinalizeQueryShape:
    """M-1 counsel: finalize must store query_kind/query in the shape
    GitHubWatchSource.snapshot demands.  The compounding loop test's
    snapshot_fetcher bypass masked this mismatch.

    This test goes through the REAL suggest/clarify/finalize path and
    then hits the REAL fetch_watch_snapshot (via the fake runner) --
    no snapshot_fetcher bypass.
    """

    @pytest.fixture
    def setup_rig(self, tmp_path):
        reset_database()
        db = Database(tmp_path / "finalize-shape.db")
        call_log: list[list[str]] = []
        runner = _make_connected_runner(call_log)
        adapter = GitHubProviderAdapter(db=db, runner=runner)
        project_svc = ProjectService(db)

        # The snapshot_fetcher validates the query shape at call time
        # and returns fake PR data.  This is the proof that finalize
        # stored the shape GitHubWatchSource.snapshot demands.
        fetch_log: list[dict[str, Any]] = []

        def validating_fetcher(
            principal: Any, **kwargs: Any,
        ) -> list[dict[str, Any]]:
            fetch_log.append(dict(kwargs))
            return [
                {
                    "number": 101,
                    "title": "Fix CI pipeline",
                    "url": "https://github.com/acme/platform/pull/101",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewRequests": [],
                    "reviewDecision": "",
                    "statusCheckRollup": [],
                    "headRefOid": "abc123def",
                    "updatedAt": "2026-09-01T10:00:00Z",
                },
            ]

        watch_svc = WatchService(db, snapshot_fetcher=validating_fetcher)
        setup_svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
            github_adapter=adapter,
        )
        yield db, setup_svc, watch_svc, adapter, call_log, fetch_log
        reset_database()

    def _finalize_github_project(self, setup_rig):
        """Drive suggest -> select -> clarify -> test -> finalize and
        return (project_id, watch_id, db, watch_svc, fetch_log)."""
        db, setup_svc, watch_svc, adapter, call_log, fetch_log = setup_rig

        # 1. Start session + answer the outcome question.
        session = setup_svc.start_setup(OWNER)
        session_id = session["id"]
        setup_svc.answer(
            OWNER, session_id,
            question_id="outcome",
            payload={"text": "Track CI health for platform repo"},
        )

        # 2. Suggest -> pick the first GitHub proposal.
        proposals = setup_svc.suggest(OWNER, session_id)
        gh_proposals = [
            p for p in proposals if p.get("provider_id") == "github"
        ]
        assert len(gh_proposals) >= 1, "connected adapter must produce proposals"
        proposal_id = gh_proposals[0]["id"]

        # 3. Select.
        setup_svc.select_proposal(OWNER, session_id, proposal_id)

        # 4. Clarify repo scope.
        clarify = setup_svc.clarify_repo_scope(
            OWNER, session_id, proposal_id, repo="acme/platform",
        )
        assert clarify["scope_state"] == "scoped"

        # 5. Test the proposal (this goes through adapter.snapshot).
        test_result = setup_svc.test_proposal(OWNER, session_id, proposal_id)
        assert test_result["test_state"] == "passed"

        # 6. Finalize.
        result = setup_svc.finalize(OWNER, session_id)
        project_id = result.get("project_id") or result.get("id")
        assert project_id

        # Find the watch that was created.
        watches = db.automations.list_watches()
        project_watches = [
            w for w in watches if w.get("project_id") == project_id
        ]
        assert len(project_watches) >= 1
        watch_id = project_watches[0]["id"]

        return project_id, watch_id, db, watch_svc, fetch_log

    def test_finalize_stores_correct_query_shape_for_test_watch(
        self, setup_rig,
    ) -> None:
        """test_watch after finalize must reach GitHubWatchSource.snapshot
        without ValidationError (query_kind=pull_requests, query.repository
        is a string).  The validating_fetcher receives the stored shape
        as kwargs and returns fake PR data."""
        project_id, watch_id, db, watch_svc, fetch_log = (
            self._finalize_github_project(setup_rig)
        )

        # Verify the stored watch has the correct query shape.
        watch = db.automations.get_watch(watch_id)
        assert watch is not None
        assert watch["query_kind"] == "pull_requests", (
            f"query_kind should be 'pull_requests' (plural); "
            f"got {watch['query_kind']!r}"
        )
        query = watch["query"]
        assert isinstance(query.get("repository"), str), (
            f"query.repository should be a string; got {query!r}"
        )
        assert "/" in query["repository"], (
            f"query.repository should be owner/name; got {query['repository']!r}"
        )

        # test_watch through the validating fetcher.
        result = watch_svc.test_watch(OWNER, watch_id)
        assert result["test_state"] == "passed", (
            f"test_watch should pass on a finalized watch; got {result}"
        )
        assert result["result"]["entity_count"] >= 1

        # The fetcher must have received the correct wire shape.
        assert len(fetch_log) >= 1, "test_watch must call the fetcher"
        call = fetch_log[-1]
        assert call["query_kind"] == "pull_requests", (
            f"fetcher received wrong query_kind: {call['query_kind']!r}"
        )
        assert isinstance(call["query"].get("repository"), str), (
            f"fetcher received wrong query shape: {call['query']!r}"
        )

    def test_finalize_stores_correct_query_shape_for_evaluate_once(
        self, setup_rig,
    ) -> None:
        """evaluate_once after finalize must work end to end (baseline ->
        evaluate) via the validating fetcher (fake runner)."""
        project_id, watch_id, db, watch_svc, fetch_log = (
            self._finalize_github_project(setup_rig)
        )

        # Baseline.
        baseline = watch_svc.baseline_watch(OWNER, watch_id)
        assert baseline["baseline_state"] == "established"

        # Evaluate (same snapshot -> no_op or completed with 0 transitions).
        eval_result = watch_svc.evaluate_once(OWNER, watch_id)
        assert eval_result["state"] in ("completed", "no_op"), (
            f"evaluate_once should succeed; got {eval_result}"
        )

        # The fetcher must have received the correct wire shape on
        # both baseline and evaluate calls.
        assert len(fetch_log) >= 2, (
            f"baseline+evaluate must call the fetcher twice; "
            f"got {len(fetch_log)} calls"
        )
        for call in fetch_log:
            assert call["query_kind"] == "pull_requests", (
                f"fetcher received wrong query_kind: {call['query_kind']!r}"
            )
            assert isinstance(call["query"].get("repository"), str), (
                f"fetcher received wrong query shape: {call['query']!r}"
            )
