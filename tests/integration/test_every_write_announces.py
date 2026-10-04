"""Every write announces itself: one ``desk_changed`` frame on ``/ws``.

Proved on a real hub (inventory C, section 2.2, 2026-10-03): seven writes sent
no bus frame, so a second window stayed stale until a reload -- action item
done, action item edit, meeting rename, project create, resource add, meeting
attach, Brief generate, thread create.

The cause was structural: a write announced only when its service was built
with ``on_changed``. The repair is two roots, and this file fences both:

1. ``OperationRegistry.invoke`` announces every operation whose descriptor
   says ``effect="write"`` (``holdspeak/operations.py``).
2. One HTTP middleware announces every mutating ``/api`` request that answers
   2xx (``holdspeak/web/announce.py``) -- the routes that do not go through
   the registry.

Everything here runs against a real hub (``MeetingWebServer.start()``, a real
port, a real ``/ws`` client). The walk in ``test_no_registered_write_is_silent``
swaps each operation's SERVICE METHOD for a stand-in that returns at once: it
proves the registry's root (validation, the kernel path for admitted
operations, the bus, the socket), not the 68 services. The eight named writes
run their real services over HTTP.
"""
from __future__ import annotations

import dataclasses
import json
import threading
import time
import urllib.request
from typing import Any, Callable, Iterator

import pytest

pytest.importorskip("fastapi", reason="requires meeting/web dependencies")
pytest.importorskip("websockets", reason="needs a websocket client")

pytestmark = [pytest.mark.requires_meeting]

TOKEN = "every-write-announces-owner-token"


