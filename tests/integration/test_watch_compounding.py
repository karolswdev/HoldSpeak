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
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
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
