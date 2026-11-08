"""Parked 2026-11-08 (Lane I, engine door): PR review replay without a model
call, the pre-story review identity and the route-execution budget readers.
The review now runs once per press through the engine door. Kept, not run
(tests/_parked/conftest.py)."""
from __future__ import annotations

from typing import Any

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from tests.unit.test_drafters_read_memory import _decide  # noqa: F401
from tests.unit.test_memory_every_job import _ReviewRig  # noqa: F401


def _executions(db: Database, capability_id: str) -> list[Any]:
    with db._connection() as conn:
        return conn.execute(
            """SELECT e.tokens_reserved, e.token_budget, e.terminal_outcome
                 FROM inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                WHERE p.capability_id=?""",
            (capability_id,),
        ).fetchall()


def _full_memory_would_not_fit(db: Database, capability_id: str, full: Any, reserved_output_tokens: int) -> bool:
    """The admitted payload with the WHOLE memory block instead of the fitted one."""
    from holdspeak.services.memory_grounding import admitted_memory_prefix, with_memory

    adoption = _configure(db).inference_adoption_service
    with db._connection() as conn:
        row = conn.execute(
            """SELECT s.operation_id, e.route_plan_id
                 FROM inference_adoption_material_snapshots s,
                      inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                WHERE s.capability_id=? AND p.capability_id=?""",
            (capability_id, capability_id),
        ).fetchone()
    sent = adoption.admitted_payload(row["operation_id"])
    own = sent["user_prompt"][len(admitted_memory_prefix(sent["user_prompt"])):]
    return adoption.payload_room(
        route_plan_id=row["route_plan_id"], capability_id=capability_id,
        operation_id=row["operation_id"], payload={**sent, "user_prompt": with_memory(own, full)},
        reserved_output_tokens=reserved_output_tokens,
    ) < 0



def test_a_replay_rebuilds_the_reviews_own_material(rig, tmp_path, monkeypatch):
    """Astra P2 repro: the linked story changed between two reviews of the same
    commit and diff.  A replay may reuse only its MEMORY block, so the second
    review never returns the first review's stale artifact as a success."""
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    review = _ReviewRig(rig, tmp_path, monkeypatch)
    review.linked = [{"ref": "file:story-02-ledger.md", "text": "Story 02: move the ledger."}]
    first = review.post()
    assert first.status_code == 200, first.text

    # The same request again is an exact replay: one model call, one artifact.
    again = review.post()
    assert again.status_code == 200 and again.json()["artifact_id"] == first.json()["artifact_id"]
    assert len(review.engine.prompts) == 1

    review.linked = [{"ref": "file:story-02-ledger.md", "text": "Story 02: move the ledger. EDITED."}]
    second = review.post()
    stale = second.status_code == 200 and second.json().get("artifact_id") == first.json()["artifact_id"]
    assert not stale, "a changed story returned the first review as a success"
    # The story is part of the request identity (2026-10-05; it was an HTTP
    # 500 before): a changed story is a new review run with its own artifact,
    # and the model reads the edited story.
    assert second.status_code == 200, second.text
    assert len(review.engine.prompts) == 2
    assert "EDITED" in review.engine.prompts[1]
    # And that edited request replays exactly too.
    third = review.post()
    assert third.status_code == 200 and third.json()["artifact_id"] == second.json()["artifact_id"]
    assert len(review.engine.prompts) == 2




def test_a_review_made_before_the_story_joined_the_identity_still_replays(rig, tmp_path, monkeypatch):
    """Astra on #867 (P2): a review made by the base branch (its identity had no
    story) replays when the story is unchanged; an edited story is a new run."""
    from holdspeak.web.routes import delivery_prs

    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    review = _ReviewRig(rig, tmp_path, monkeypatch)
    review.linked = [{"ref": "file:story-02-ledger.md", "revision": "r1",
                      "text": "Story 02: move the ledger."}]
    # The base branch's route: the identity leaves the story out.
    with monkeypatch.context() as base:
        base.setattr(delivery_prs, "_legacy_review_matches", lambda *_args: True)
        legacy = review.post()
    assert legacy.status_code == 200, legacy.text
    assert len(review.engine.prompts) == 1

    # This branch, identical material: the legacy review replays.
    again = review.post()
    assert again.status_code == 200, again.text
    assert again.json()["artifact_id"] == legacy.json()["artifact_id"]
    assert len(review.engine.prompts) == 1

    # An edited story: a new run with its own artifact.
    review.linked = [{"ref": "file:story-02-ledger.md", "revision": "r2",
                      "text": "Story 02: move the ledger. EDITED."}]
    edited = review.post()
    assert edited.status_code == 200, edited.text
    assert edited.json()["artifact_id"] != legacy.json()["artifact_id"]
    assert len(review.engine.prompts) == 2