class Hub:
    """A started hub, its ``/ws`` listener and an HTTP caller."""

    def __init__(self) -> None:
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        self.server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_a, **_k: None,
                on_stop=lambda *_a, **_k: None,
                get_state=lambda: {"activity": {"state": "idle", "source": "runtime"}},
            ),
            host="127.0.0.1",
            auth_token=TOKEN,
        )
        self.url = self.server.start().rstrip("/")
        from holdspeak.runtime import composition

        self.root = composition.installed()
        self.frames: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._listener = threading.Thread(target=self._listen, daemon=True)
        self._listener.start()
        assert self._ready.wait(10), "the /ws listener did not connect"

    def _listen(self) -> None:
        from websockets.sync.client import connect

        ws_url = self.url.replace("http://", "ws://") + "/ws"
        with connect(
            ws_url,
            subprotocols=["holdspeak.v1"],
            additional_headers={"Authorization": f"Bearer {TOKEN}"},
        ) as socket:
            self._ready.set()
            while not self._stop.is_set():
                try:
                    raw = socket.recv(timeout=0.1)
                except TimeoutError:
                    continue
                except Exception:
                    return
                try:
                    frame = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                if isinstance(frame, dict) and frame.get("type") == "desk_changed":
                    with self._lock:
                        self.frames.append(frame.get("data") or {})

    def call(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            self.url + path, data=data, method=method,
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read()
        try:
            return status, json.loads(raw or b"null")
        except ValueError:
            return status, raw

    def frames_from(self, write: Callable[[], Any], wait_s: float = 2.0) -> list[dict[str, Any]]:
        """Run *write*; the ``desk_changed`` frames the listener got for it."""
        time.sleep(0.15)  # frames of the write before this one have landed
        with self._lock:
            self.frames.clear()
        write()
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            with self._lock:
                if self.frames:
                    break
            time.sleep(0.02)
        time.sleep(0.15)  # a second frame for the same write would land here
        with self._lock:
            return list(self.frames)

    def stop(self) -> None:
        self._stop.set()
        self._listener.join(timeout=5)
        self.server.stop()


@pytest.fixture(scope="module")
def hub() -> Iterator[Hub]:
    from holdspeak.db import reset_database

    reset_database()
    started = Hub()
    try:
        yield started
    finally:
        started.stop()
        reset_database()


@pytest.fixture(autouse=True)
def _the_hub_is_the_runtime(hub: Hub) -> None:
    """``tests/conftest.py`` installs a bare root for each test; put the hub's back."""
    from holdspeak.runtime import composition

    composition.install(hub.root)


@pytest.fixture(scope="module")
def seeded(hub: Hub) -> dict[str, str]:
    """One meeting with one action item, and one project, made the real way."""
    from datetime import datetime

    from holdspeak.db import get_database
    from holdspeak.intel import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    get_database().meetings.save_meeting(
        MeetingState(
            id="m-announce",
            started_at=datetime(2026, 10, 1, 10, 0, 0),
            title="Announce fence",
            segments=[TranscriptSegment(text="Send the plan", speaker="Me", start_time=0.0, end_time=5.0)],
            intel=IntelSnapshot(timestamp=0.0, action_items=[
                ActionItem(task="Send the plan", owner="Me", id="ai-announce"),
            ]),
        )
    )
    from holdspeak.runtime import composition

    composition.install(hub.root)
    status, body = hub.call("POST", "/api/projects", {"name": "Announce fence room"})
    assert status == 200, body
    return {"meeting": "m-announce", "item": "ai-announce", "project": body["project"]["id"]}


#: The writes the inventory proved silent, by the name the owner knows them by.
NAMED_WRITES: dict[str, Callable[[Hub, dict[str, str]], tuple[int, Any]]] = {
    "action item done": lambda hub, ids: hub.call(
        "PATCH", f"/api/all-action-items/{ids['item']}", {"status": "done"}),
    "action item edit": lambda hub, ids: hub.call(
        "PATCH", f"/api/all-action-items/{ids['item']}/edit", {"task": "Send the plan today"}),
    "meeting rename": lambda hub, ids: hub.call(
        "PUT", f"/api/meetings/{ids['meeting']}", {"title": "Announce fence, renamed"}),
    "project create": lambda hub, ids: hub.call(
        "POST", "/api/projects", {"name": "A second room"}),
    "resource add": lambda hub, ids: hub.call(
        "PUT", f"/api/projects/{ids['project']}/resources/meeting:{ids['meeting']}", {}),
    "meeting attach": lambda hub, ids: hub.call(
        "POST", f"/api/projects/{ids['project']}/meetings/{ids['meeting']}"),
    "Brief generate": lambda hub, ids: hub.call("POST", "/api/brief/generate", {}),
    "thread create": lambda hub, ids: hub.call("POST", "/api/threads", {"title": "Announce fence"}),
}


def test_the_named_writes_each_send_a_frame(hub: Hub, seeded: dict[str, str]) -> None:
    silent: list[str] = []
    for label, write in NAMED_WRITES.items():
        answer: list[tuple[int, Any]] = []
        frames = hub.frames_from(lambda: answer.append(write(hub, seeded)))
        status, body = answer[0]
        assert 200 <= status < 300, f"{label}: the write itself failed ({status}): {body!r}"
        if not frames:
            silent.append(label)
    assert not silent, f"these writes sent no desk_changed frame: {silent}"


def test_a_write_sends_one_frame_not_two(hub: Hub, seeded: dict[str, str]) -> None:
    """A note announces from its service; the roots add no second frame."""
    frames = hub.frames_from(lambda: hub.call("POST", "/api/notes", {"title": "One frame", "body_markdown": "x"}))
    assert len(frames) == 1, frames
    assert frames[0]["kind"] == "note" and frames[0]["op"] == "create"
    frames = hub.frames_from(lambda: hub.call("POST", "/api/projects", {"name": "One frame room"}))
    assert len(frames) == 1, frames
    assert frames[0]["kind"] == "project" and frames[0]["op"] == "create" and frames[0]["id"]


def test_a_read_and_a_refused_write_send_no_frame(hub: Hub, seeded: dict[str, str]) -> None:
    assert hub.frames_from(lambda: hub.call("GET", "/api/projects"), wait_s=0.5) == []
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(
        lambda: answer.append(hub.call("PUT", "/api/meetings/no-such-meeting", {"title": "x"})), wait_s=0.5)
    assert answer[0][0] == 404
    assert frames == []


def _minimal(schema: Any) -> Any:
    """The smallest value that passes *schema* (required fields only)."""
    kinds = schema.get("type")
    kind = kinds[0] if isinstance(kinds, list) else kinds
    if "enum" in schema:
        return schema["enum"][0]
    if kind == "object":
        properties = schema.get("properties", {})
        names = list(schema.get("required", []))
        if schema.get("minProperties") and not names:
            names = list(properties)[:1]
        return {name: _minimal(properties.get(name, {"type": "string"})) for name in names}
    if kind == "array":
        return [_minimal(schema.get("items", {"type": "string"}))] if schema.get("minItems") else []
    if kind == "integer" or kind == "number":
        return schema.get("minimum", 1)
    if kind == "boolean":
        return True
    return "walk"


def test_no_registered_write_is_silent(hub: Hub, seeded: dict[str, str]) -> None:
    """Walk every ``effect="write"`` operation of the hub's own registry.

    A new write operation is in this walk the day it is declared; it cannot
    ship silent.
    """
    from holdspeak import operations
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime import composition

    registry = composition.current().operations
    owner = Principal(PrincipalKind.OWNER, "the-owner")
    writes = [name for name, bound in registry.operations.items() if bound.descriptor.effect == "write"]
    assert len(writes) >= 60, "the walk lost the catalogue"

    silent: list[str] = []
    failed: dict[str, str] = {}
    for name in writes:
        bound = registry.operations[name]
        # The kernel path of an admitted operation needs real rows (a project
        # revision, a watch). The root under test is the same line for both
        # paths, so the walk runs each operation as exempt; the named writes
        # above run the admitted path for real (resource add, meeting attach).
        descriptor = dataclasses.replace(bound.descriptor, admission=None)
        registry.operations[name] = operations.BoundOperation(
            descriptor, lambda principal, **_arguments: {"id": "walk"}, bound.target)
        try:
            held = {key: None for key in descriptor.held}
            arguments = _minimal(dict(descriptor.args_schema))

            def write() -> None:
                try:
                    registry.invoke(owner, name, arguments, held=held)
                except Exception as exc:  # noqa: BLE001 - reported by name below
                    failed[name] = f"{type(exc).__name__}: {exc}"

            frames = hub.frames_from(write, wait_s=1.0)
        finally:
            registry.operations[name] = bound
        if name not in failed and not frames:
            silent.append(name)
    assert not failed, f"the walk could not call: {failed}"
    assert not silent, f"these write operations sent no desk_changed frame: {silent}"
