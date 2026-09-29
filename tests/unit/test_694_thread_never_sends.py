"""#694 (Codex Astra counsel r1, P1): a model never presses Send for the owner.

A thread runs its tools with the owner's principal. With ``channel.send`` in
the thread tool table, a custom mode that names it let a model send a
prepared file as the owner with no Send press: in ``yolo`` (unset policy
admits) and under a remembered "allow" for the tool (in any control mode).
Through the real thread HTTP route, a real published update, a real saved
folder and a real prepared send: the model is not offered ``channel.send``,
and nothing is written. The model may still prepare (``channel.prepare``).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import _boot, destination, files, ops, prepare, room  # noqa: E402
from test_phase143_inference_assignments import OWNER, _profile, _result_claim  # noqa: E402


class _ModelThatSends:
    """A deterministic model: on its first pass, if it holds the tool, it calls it."""

    active_provider = "fixture"
    active_model = "fixture"

    def __init__(self, send_id: str = "", *, tool: str = "channel.send",
                 arguments: dict[str, Any] | None = None) -> None:
        self.tool = tool
        self.arguments = arguments if arguments is not None else {"send_id": send_id, "command_id": "model-send"}
        self.calls = 0
        self.palettes: list[list[str]] = []

    def run_prompt_stream(self, *, messages: Any = None, tools: Any = None, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        self.calls += 1
        palette = [t["function"]["name"] for t in tools or []]
        self.palettes.append(palette)
        if self.calls == 1 and self.tool in palette:
            yield Delta(kind="tool_calls", meta={"tool_calls": [{
                "id": "model-emitted-press", "name": self.tool,
                "arguments": json.dumps(self.arguments),
            }]})
        else:
            yield Delta(kind="text", text="Done.")
        yield Delta(kind="usage", meta={"prompt_tokens": 1, "completion_tokens": 1})
        yield Delta(kind="done")

    def run_prompt_messages(self, **_kw: Any) -> str:
        return "Done."

    def run_prompt(self, **_kw: Any) -> str:
        return "Done."


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.config as config_module
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    yield lambda: _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.mark.parametrize("posture", ["yolo", "remembered_allow"])
def test_a_model_is_never_offered_the_send_and_nothing_is_written(hub: Any, tmp_path: Path, posture: str) -> None:
    from holdspeak.config import Config
    from holdspeak.kernel.runtime import _service
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    cfg = Config.load()
    cfg.control_mode = "yolo" if posture == "yolo" else "safe"
    cfg.save()
    h = hub()
    _, update = room(h, body="The thread must not send this.")
    folder = tmp_path / "out"
    prepared = prepare(h, update, destination(h, folder))

    mode = h.client.post("/api/recipes", json={"name": "Send mode", "kind": "mode",
                                               "tools": ["channel.send", "channel.prepare"]})
    assert mode.status_code == 201, mode.text
    thread = h.client.post("/api/threads", json={"title": "Review", "recipe_id": mode.json()["recipe"]["id"]})
    assert thread.status_code == 201, thread.text
    tid = thread.json()["id"]
    if posture == "remembered_allow":
        h.db.threads.set_tool_policy(tid, "channel.send", "allow")

    _profile(h.db, "p694-local", claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(h.db).set_assignment(OWNER, {
        "command_id": "p694-assign", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "p694-local", "profile_revision": 1}],
    })
    model = _ModelThatSends(prepared["send"]["id"])
    _service().inference_runner._engine_factory = lambda _rev, **_kw: model

    turn = h.client.post(f"/api/threads/{tid}/turns", json={"text": "Review this update."})
    assert turn.status_code == 201, turn.text
    mid = turn.json()["assistant_message_id"]
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        msg = h.db.threads.get_message(mid)
        if msg is not None and not msg.streaming:
            break
        time.sleep(0.1)
    assert msg is not None and not msg.streaming, "the turn never finished"

    assert model.calls >= 1
    assert files(folder) == [], f"the model sent a file as the owner: {files(folder)}"
    assert ops(h, "channel.send") == [], ops(h, "channel.send")
    assert all("channel.send" not in palette for palette in model.palettes), model.palettes
    assert any("channel.prepare" in palette for palette in model.palettes), model.palettes


def _assign_model(h: Any, model: Any) -> None:
    from holdspeak.kernel.runtime import _service
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _profile(h.db, "p694-local", claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(h.db).set_assignment(OWNER, {
        "command_id": "p694-assign", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "p694-local", "profile_revision": 1}],
    })
    _service().inference_runner._engine_factory = lambda _rev, **_kw: model


def _run_turn(h: Any, tid: str) -> None:
    turn = h.client.post(f"/api/threads/{tid}/turns", json={"text": "Nudge the reviewer."})
    assert turn.status_code == 201, turn.text
    mid = turn.json()["assistant_message_id"]
    deadline = time.monotonic() + 45
    msg = None
    while time.monotonic() < deadline:
        msg = h.db.threads.get_message(mid)
        if msg is not None and not msg.streaming:
            break
        time.sleep(0.1)
    assert msg is not None and not msg.streaming, "the turn never finished"


def test_a_yolo_thread_cannot_post_a_nudge(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Muad'Dib's ruling on #694: nudge.send (a GitHub comment posted as the
    owner) is the owner's press. A yolo thread whose mode names it: the
    model is not offered it, no gh command runs, no nudge.send operation."""
    import subprocess

    from holdspeak.config import Config
    from test_philo5_the_loop_r2 import _nudge_step

    cfg = Config.load()
    cfg.control_mode = "yolo"
    cfg.save()
    h = hub()
    gh_calls: list[list[str]] = []

    def runner(argv: list[str], **_kwargs: Any) -> Any:
        gh_calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "https://github.com/example/payments/pull/7#c1\n", "")

    monkeypatch.setattr(h.root.project_steward_service, "_subprocess_runner", runner)
    step_id = _nudge_step(h)

    mode = h.client.post("/api/recipes", json={"name": "Nudge mode", "kind": "mode", "tools": ["nudge.send"]})
    assert mode.status_code == 201, mode.text
    thread = h.client.post("/api/threads", json={"title": "Nudge", "recipe_id": mode.json()["recipe"]["id"]})
    assert thread.status_code == 201, thread.text
    model = _ModelThatSends(tool="nudge.send", arguments={"step_id": step_id, "text": "Please review"})
    _assign_model(h, model)
    _run_turn(h, thread.json()["id"])

    assert model.calls >= 1
    assert gh_calls == [], f"the model posted a GitHub comment as the owner: {gh_calls}"
    assert ops(h, "nudge.send") == [], ops(h, "nudge.send")
    assert all("nudge.send" not in palette for palette in model.palettes), model.palettes


