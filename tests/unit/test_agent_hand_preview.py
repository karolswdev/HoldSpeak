"""Conductor F1: the launch sheet's preview (``POST /api/agent/hand/preview``).

The preview composes the SAME brief the hand composes and resolves the same
repository and branch, and writes nothing: no worktree, no gate file, no
registration, no launch, no tmux call. A thing that would refuse the launch
is named in ``refused``; an item the brief cannot carry refuses by name.
Real git and the real hand rig (``test_agent_hand._rig``); tmux is faked.
"""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery import DeliveryRegistry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_brief import compose_agent_brief
from holdspeak.services.agent_hand_preview import LaunchReads
from holdspeak.services.agent_hand_preview import preview_hand as _preview_hand
from holdspeak.services.agent_hand_service import AgentHandRefused
from holdspeak.services.errors import ServiceError
from holdspeak.services.onboarding_service import _version_of
from holdspeak.web.routes.agent_hand import build_agent_hand_router
from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, db  # noqa: F401  (the fixture)
from tests.unit.test_factory_launch import _make_repo

import pytest


def _reads(rig, which=None) -> LaunchReads:
    """The rig's driver files, read only (the preview never calls the driver getter)."""
    tmp = rig.repo.parent
    return LaunchReads(
        profiles_path=tmp / "profiles.json", registry_path=tmp / "sources.json",
        ledger_path=tmp / "launches.json", which=which or (lambda name: f"/bin/{name}"),
        runner=rig.tmux,
    )


_RIGS: dict = {}


def preview_hand(service, principal, kind, item_id, **kw):
    """The preview over the rig whose hand service this is."""
    rig = _RIGS.get(id(service))
    if rig is not None and "reads" not in kw:
        kw["reads"] = _reads(rig, getattr(rig, "which", None))
    return _preview_hand(service, principal, kind, item_id, **kw)


def _track(rig, which=None):
    rig.which = which
    _RIGS[id(rig.hand)] = rig
    return rig


