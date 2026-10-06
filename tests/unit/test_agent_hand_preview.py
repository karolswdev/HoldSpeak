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
from holdspeak.services.agent_hand_preview import preview_hand
from holdspeak.services.agent_hand_service import AgentHandRefused
from holdspeak.services.errors import ServiceError
from holdspeak.services.onboarding_service import _version_of
from holdspeak.web.routes.agent_hand import build_agent_hand_router
from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, db  # noqa: F401  (the fixture)
from tests.unit.test_factory_launch import _make_repo

import pytest


def test_preview_is_the_hands_brief_and_writes_nothing(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    sources_before = [s.source_id for s in rig.registry.sources()]
    result = preview_hand(rig.hand, OWNER, "action", "ai_1")

    brief = compose_agent_brief(db, "action:ai_1", project_id=PROJECT, control_mode="yolo", repo_path=str(rig.repo))
    assert result["text"] == brief["text"] and result["bytes"] == brief["bytes"]
    assert result["refs"] == brief["refs"] and "action:ai_1" in result["refs"]
    assert result["repo"] == str(rig.repo)
    assert result["branch"] == "hs/action-ai_1" and result["worktree"] == "hs-action-ai_1"
    assert result["control_mode"] == "yolo" and result["profile"] == "claude-default"
    assert result["refused"] == []
    assert len(result["acceptance"]) == 6
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
    rig = _rig(tmp_path, db, monkeypatch, which=lambda name: None if name == "codex" else f"/bin/{name}")
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
    rig = _rig(tmp_path, db, monkeypatch)
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
    rig = _rig(tmp_path, db, monkeypatch)
    clone = _make_repo(tmp_path / "mapped")
    empty = DeliveryRegistry(tmp_path / "empty-sources.json", map_path=tmp_path / "absent.json")
    rig.service._registry = empty
    rig.hand._project_map = {"projects": {"railsproj": str(clone)}}
    result = preview_hand(rig.hand, OWNER, "action", "ai_1")
    assert result["repo"] == str(clone) and result["refused"] == []
    assert empty.sources() == []


def test_route_previews_and_refuses_by_name(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace(agent_hand_service=rig.hand, delivery_service=None)))
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
    rig = _rig(tmp_path, db, monkeypatch)
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
