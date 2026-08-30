"""HS-152-03 -- The People fence (sensitive results, multi-pass redaction).

Drives the REAL RoutedInferenceCoordinator / InferenceRunner /
``_attempt_stream`` path with a fake engine injected via
``_engine_factory`` (the HS-151-04 law: fake-adoption tests hid three
real-path defects), the REAL ``ThreadToolExecutor`` and the REAL
``holdspeak.mcp.tools.dispatch`` -- ``people.readiness`` is a genuine
People-family call, not a stub.

Pins (story acceptance):

1. A ``people.*`` result on a local turn, then ``profile_override`` ->
   cloud: the payload the engine receives carries
   ``[people content withheld]`` and no sentinel; the part row has
   ``sensitive=1``.
2. Within one multi-pass turn on a cloud profile, pass 2's payload
   already withholds pass 1's People result.
3. A non-People tool result passes verbatim on cloud.

Scoped: this file + test_thread_tool_loop.py + test_thread_service.py.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import ThreadService, _PEOPLE_REDACTION

OWNER = Principal(PrincipalKind.OWNER, "owner-session")

# ``people.readiness`` on a fresh HOME answers with a content-free view --
# but content-free to the OWNER is still People-family output, and the fence
# is about the family, not the bytes.  The readiness JSON is the sentinel.
PEOPLE_TOOL = "people.readiness"
PLAIN_TOOL = "desk.list"


class _ToolThenTextEngine:
    """Fake engine: asks for one tool call unless the transcript already
    holds a tool message, then answers in text.  Captures every ``messages``
    list it is handed (the post-redactor payload)."""

    active_provider = "fake-fence"
    active_model = "fence-model"

    def __init__(self, tool_name: str, tool_args: dict[str, Any] | None = None) -> None:
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.calls: list[list[dict[str, Any]]] = []
        self.tools_seen: list[Any] = []
        self.always_answer = False

    def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, tools=None, **kw):
        msgs = [dict(m) for m in (messages or [])]
        self.calls.append(msgs)
        self.tools_seen.append(tools)
        has_tool_msg = any(m.get("role") == "tool" for m in msgs)
        if has_tool_msg or self.always_answer:
            for w in ("All", "done."):
                yield Delta(kind="text", text=w + " ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [{
                "id": "call_fence_1",
                "name": self.tool_name,
                "arguments": json.dumps(self.tool_args),
            }]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, *, messages=None, **kw):
        return "All done. "

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        return "All done. "


@pytest.fixture
def rig():
    """Isolated HOME + real hub + real kernel broker; yields (db, broker, server)."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix="hs152-fence-"))
    old_home = os.environ.get("HOME", "")
    os.environ["HOME"] = str(home)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
    )
    server.start()
    db = get_database()
    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    try:
        yield db, broker
    finally:
        server.stop()
        os.environ["HOME"] = old_home
        reset_database()


def _seed_profile(db: Any, profile_id: str, *, boundary: str) -> str:
    """A chat.turn-capable profile; returns the assignment-entry profile id.

    ``same_device`` = a v2 model profile (the local fixture).  Anything else
    = a legacy ``profiles`` row with a public base URL -- exactly how a
    hosted / OpenAI-compatible model routes in production (the route
    planner adapts it to a ``legacy-<id>`` leg whose boundary is derived
    from the endpoint, ``external_service`` -> ``cloud``).
    """
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    if boundary == "same_device":
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        return profile_id
    db.profiles.upsert(
        profile_id=profile_id,
        name="Fence cloud capture",
        kind="openAICompatible",
        base_url="https://cloud.example.test/v1",
        model="capture-model",
        context_limit=32768,
        requires_key=False,
    )
    return "legacy-" + profile_id


def _assign(db: Any, entry_id: str, command_id: str, expected_revision: int = 0) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": command_id,
        "expected_revision": expected_revision,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": entry_id, "profile_revision": 1}],
    })


def _service(db: Any, broker: Any, broadcasts: list) -> ThreadService:
    from holdspeak.mcp.tools import dispatch as mcp_dispatch

    return ThreadService(
        db,
        broadcast=lambda t, d: broadcasts.append((t, d)),
        broker=broker,
        tool_dispatch_fn=mcp_dispatch,
        control_mode_fn=lambda: "yolo",
    )


