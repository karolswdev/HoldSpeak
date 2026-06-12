"""HS-63-06: the meeting-glue → MeetingSession constructor contract.

The HS-63-06 live closeout caught a Phase-60 production bug the suite had
masked for three phases: `_start_meeting` passed `on_wake_type=` to
`MeetingSession(...)`, which never accepted it, so every real meeting start
through the web runtime failed with a TypeError — invisible to tests
because the FakeMeetingSession stub accepts ``**kwargs``. This lock binds
the real call site to the real signature so a stray kwarg can never hide
behind a permissive fake again.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _meeting_session_call_kwargs() -> set[str]:
    """The kwarg names meeting_glue's _start_meeting passes to MeetingSession."""
    tree = ast.parse((_REPO / "holdspeak" / "runtime" / "meeting_glue.py").read_text())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "MeetingSession"
        ):
            return {kw.arg for kw in node.keywords if kw.arg}
    raise AssertionError("no MeetingSession(...) call found in meeting_glue.py")


def test_start_meeting_passes_only_real_meeting_session_kwargs() -> None:
    from holdspeak.meeting_session import MeetingSession

    accepted = set(inspect.signature(MeetingSession.__init__).parameters) - {"self"}
    passed = _meeting_session_call_kwargs()
    stray = sorted(passed - accepted)
    assert not stray, (
        f"_start_meeting passes kwargs MeetingSession does not accept: {stray}. "
        "The real constructor would raise a TypeError on every live meeting "
        "start — and the FakeMeetingSession stub will not save you."
    )
    assert passed, "the call site lost its kwargs entirely — check the parse"
