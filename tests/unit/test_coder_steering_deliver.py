"""The deliver chokepoint (HS-87-03).

Fake runner, fake transport, recording audit — what's pinned: nothing
types unarmed, the send targets the VERIFIED %N (never the target
string), the text goes through exactly as composed, and every
attempt — delivered or refused — leaves its audit row.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.coder_steering import arm, clear_grants, deliver


@pytest.fixture(autouse=True)
def _fresh_store():
    clear_grants()
    yield
    clear_grants()


def _identity_runner(pane_id: str = "%5"):
    return lambda argv, cwd=None: SimpleNamespace(
        stdout=f"{pane_id}\n", returncode=0, stderr=""
    )


class _Recorder:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.sent: list[dict] = []

    def audit(self, **kw):
        self.rows.append(kw)
        return len(self.rows)

    def transport(self, *, pane, text, submit=True):
        self.sent.append({"pane": pane, "text": text, "submit": submit})


def test_unarmed_deliver_refuses_types_nothing_and_audits() -> None:
    rec = _Recorder()
    result = deliver(
        "claude:a",
        "do the thing",
        current_target="hs:0.0",
        agent="claude",
        runner=_identity_runner(),
        transport=rec.transport,
        audit=rec.audit,
    )
    assert result["status"] == "unarmed"
    assert result["audit_id"] == 1
    assert rec.sent == []  # not one keystroke
    assert rec.rows[0]["outcome"] == "unarmed"
    assert rec.rows[0]["session_key"] == "claude:a"


def test_armed_deliver_sends_the_exact_text_to_the_verified_pane() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    text = "line one\nline two\n  indented"
    result = deliver(
        "claude:a",
        text,
        current_target="hs:0.0",
        agent="claude",
        runner=_identity_runner("%9"),
        transport=rec.transport,
        audit=rec.audit,
    )
    assert result["status"] == "delivered"
    assert result["pane_id"] == "%9"
    # The send targets the verified %N, never the target string —
    # nothing can re-resolve between the check and the keystroke.
    assert rec.sent == [{"pane": "%9", "text": text, "submit": True}]
    assert rec.rows[0]["outcome"] == "delivered"
    assert rec.rows[0]["pane_id"] == "%9"


def test_no_submit_mode_rides_through_to_the_transport() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    deliver(
        "claude:a",
        "partial",
        current_target="hs:0.0",
        submit=False,
        runner=_identity_runner("%9"),
        transport=rec.transport,
        audit=rec.audit,
    )
    assert rec.sent[0]["submit"] is False
    assert rec.rows[0]["submit"] is False


def test_recycled_pane_refuses_revokes_audits_and_types_nothing() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    result = deliver(
        "claude:a",
        "meant for the old pane",
        current_target="hs:0.0",
        runner=_identity_runner("%13"),  # the target resolves elsewhere now
        transport=rec.transport,
        audit=rec.audit,
    )
    assert result["status"] == "pane_mismatch"
    assert result["revoked"] is True
    assert rec.sent == []
    assert rec.rows[0]["outcome"] == "pane_mismatch"


def test_transport_failure_is_audited_as_its_own_outcome() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))

    def broken_transport(*, pane, text, submit=True):
        raise RuntimeError("tmux exited with 1")

    result = deliver(
        "claude:a",
        "hello",
        current_target="hs:0.0",
        runner=_identity_runner("%9"),
        transport=broken_transport,
        audit=rec.audit,
    )
    assert result["status"] == "transport_error"
    assert rec.rows[0]["outcome"] == "transport_error"
    assert "tmux exited" in rec.rows[0]["detail"]


def test_empty_text_never_reaches_the_grant_check() -> None:
    rec = _Recorder()
    result = deliver(
        "claude:a",
        "   \n",
        current_target="hs:0.0",
        transport=rec.transport,
        audit=rec.audit,
    )
    assert result["status"] == "empty_text"
    assert rec.sent == []


def test_grounding_refs_ride_the_audit_row() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    deliver(
        "claude:a",
        "with context",
        current_target="hs:0.0",
        grounding_refs=["meeting:m1", "artifact:a2"],
        runner=_identity_runner("%9"),
        transport=rec.transport,
        audit=rec.audit,
    )
    assert rec.rows[0]["grounding"] == ["meeting:m1", "artifact:a2"]


def test_a_broken_audit_sink_never_blocks_the_refusal() -> None:
    def exploding_audit(**kw):
        raise RuntimeError("db is gone")

    result = deliver(
        "claude:a",
        "text",
        current_target="hs:0.0",
        runner=_identity_runner(),
        transport=lambda **kw: None,
        audit=exploding_audit,
    )
    assert result["status"] == "unarmed"
    assert result["audit_id"] is None