def _run_turn(svc: ThreadService, db: Any, tid: str, text: str, timeout: float = 20.0) -> str:
    result = asyncio.run(svc.start_turn(OWNER, tid, text))
    aid = result["assistant_message_id"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        msg = db.threads.get_message(aid)
        if msg and not msg.streaming:
            return aid
        time.sleep(0.1)
    pytest.fail("turn did not complete")


def _tool_part_rows(db: Any, tid: str) -> list[Any]:
    rows = []
    for m in db.threads.list_path(tid):
        if m.role == "tool":
            rows.extend(db.threads.get_parts(m.id))
    return rows


def _flat(messages: list[dict[str, Any]]) -> str:
    """The message contents as the engine sees them (no JSON re-escaping)."""
    return "\n---\n".join(str(m.get("content", "")) for m in messages)


def test_people_result_local_then_cloud_turn_withheld(rig) -> None:
    """AC1: local turn calls people.*; the next turn on a cloud profile
    receives the withheld marker, never the People bytes; part row sensitive=1."""
    db, broker = rig
    local_id = _seed_profile(db, "fence-local", boundary="same_device")
    _seed_profile(db, "fence-cloud", boundary="external_service")
    _assign(db, local_id, "fence-assign-1")

    engine = _ToolThenTextEngine(PEOPLE_TOOL)
    broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    broadcasts: list = []
    svc = _service(db, broker, broadcasts)
    tid = svc.create(title="Fence")["id"]

    # -- Turn 1: local. Pass 1 asks for people.readiness; pass 2 answers. --
    _run_turn(svc, db, tid, "Is the People store ready?")
    assert len(engine.calls) == 2, f"expected 2 passes, got {len(engine.calls)}"
    assert engine.tools_seen[0], "tool palette must reach the engine"

    tool_parts = _tool_part_rows(db, tid)
    assert len(tool_parts) == 1
    people_text = tool_parts[0].text
    assert people_text and people_text.startswith("{"), people_text
    assert tool_parts[0].sensitive == 1, "people.* result row must be sensitive=1"

    result_frames = [d for t, d in broadcasts if t == "thread_tool_result"]
    assert result_frames and result_frames[0]["sensitive"] is True
    assert result_frames[0]["name"] == PEOPLE_TOOL

    # Local egress: pass 2 carried the People bytes verbatim (the fence is
    # about cloud, not about the owner's own machine).
    pass2 = _flat(engine.calls[1])
    assert people_text in pass2
    assert _PEOPLE_REDACTION not in pass2
    assert db.threads.get_message(_last_assistant(db, tid)).egress_scope == "local"

    # -- Turn 2: profile_override -> cloud. --
    svc.patch(tid, profile_override="fence-cloud")
    engine.always_answer = True
    aid2 = _run_turn(svc, db, tid, "And now, on the cloud?")
    assert db.threads.get_message(aid2).egress_scope == "cloud"

    cloud_payload = _flat(engine.calls[-1])
    assert _PEOPLE_REDACTION in cloud_payload, cloud_payload
    assert people_text not in cloud_payload, "People bytes leaked to cloud"
    assert "_sensitive_texts" not in json.dumps(engine.calls[-1])


def test_multipass_cloud_pass_two_withholds_pass_one(rig) -> None:
    """AC2: on a cloud profile from the start, pass 2's payload already
    withholds the People result pass 1 produced."""
    db, broker = rig
    cloud_id = _seed_profile(db, "fence-cloud", boundary="external_service")
    _assign(db, cloud_id, "fence-assign-2")

    engine = _ToolThenTextEngine(PEOPLE_TOOL)
    broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    broadcasts: list = []
    svc = _service(db, broker, broadcasts)
    tid = svc.create(title="Fence cloud")["id"]

    aid = _run_turn(svc, db, tid, "Is the People store ready?")
    assert len(engine.calls) == 2
    assert db.threads.get_message(aid).egress_scope == "cloud"

    people_text = _tool_part_rows(db, tid)[0].text
    assert people_text
    pass2 = engine.calls[1]
    tool_msgs = [m for m in pass2 if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["content"] == _PEOPLE_REDACTION
    assert people_text not in _flat(pass2)

    done = [d for t, d in broadcasts if t == "thread_turn_done"]
    assert done and done[-1]["outcome"] == "succeeded"


def test_non_people_result_verbatim_on_cloud(rig) -> None:
    """AC3: a non-People tool result crosses to the cloud verbatim."""
    db, broker = rig
    cloud_id = _seed_profile(db, "fence-cloud", boundary="external_service")
    _assign(db, cloud_id, "fence-assign-3")

    engine = _ToolThenTextEngine(PLAIN_TOOL, {"kind": "notes"})
    broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    broadcasts: list = []
    svc = _service(db, broker, broadcasts)
    tid = svc.create(title="Fence plain")["id"]

    _run_turn(svc, db, tid, "List my notes")
    assert len(engine.calls) == 2

    parts = _tool_part_rows(db, tid)
    assert len(parts) == 1 and parts[0].sensitive == 0
    plain_text = parts[0].text
    tool_msgs = [m for m in engine.calls[1] if m.get("role") == "tool"]
    assert tool_msgs and tool_msgs[0]["content"] == plain_text
    assert _PEOPLE_REDACTION not in _flat(engine.calls[1])

    frames = [d for t, d in broadcasts if t == "thread_tool_result"]
    assert frames and frames[0]["sensitive"] is False and frames[0]["outcome"] == "succeeded"


def _last_assistant(db: Any, tid: str) -> str:
    return [m for m in db.threads.list_path(tid) if m.role == "assistant"][-1].id
