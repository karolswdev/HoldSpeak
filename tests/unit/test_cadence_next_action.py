"""CAD-2-01 — the deterministic next-action generator."""
from __future__ import annotations

from holdspeak.cadence.models import EvidenceRef, OpenLoop
from holdspeak.cadence.next_action import generate_next_action


def _loop(**kw) -> OpenLoop:
    return OpenLoop(source_type=kw.pop("source_type", "meeting_action"),
                    source_id=kw.pop("source_id", "x"), title=kw.pop("title", "Ship the thing"),
                    id=kw.pop("id", "L1"), **kw)


def test_owned_action_drafts_an_issue_with_source():
    loop = _loop(owner="Karol", due_at="2026-06-30", project="holdspeak",
                 evidence=[EvidenceRef(kind="action_item", ref_id="a1", label="Standup",
                                       deep_link="/meetings/m1#ai-a1")])
    na = generate_next_action(loop)
    assert na.kind == "create_issue" and na.reversible is False
    assert "Owner: Karol" in na.body_markdown and "/meetings/m1#ai-a1" in na.body_markdown


def test_unowned_action_asks_to_assign_owner():
    na = generate_next_action(_loop(owner=None))
    assert na.kind == "assign_owner" and na.reversible is True


def test_proposal_maps_to_approve():
    na = generate_next_action(_loop(source_type="proposal", title="Create issue: watchdog"))
    assert na.kind == "approve_proposal" and na.reversible is False


def test_needs_review_maps_to_review_regardless_of_source():
    na = generate_next_action(_loop(source_type="meeting_action", owner="Karol", needs_review=True))
    assert na.kind == "review_draft" and na.reversible is True


def test_agent_question_maps_to_reply():
    na = generate_next_action(_loop(source_type="agent_question", title="SQLite or config?"))
    assert na.kind == "reply_to_agent"


def test_generator_is_deterministic():
    loop = _loop(owner="Karol")
    assert generate_next_action(loop).kind == generate_next_action(loop).kind