@pytest.mark.parametrize("tool", ["project.archive", "project.configure_steward"])
def test_a_yolo_thread_cannot_change_the_room_for_the_owner(hub: Any, tool: str) -> None:
    """Codex Astra counsel r2 on #694 (P1): the kernel makes these owner-only
    (kernel/project.OWNER_ONLY_OPERATIONS), yet a yolo thread archived a real
    project and enabled unattended steward work as the owner. The model is
    not offered the tool; the project and its policy do not change."""
    from holdspeak.config import Config

    cfg = Config.load()
    cfg.control_mode = "yolo"
    cfg.save()
    h = hub()
    pid, _update = room(h, body="The thread must not change this Room.")
    before_project = h.client.get(f"/api/projects/{pid}").json()
    before_policy = h.client.get(f"/api/projects/{pid}/steward/policy").json()
    arguments = {"project_id": pid} if tool == "project.archive" else {
        "project_id": pid, "enabled": True, "unattended_enabled": True, "eligible_effect_kinds": ["github_comment"]}

    mode = h.client.post("/api/recipes", json={"name": "Room mode", "kind": "mode", "tools": [tool]})
    assert mode.status_code == 201, mode.text
    thread = h.client.post("/api/threads", json={"title": "Room", "recipe_id": mode.json()["recipe"]["id"]})
    assert thread.status_code == 201, thread.text
    model = _ModelThatSends(tool=tool, arguments=arguments)
    _assign_model(h, model)
    _run_turn(h, thread.json()["id"])

    assert model.calls >= 1
    after_project = h.client.get(f"/api/projects/{pid}").json()
    after_policy = h.client.get(f"/api/projects/{pid}/steward/policy").json()
    assert after_project.get("is_archived") is False and after_project == before_project, \
        f"the model changed the project as the owner: {after_project}"
    assert after_policy == before_policy, f"the model changed the steward policy as the owner: {after_policy}"
    assert ops(h, tool) == [], ops(h, tool)
    assert all(tool not in palette for palette in model.palettes), model.palettes


def _counts(h: Any) -> dict[str, int]:
    with h.db._connection() as conn:
        names = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {n: conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in names}


def _heads(h: Any) -> list[dict[str, Any]]:
    with h.db._connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM inference_assignment_heads ORDER BY rowid")]