def test_preview_is_the_hands_brief_and_writes_nothing(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _track(_rig(tmp_path, db, monkeypatch))
    sources_before = [s.source_id for s in rig.registry.sources()]
    result = preview_hand(rig.hand, OWNER, "action", "ai_1")

    brief = compose_agent_brief(db, "action:ai_1", project_id=PROJECT, control_mode="yolo", repo_path=str(rig.repo))
    assert result["text"] == brief["text"] and result["bytes"] == brief["bytes"]
    assert result["refs"] == brief["refs"] and "action:ai_1" in result["refs"]
    assert result["repo"] == str(rig.repo)
    assert result["branch"] == "hs/action-ai_1" and result["worktree"] == "hs-action-ai_1"
    assert result["control_mode"] == "yolo" and result["profile"] == "claude-default"
    assert result["refused"] == []
    assert len(result["acceptance"]) == 7
    kinds = [s["kind"] for s in result["sources"]]
    assert kinds[0] == "action" and result["sources"][0]["title"] == "Fix the login timeout"
    assert "meeting" in kinds
    # No side effect: no worktree, no gate, no tmux, no new source, no launch.
    assert not (rig.repo.parent / "hs-action-ai_1").exists()
    assert not rig.gate_path.exists()
    assert rig.tmux.calls == []
    assert [s.source_id for s in rig.registry.sources()] == sources_before
    assert rig.launches.list() == []


def test_preview_names_what_would_refuse_the_launch(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    which = lambda name: None if name == "codex" else f"/bin/{name}"  # noqa: E731
    rig = _track(_rig(tmp_path, db, monkeypatch, which=which), which)
    result = preview_hand(rig.hand, OWNER, "action", "ai_1", profile="codex-default")
    assert result["refused"] == ["executable_absent"]
    assert result["profile"] == "codex-default"
    assert result["text"]  # the brief still shows

    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Unrelated' WHERE id=?", (PROJECT,))
    result = preview_hand(rig.hand, OWNER, "action", "ai_1")
    assert result["repo"] is None and result["refused"] == ["no_repository"]

    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Railsproj' WHERE id=?", (PROJECT,))
    (rig.repo.parent / "hs-action-ai_1").mkdir()
    assert preview_hand(rig.hand, OWNER, "action", "ai_1")["refused"] == ["worktree_duplicate"]


def test_preview_refuses_an_item_by_name_and_an_agent_principal(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _track(_rig(tmp_path, db, monkeypatch))
    with pytest.raises(AgentHandRefused) as exc:
        preview_hand(rig.hand, OWNER, "action", "nope")
    assert exc.value.reason == "item_unknown"
    with pytest.raises(AgentHandRefused) as exc:
        preview_hand(rig.hand, OWNER, "issue", "418")
    assert exc.value.reason == "item_kind_unsupported"
    with pytest.raises(ServiceError) as exc:
        preview_hand(rig.hand, Principal(PrincipalKind.AGENT, "agent:tmux:x"), "action", "ai_1")
    assert exc.value.code == "owner_required"


def test_preview_does_not_register_a_project_map_clone(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _track(_rig(tmp_path, db, monkeypatch))
    clone = _make_repo(tmp_path / "mapped")
    rig.hand._project_map = {"projects": {"railsproj": str(clone)}}
    reads = _reads(rig)
    reads.registry_path = tmp_path / "empty-sources.json"  # absent: no source registered yet
    result = preview_hand(rig.hand, OWNER, "action", "ai_1", reads=reads)
    assert result["repo"] == str(clone) and result["refused"] == []
    assert not reads.registry_path.exists()


def test_route_previews_and_refuses_by_name(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _track(_rig(tmp_path, db, monkeypatch))
    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace(
        agent_hand_service=rig.hand, delivery_service=None, agent_hand_reads=_reads(rig))))
    client = TestClient(app)
    ok = client.post("/api/agent/hand/preview", json={"kind": "action", "id": "ai_1"})
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert set(body) >= {"text", "refs", "bytes", "people_cut", "acceptance", "repo", "branch", "sources", "refused"}
    missing = client.post("/api/agent/hand/preview", json={"kind": "action", "id": "nope"})
    assert missing.status_code == 404 and missing.json()["error"] == "item_unknown"
    assert client.post("/api/agent/hand/preview", json={"kind": "action"}).status_code == 400
    assert rig.tmux.calls == [] and rig.launches.list() == []


def test_version_reads_the_install_path_and_never_runs_a_process(tmp_path) -> None:
    cellar = tmp_path / "Cellar/tmux/3.5a/bin"
    cellar.mkdir(parents=True)
    (cellar / "tmux").write_text("")
    assert _version_of(str(cellar / "tmux")) == "3.5a"
    native = tmp_path / ".local/share/claude/versions"
    native.mkdir(parents=True)
    (native / "2.1.4").write_text("")
    assert _version_of(str(native / "2.1.4")) == "2.1.4"
    # An npm install under nvm: the package's version, not node's (v20.1.0).
    pkg = tmp_path / "nvm/v20.1.0/lib/node_modules/@openai/codex"
    (pkg / "bin").mkdir(parents=True)
    (pkg / "package.json").write_text('{"version": "0.46.0"}')
    (pkg / "bin/codex.js").write_text("")
    assert _version_of(str(pkg / "bin/codex.js")) == "0.46.0"
    assert _version_of(str(tmp_path / "opt/bin/claude")) is None
    assert _version_of(None) is None


def test_a_repository_registered_after_the_driver_loaded_is_seen(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """The launch driver is shared for the process; the Delivery drawer registers
    through its own registry instance. The preview and the hand read the file again."""
    rig = _track(_rig(tmp_path, db, monkeypatch))
    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Payments' WHERE id=?", (PROJECT,))
    assert preview_hand(rig.hand, OWNER, "action", "ai_1")["refused"] == ["no_repository"]
    other = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    clone = _make_repo(tmp_path / "later")
    other.register(str(clone), label="Payments")
    result = preview_hand(rig.hand, OWNER, "action", "ai_1")
    assert result["repo"] == str(clone) and result["refused"] == []


def test_repo_label_shows_the_home_folder_as_tilde(tmp_path, monkeypatch) -> None:
    from holdspeak.services.agent_hand_preview import _home_as_tilde

    real = tmp_path / "real"
    (real / "dev/payments-ledger").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    monkeypatch.setenv("HOME", str(link))
    assert _home_as_tilde(str(link / "dev/payments-ledger")) == "~/dev/payments-ledger"
    assert _home_as_tilde(str(real / "dev/payments-ledger")) == "~/dev/payments-ledger"
    assert _home_as_tilde("/srv/repo") == "/srv/repo"
    assert _home_as_tilde(None) is None



# ── Astra round 1 on #905: the preview is the launch it shows, and it has no side effect ──


def test_cold_preview_writes_no_files(db) -> None:  # noqa: F811
    """A cold hub: no profiles, registry, ledger, config or default database
    file appears, and the launch driver getter is never called."""
    from pathlib import Path

    from holdspeak.services.agent_hand_service import default_agent_hand_service

    service = default_agent_hand_service(db)

    def no_driver():
        raise AssertionError("the preview called the launch driver getter")

    service._launch_service = no_driver
    home = Path.home()
    before = {str(p.relative_to(home)) for p in home.rglob("*") if p.is_file()}
    preview_hand(service, OWNER, "action", "ai_1")
    after = {str(p.relative_to(home)) for p in home.rglob("*") if p.is_file()}
    assert after == before, sorted(after - before)


def test_preview_does_not_reconcile_an_existing_launch(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """A held launch after a restart stays as it is: the preview binds nothing
    and reconciles nothing (it was pending -> interrupted)."""
    from holdspeak.delivery.factory_launch import _DEFAULT_SERVICES
    from holdspeak.services.agent_hand_service import default_agent_hand_service
    from tests.unit.test_agent_hand_round1 import _restart

    rig = _track(_rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False))
    first = rig.hand.hand(OWNER, "action", "ai_1")
    restarted = _restart(rig, bind=False)
    rig.tmux.ended = True
    monkeypatch.setitem(_DEFAULT_SERVICES, id(db), restarted)
    monkeypatch.setattr("holdspeak.kernel.runtime._service", lambda: rig.broker)
    service = default_agent_hand_service(db)
    before = restarted.launch_record(first["launch_id"])["instruction_state"]
    try:
        _preview_hand(service, OWNER, "action", "ai_1", reads=_reads(rig))
        assert restarted.launch_record(first["launch_id"])["instruction_state"] == before
    finally:
        restarted.first_message.close()


def test_preview_emits_no_change(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    from holdspeak.runtime import composition
    from holdspeak.web.announce import install

    rig = _track(_rig(tmp_path, db, monkeypatch))
    seen: list = []
    monkeypatch.setattr(composition, "_installed", SimpleNamespace(_send_desk_changed=lambda changes: seen.extend(changes)))
    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace(
        agent_hand_service=rig.hand, delivery_service=None, agent_hand_reads=_reads(rig))))
    install(app)
    response = TestClient(app).post("/api/agent/hand/preview", json={"kind": "action", "id": "ai_1"})
    assert response.status_code == 200
    assert seen == [], seen


def test_preview_shows_the_held_launch_that_would_resume(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """A held Claude launch: previewing Codex names the held agent and refuses by
    name; the hand refuses the other agent too, and resumes the held one."""
    rig = _track(_rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False))
    first = rig.hand.hand(OWNER, "action", "ai_1", profile="claude-default", instruction="Original instruction")
    try:
        shown = preview_hand(rig.hand, OWNER, "action", "ai_1", profile="codex-default", instruction="Changed")
        actual = rig.launches.get(first["launch_id"])
        assert shown["profile"] == actual["profile_id"] == "claude-default"
        assert shown["requested_profile"] == "codex-default"
        assert shown["resume"]["launch_id"] == first["launch_id"]
        assert shown["resume"]["instruction_state"] == actual["instruction_state"]
        assert shown["refused"] == ["launch_profile_mismatch"]
        assert "Original instruction" in shown["text"]  # the held brief, not a new one
        with pytest.raises(AgentHandRefused) as exc:
            rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
        assert exc.value.reason == "launch_profile_mismatch"

        same = preview_hand(rig.hand, OWNER, "action", "ai_1", profile="claude-default")
        assert same["refused"] == [] and same["profile"] == "claude-default" and same["resume"]
        again = rig.hand.hand(OWNER, "action", "ai_1", profile="claude-default")
        assert again["resumed"] and again["launch_id"] == first["launch_id"]
        assert again["profile"] == "claude-default"
    finally:
        rig.tmux.ended = True
        rig.service.first_message.close()


def test_preview_names_the_launch_cap(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _track(_rig(tmp_path, db, monkeypatch))
    rig.hand._max_live = 0
    assert preview_hand(rig.hand, OWNER, "action", "ai_1")["refused"] == ["launch_cap_reached"]


def test_route_reads_one_launch_delivery_without_the_driver(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """The sheet's receipt follows the launch until its brief is sent, held or
    refused: GET /api/agent/launches/{id} reads the ledger, path-free."""
    rig = _track(_rig(tmp_path, db, monkeypatch, register_when=lambda tmux: False))
    first = rig.hand.hand(OWNER, "action", "ai_1")

    def no_driver():
        raise AssertionError("the launch read called the launch driver getter")

    try:
        app = FastAPI()
        hand = rig.hand
        hand_getter = hand._launch_service
        hand._launch_service = no_driver
        app.include_router(build_agent_hand_router(SimpleNamespace(
            agent_hand_service=hand, delivery_service=None, agent_hand_reads=_reads(rig))))
        client = TestClient(app)
        body = client.get(f"/api/agent/launches/{first['launch_id']}").json()
        assert body["launch_id"] == first["launch_id"]
        assert body["instruction_state"] == "pending" and body["profile"] == "claude-default"
        assert not any("/" in str(v) for v in body.values() if isinstance(v, str))
        assert client.get("/api/agent/launches/nope").status_code == 404
        hand._launch_service = hand_getter
    finally:
        rig.tmux.ended = True
        rig.service.first_message.close()
