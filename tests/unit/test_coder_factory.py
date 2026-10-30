"""The session factory (HS-90-01).

Fake runner, recording audit — what's pinned: a bad session name is refused
BY NAME and never reaches tmux; spawn returns the new pane; kill rides the
STEER gate (unarmed refuses, a recycled pane refuses AND revokes, an armed
kill ends the verified %N and drops the grant); every act is audited.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
import pytest

from holdspeak import coder_factory, coder_steering
from holdspeak.web.routes.system.coder_factory_routes import register_factory_routes


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


@pytest.mark.parametrize("session", ["owner-desk", "holdspeak-signin-owned;quit"])
def test_signin_cleanup_cannot_end_another_session(session) -> None:
    calls = []
    audit = _Rec()
    answer = coder_factory.discard_signin_session(session, runner=lambda *a, **k: calls.append(a), audit=audit.audit)
    assert answer["status"] == "bad_name"
    assert calls == []
    assert audit.rows[0]["outcome"] == "bad_name"


def test_failed_signin_cleanup_ends_only_its_private_session_and_revokes_its_credential(monkeypatch) -> None:
    from holdspeak.principals import agent_credentials

    revoked = []
    calls = []
    monkeypatch.setattr(agent_credentials, "revoke", lambda identity, reason: revoked.append((identity, reason)))
    def run(argv, **_kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0)
    answer = coder_factory.discard_signin_session("holdspeak-signin-0123456789", runner=run, audit=_Rec().audit)
    assert answer["status"] == "discarded"
    assert calls == [["tmux", "kill-session", "-t", "holdspeak-signin-0123456789"]]
    assert revoked == [("agent:tmux:holdspeak-signin-0123456789", "signin_target_failed")]


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
            from tests.unit._spawn_env import consume

            consume(argv)  # the session's bootstrap reads its credential
            return ("", 0, "")
        if argv[:2] == ["tmux", "list-panes"]:
            return ("%7\n", 0, "")
        return ("", 0, "")
    r = coder_factory.spawn("work", command="htop", runner=_runner(script), audit=rec.audit)
    assert r["status"] == "spawned" and r["session"] == "work" and r["pane_id"] == "%7"
    assert rec.rows[0]["outcome"] == "spawned" and "spawn work" in rec.rows[0]["text"]


def test_spawn_accepts_a_validated_cwd_and_passes_it_to_tmux(tmp_path) -> None:
    rec = _Rec()
    seen: list[list[str]] = []

    def script(argv):
        seen.append(argv)
        if argv[:2] == ["tmux", "new-session"]:
            from tests.unit._spawn_env import consume

            consume(argv)
            return ("", 0, "")
        if argv[:2] == ["tmux", "list-panes"]:
            return ("%8\n", 0, "")
        return ("", 0, "")

    result = coder_factory.spawn(
        "work-cwd", cwd=str(tmp_path), runner=_runner(script), audit=rec.audit
    )
    assert result["status"] == "spawned"
    assert result["cwd"] == str(tmp_path.resolve())
    assert ["-c", str(tmp_path.resolve())] == seen[0][3:5]


def test_spawn_refuses_a_missing_cwd_before_tmux() -> None:
    rec = _Rec()
    calls: list[list[str]] = []
    result = coder_factory.spawn(
        "work-cwd", cwd="/definitely/not/a/holdspeak-directory",
        runner=_runner(lambda argv: (calls.append(argv), ("", 0, ""))[1]),
        audit=rec.audit,
    )
    assert result["status"] == "cwd_invalid"
    assert calls == []


def test_factory_route_forwards_cwd_to_the_audited_spawn(monkeypatch, tmp_path) -> None:
    seen: dict[str, object] = {}

    def fake_spawn(name, *, command=None, cwd=None, **kwargs):
        seen.update({"name": name, "command": command, "cwd": cwd})
        return {"status": "spawned", "session": name, "pane_id": "%9", "cwd": cwd}

    monkeypatch.setattr(coder_factory, "spawn", fake_spawn)
    app = FastAPI()
    router = APIRouter()
    register_factory_routes(router)
    app.include_router(router)
    response = TestClient(app).post(
        "/api/coders/factory/spawn",
        json={"name": "work-cwd", "cwd": str(tmp_path)},
    )
    assert response.status_code == 200
    assert seen == {"name": "work-cwd", "command": None, "cwd": str(tmp_path)}


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
