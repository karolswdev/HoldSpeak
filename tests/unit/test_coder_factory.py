"""The session factory (HS-90-01).

Fake runner, recording audit — what's pinned: a bad session name is refused
BY NAME and never reaches tmux; spawn returns the new pane; kill rides the
STEER gate (unarmed refuses, a recycled pane refuses AND revokes, an armed
kill ends the verified %N and drops the grant); every act is audited.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak import coder_factory, coder_steering


@pytest.fixture(autouse=True)
def _fresh():
    coder_steering.clear_grants()
    yield
    coder_steering.clear_grants()


class _Rec:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def audit(self, **kw):
        self.rows.append(kw)
        return len(self.rows)


def _runner(script):
    """script: (argv) -> (stdout, returncode, stderr)."""
    def run(argv, cwd=None):
        out, rc, err = script(argv)
        return SimpleNamespace(stdout=out, returncode=rc, stderr=err)
    return run


# --- name guard (injection discipline) -------------------------------------


def test_valid_name_allows_safe_refuses_payloads() -> None:
    for good in ("work", "hs-89", "my_session", "a.b", "X1"):
        assert coder_factory.valid_name(good), good
    for bad in ("rm -rf /", "a;b", "$(x)", "a b", "", "a" * 65, "-flag", "`x`"):
        assert not coder_factory.valid_name(bad), bad


def test_spawn_bad_name_never_reaches_tmux() -> None:
    rec = _Rec()
    calls: list[list[str]] = []
    r = coder_factory.spawn("evil; reboot", runner=_runner(lambda a: (calls.append(a), ("", 0, ""))[1]), audit=rec.audit)
    assert r["status"] == "bad_name"
    assert calls == []  # tmux never ran
    assert rec.rows[0]["outcome"] == "bad_name"


def test_spawn_creates_and_returns_the_pane() -> None:
    rec = _Rec()
    def script(argv):
        if argv[:2] == ["tmux", "new-session"]:
            return ("", 0, "")
        if argv[:2] == ["tmux", "list-panes"]:
            return ("%7\n", 0, "")
        return ("", 0, "")
    r = coder_factory.spawn("work", command="htop", runner=_runner(script), audit=rec.audit)
    assert r["status"] == "spawned" and r["session"] == "work" and r["pane_id"] == "%7"
    assert rec.rows[0]["outcome"] == "spawned" and "spawn work" in rec.rows[0]["text"]


def test_rename_relabels_with_the_same_guard() -> None:
    rec = _Rec()
    assert coder_factory.rename("work", "bad name", runner=_runner(lambda a: ("", 0, "")), audit=rec.audit)["status"] == "bad_name"
    r = coder_factory.rename("work", "shipped", runner=_runner(lambda a: ("", 0, "")), audit=rec.audit)
    assert r["status"] == "renamed" and r["session"] == "shipped"


# --- kill = the steer gate -------------------------------------------------


def _identity(pane="%5"):
    return lambda argv, cwd=None: SimpleNamespace(stdout=f"{pane}\n", returncode=0, stderr="")


def test_kill_unarmed_refuses_and_audits() -> None:
    rec = _Rec()
    r = coder_factory.kill("claude:a", current_target="hs:0.0", runner=_identity(), audit=rec.audit)
    assert r["status"] == "unarmed"
    assert rec.rows[0]["outcome"] == "unarmed"


def test_kill_recycled_pane_refuses_and_revokes() -> None:
    rec = _Rec()
    coder_steering.arm("claude:a", "hs:0.0", runner=_identity("%9"))
    r = coder_factory.kill("claude:a", current_target="hs:0.0", runner=_identity("%13"), audit=rec.audit)
    assert r["status"] == "pane_mismatch" and r.get("revoked") is True


def test_armed_kill_ends_the_verified_pane_and_drops_the_grant() -> None:
    rec = _Rec()
    coder_steering.arm("claude:a", "hs:0.0", runner=_identity("%9"))
    killed_argv: list[list[str]] = []
    def script(argv):
        if argv[:2] == ["tmux", "kill-pane"]:
            killed_argv.append(argv)
            return ("", 0, "")
        return ("%9\n", 0, "")  # identity resolution
    r = coder_factory.kill("claude:a", current_target="hs:0.0", scope="pane", runner=_runner(script), audit=rec.audit)
    assert r["status"] == "killed" and r["pane_id"] == "%9" and r["scope"] == "pane"
    assert killed_argv == [["tmux", "kill-pane", "-t", "%9"]]
    assert coder_steering.active_grants() == {}  # the grant is dropped
    assert rec.rows[0]["outcome"] == "killed" and "kill %9 (pane)" in rec.rows[0]["text"]


def test_kill_session_scope_targets_the_session() -> None:
    coder_steering.arm("claude:a", "hs:0.0", runner=_identity("%9"))
    seen: list[list[str]] = []
    def script(argv):
        if argv[:2] == ["tmux", "kill-session"]:
            seen.append(argv); return ("", 0, "")
        return ("%9\n", 0, "")
    r = coder_factory.kill("claude:a", current_target="hs:0.0", scope="session", runner=_runner(script))
    assert r["status"] == "killed" and r["scope"] == "session"
    assert seen == [["tmux", "kill-session", "-t", "%9"]]
