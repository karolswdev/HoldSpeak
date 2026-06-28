"""CAD-1-03 — deterministic, explainable stale-scoring."""
from __future__ import annotations

from datetime import datetime

from holdspeak.cadence.models import OpenLoop
from holdspeak.cadence.scoring import LoopSignals, score_loop

NOW = datetime(2026, 6, 28, 10, 0, 0)


def _loop(**kw) -> OpenLoop:
    return OpenLoop(source_type=kw.pop("source_type", "meeting_action"),
                    source_id=kw.pop("source_id", "x"), title=kw.pop("title", "t"), **kw)


def test_breakdown_sums_to_total():
    b = score_loop(_loop(priority="high"), now=NOW,
                   signals=LoopSignals(unowned=True, recurrence_count=2))
    assert round(sum(b.contributions.values()), 2) == b.total


def test_deterministic_with_injected_now():
    loop = _loop(priority="normal", created_at="2026-06-20T10:00:00")
    a = score_loop(loop, now=NOW)
    b = score_loop(loop, now=NOW)
    assert a.total == b.total


def test_accepted_unexecuted_outranks_unowned_outranks_plain():
    accepted = score_loop(_loop(priority="normal"), now=NOW,
                          signals=LoopSignals(accepted_unexecuted=True))
    unowned = score_loop(_loop(priority="normal"), now=NOW, signals=LoopSignals(unowned=True))
    plain = score_loop(_loop(priority="low"), now=NOW)
    assert accepted.total > unowned.total > plain.total


def test_needs_review_is_strongly_suppressed():
    normal = score_loop(_loop(priority="normal"), now=NOW)
    review = score_loop(_loop(priority="normal", needs_review=True), now=NOW)
    assert review.total < normal.total
    assert review.contributions["needs_review"] < 0


def test_agent_question_source_dominates():
    agent = score_loop(_loop(source_type="agent_question"), now=NOW)
    action = score_loop(_loop(source_type="meeting_action"), now=NOW)
    assert agent.total > action.total  # a blocked coding agent is the top signal


def test_dismissals_suppress():
    base = score_loop(_loop(priority="normal"), now=NOW)
    dismissed = score_loop(_loop(priority="normal"), now=NOW, signals=LoopSignals(dismissals=2))
    assert dismissed.total < base.total