_CONFIG_ARGS: dict[str, dict[str, Any]] = {
    "model_library.define_endpoint": {"draft": {
        "request_id": "p694-endpoint", "profile_id": "p694-endpoint", "expected_profile_revision": 0,
        "label": "Model endpoint", "provider_family": "private_endpoint", "model": "fixture-model",
        "endpoint": "http://127.0.0.1:9/v1", "requires_key": False}, "secret": None},
    "inference_assignment.set": {"command_id": "p694-set", "expected_revision": 1,
                                 "scope": {"kind": "capability", "capability_id": "chat.turn"},
                                 "entries": [{"profile_id": "p694-local", "profile_revision": 1}]},
    "inference_assignment.clear": {"command_id": "p694-clear", "expected_revision": 1,
                                   "scope": {"kind": "capability", "capability_id": "chat.turn"},
                                   "capability_id": "chat.turn"},
    "thought.replace_default_context": {"request_id": "p694-default-context", "expected_revision": 0, "refs": []},
}


@pytest.mark.parametrize("tool", sorted(_CONFIG_ARGS))
def test_a_yolo_thread_cannot_change_the_system(hub: Any, monkeypatch: pytest.MonkeyPatch, tool: str) -> None:
    """Codex Astra counsel r3 on #694 and the owner's ruling (2026-09-29):
    CONFIG -- models, endpoints, assignments, setup, the default context --
    is never a thread's without his press. A yolo thread whose mode names the
    tool: it is not offered, and no product table changes (the thread's own
    rows and the turn's kernel and inference records aside)."""
    from holdspeak.config import Config

    cfg = Config.load()
    cfg.control_mode = "yolo"
    cfg.save()
    h = hub()
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models",
                        lambda *a, **k: {"ok": True, "models": ["fixture-model"]})
    mode = h.client.post("/api/recipes", json={"name": "Config mode", "kind": "mode", "tools": [tool]})
    assert mode.status_code == 201, mode.text
    thread = h.client.post("/api/threads", json={"title": "Config", "recipe_id": mode.json()["recipe"]["id"]})
    assert thread.status_code == 201, thread.text
    model = _ModelThatSends(tool=tool, arguments=_CONFIG_ARGS[tool])
    _assign_model(h, model)
    before, heads = _counts(h), _heads(h)
    _run_turn(h, thread.json()["id"])
    after = _counts(h)

    assert model.calls >= 1
    # The turn itself writes its thread rows, its kernel operations and its
    # model call's inference records; a model ASSIGNMENT is not one of them.
    def turn_row(table: str) -> bool:
        if table.startswith("inference_assignment"):
            return False
        return table.startswith(("thread", "kernel_", "inference_", "pipeline_", "sqlite_sequence"))

    changed = {k: (before.get(k), v) for k, v in after.items() if before.get(k) != v and not turn_row(k)}
    assert changed == {}, f"the model changed the system as the owner: {changed}"
    assert _heads(h) == heads, "the model changed a model assignment as the owner"
    assert ops(h, tool) == [], ops(h, tool)
    assert all(tool not in palette for palette in model.palettes), model.palettes


def test_a_yolo_thread_drafts_a_setup_but_never_commits_it(hub: Any) -> None:
    """Muad'Dib's ruling on #694 (Send's prepare-then-press for setup): a
    thread may DRAFT a setup (project.setup.start writes only its session);
    project.setup.finalize commits it into the system and is never offered."""
    from holdspeak.config import Config
    from holdspeak.mcp.tools import dispatch

    cfg = Config.load()
    cfg.control_mode = "yolo"
    cfg.save()
    h = hub()
    mode = h.client.post("/api/recipes", json={"name": "Setup mode", "kind": "mode",
                                               "tools": ["project.setup.start", "project.setup.finalize"]})
    assert mode.status_code == 201, mode.text

    # The draft: the model starts a setup session.
    drafting = h.client.post("/api/threads", json={"title": "Draft", "recipe_id": mode.json()["recipe"]["id"]})
    model = _ModelThatSends(tool="project.setup.start", arguments={})
    _assign_model(h, model)
    before = _counts(h)
    _run_turn(h, drafting.json()["id"])
    assert any("project.setup.start" in palette for palette in model.palettes), model.palettes
    assert _counts(h)["project_setup_sessions"] == before["project_setup_sessions"] + 1, "the draft did not happen"

    # The commit: an owner-started session the model tries to finalize.
    session = dispatch("project.setup.start", {}, OWNER)
    committing = h.client.post("/api/threads", json={"title": "Commit", "recipe_id": mode.json()["recipe"]["id"]})
    model = _ModelThatSends(tool="project.setup.finalize", arguments={"session_id": session["id"]})
    from holdspeak.kernel.runtime import _service

    _service().inference_runner._engine_factory = lambda _rev, **_kw: model
    projects = h.client.get("/api/projects").json()["projects"]
    _run_turn(h, committing.json()["id"])
    assert all("project.setup.finalize" not in palette for palette in model.palettes), model.palettes
    assert h.client.get("/api/projects").json()["projects"] == projects, "the model committed a setup as the owner"
    assert ops(h, "project.setup.finalize") == []
