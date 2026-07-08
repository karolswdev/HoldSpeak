"""The key-control chokepoint (HS-89-01).

Full key control rides the SAME grant → verify %N → send → audit shape as
`deliver`, sending keys instead of text. What's pinned: an unknown named key
is refused BY NAME (never handed to tmux), nothing is sent unarmed, a
recycled pane refuses AND revokes for keys too, the send targets the
VERIFIED %N, and every attempt — delivered or refused — leaves an audit row
whose head reads like what a human did (`C-c`, `Down Down Enter`).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.coder_steering import (
    arm,
    clear_grants,
    deliver_keys,
    is_named_key,
    normalize_keys,
    render_keys,
)


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

    def transport(self, *, pane, keys):
        self.sent.append({"pane": pane, "keys": keys})


# --- the vocabulary allow-list (injection discipline) ----------------------


def test_named_key_allow_list_admits_real_keys_and_refuses_junk() -> None:
    for good in ("C-c", "C-d", "M-x", "C-M-x", "Escape", "Up", "Down", "Enter", "Tab", "F5"):
        assert is_named_key(good), good
    for bad in ("rm -rf /", "C-;", "banana", "Down Down", "", "$(whoami)", ";reboot"):
        assert not is_named_key(bad), bad


def test_normalize_accepts_named_strings_dicts_and_literals() -> None:
    keys, bad = normalize_keys(["C-c", {"key": "Down"}, {"literal": "/find"}, {"text": "x"}])
    assert bad is None
    assert keys == [("named", "C-c"), ("named", "Down"), ("literal", "/find"), ("literal", "x")]


def test_normalize_refuses_an_unknown_named_key_by_name() -> None:
    keys, bad = normalize_keys(["C-c", "sudo reboot"])
    assert keys == []
    assert bad == "sudo reboot"


def test_render_reads_like_a_human_did_it() -> None:
    keys, _ = normalize_keys([{"literal": "/search"}, "Down", "Down", "Enter"])
    assert render_keys(keys) == '"/search" Down Down Enter'


# --- the chokepoint --------------------------------------------------------


def test_unknown_key_refuses_sends_nothing_and_audits() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    result = deliver_keys(
        "claude:a", ["reboot now"],
        current_target="hs:0.0", agent="claude",
        runner=_identity_runner("%9"), transport=rec.transport, audit=rec.audit,
    )
    assert result["status"] == "unknown_key"
    assert result["detail"] == "reboot now"
    assert rec.sent == []  # not one keystroke
    assert rec.rows[0]["outcome"] == "unknown_key"


def test_unarmed_key_control_refuses_and_audits() -> None:
    rec = _Recorder()
    result = deliver_keys(
        "claude:a", ["C-c"],
        current_target="hs:0.0", agent="claude",
        runner=_identity_runner(), transport=rec.transport, audit=rec.audit,
    )
    assert result["status"] == "unarmed"
    assert rec.sent == []
    assert rec.rows[0]["outcome"] == "unarmed"
    assert rec.rows[0]["text"] == "C-c"  # the head reads the key even on refusal


def test_empty_sequence_refuses() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    result = deliver_keys(
        "claude:a", [],
        current_target="hs:0.0", agent="claude",
        runner=_identity_runner("%9"), transport=rec.transport, audit=rec.audit,
    )
    assert result["status"] == "empty_keys"
    assert rec.sent == []


def test_armed_key_control_sends_to_the_verified_pane_and_audits() -> None:
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    result = deliver_keys(
        "claude:a", ["C-c"],
        current_target="hs:0.0", agent="claude",
        runner=_identity_runner("%9"), transport=rec.transport, audit=rec.audit,
    )
    assert result["status"] == "delivered"
    assert result["pane_id"] == "%9"
    assert rec.sent == [{"pane": "%9", "keys": [("named", "C-c")]}]
    row = rec.rows[0]
    assert row["outcome"] == "delivered" and row["pane_id"] == "%9" and row["text"] == "C-c"


def test_recycled_pane_refuses_and_revokes_for_keys_too() -> None:
    # The crown case: armed on %9, but the pane now resolves to %13 (recycled)
    # — key control refuses AND revokes, exactly like text steering.
    rec = _Recorder()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"))
    result = deliver_keys(
        "claude:a", ["C-c"],
        current_target="hs:0.0", agent="claude",
        runner=_identity_runner("%13"), transport=rec.transport, audit=rec.audit,
    )
    assert result["status"] == "pane_mismatch"
    assert result.get("revoked") is True
    assert rec.sent == []  # nothing typed into the wrong pane
