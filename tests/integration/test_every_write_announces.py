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
   the registry. The only quiet routes are named there, one by one.

One write sends ONE frame. Announcements made inside the write are held and
leave together; ``changes`` names each object. Every count here is exact.

Everything runs against a real hub (``MeetingWebServer.start()``, a real port,
a real ``/ws`` client). The two roots are fenced apart: the registry tests call
``registry.invoke`` with no HTTP request (so the middleware cannot cover for
it), and the HTTP tests use routes that never reach the registry.
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


def test_the_named_writes_each_send_one_frame(hub: Hub, seeded: dict[str, str]) -> None:
    counts: dict[str, int] = {}
    for label, write in NAMED_WRITES.items():
        answer: list[tuple[int, Any]] = []
        frames = hub.frames_from(lambda: answer.append(write(hub, seeded)))
        status, body = answer[0]
        assert 200 <= status < 300, f"{label}: the write itself failed ({status}): {body!r}"
        counts[label] = len(frames)
    silent = [label for label, count in counts.items() if count == 0]
    assert not silent, f"these writes sent no desk_changed frame: {silent}"
    assert counts == {label: 1 for label in NAMED_WRITES}, counts


def test_a_write_sends_one_frame_not_two(hub: Hub, seeded: dict[str, str]) -> None:
    """A note announces from its service; the roots add no second frame."""
    frames = hub.frames_from(lambda: hub.call("POST", "/api/notes", {"title": "One frame", "body_markdown": "x"}))
    assert len(frames) == 1, frames
    assert frames[0]["kind"] == "note" and frames[0]["op"] == "create"
    assert frames[0]["changes"] == [{"kind": "note", "id": frames[0]["id"], "op": "create"}]
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


def test_a_settings_write_is_not_silenced_by_its_last_path_word(hub: Hub, seeded: dict[str, str]) -> None:
    """Astra, #771 finding 1: ``PUT /api/settings/heartbeat`` wrote and sent nothing.

    A suffix rule (``heartbeat``, meant for node traffic) silenced it. No rule
    by prefix or suffix is left: only the routes named in ``QUIET_ROUTES``.
    """
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(
        lambda: answer.append(hub.call("PUT", "/api/settings/heartbeat", {"sweep_every_minutes": 17})))
    assert answer[0][0] == 200, answer
    assert hub.call("GET", "/api/settings/heartbeat")[1]["sweep_every_minutes"] == 17
    assert len(frames) == 1, frames
    assert (frames[0]["kind"], frames[0]["op"]) == ("setting", "update")


def test_the_quiet_routes_are_real_named_and_quiet(hub: Hub, seeded: dict[str, str]) -> None:
    from holdspeak.web.announce import QUIET_ROUTES

    live = {
        (method, route.path)
        for route in hub.server.app.routes
        for method in (getattr(route, "methods", None) or ())
    }
    stale = sorted(key for key in QUIET_ROUTES if key not in live)
    assert not stale, f"QUIET_ROUTES names routes the hub does not have: {stale}"
    assert all(reason.strip() for reason in QUIET_ROUTES.values())

    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(
        lambda: answer.append(hub.call("POST", "/api/grounding/resolve", {"refs": []})), wait_s=0.5)
    assert 200 <= answer[0][0] < 300, answer
    assert frames == []


def test_the_room_read_marker_sends_no_frame(hub: Hub, seeded: dict[str, str]) -> None:
    """Astra, #785 finding 1: each Room writes its read marker when it opens.

    A frame for it made the Room re-read at once and erase its catch-up list.
    The marker is written and no window is told.
    """
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(
        lambda: answer.append(hub.call("POST", f"/api/projects/{seeded['project']}/room/read")), wait_s=0.6)
    assert answer[0][0] == 200, answer
    assert frames == []


def test_ready_read_sends_one_frame(hub: Hub, seeded: dict[str, str]) -> None:
    """Astra, #771 finding 2: the route broadcast for itself and the root added a second frame."""
    from holdspeak.db import get_database

    assert get_database().meetings.mark_ready_unseen(seeded["meeting"]) is not None
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(
        lambda: answer.append(hub.call("POST", f"/api/meetings/{seeded['meeting']}/ready/read")))
    assert answer[0][0] == 200 and answer[0][1]["ready_at"], answer
    assert len(frames) == 1, frames
    # The Dock reads these two fields (web/src/desk/components/window/Dock.tsx).
    assert (frames[0]["kind"], frames[0]["id"]) == ("meeting_ready_read", seeded["meeting"])


def test_a_bulk_write_sends_one_frame_that_names_each_item(hub: Hub, seeded: dict[str, str]) -> None:
    """Astra, #771 finding 2: parking three items sent three frames."""
    status, body = hub.call("POST", "/api/workbenches", {"name": "Bulk fence"})
    assert status == 201, body
    workbench = body["workbench"]["id"]
    items = []
    for title in ("one", "two", "three"):
        status, body = hub.call("POST", f"/api/workbenches/{workbench}/items", {"title": title})
        assert status == 201, body
        items.append(body["item"]["id"])

    for verb in ("park", "restore"):
        answer: list[tuple[int, Any]] = []
        frames = hub.frames_from(lambda: answer.append(
            hub.call("POST", f"/api/workbenches/{workbench}/items/{verb}", {"item_ids": items})))
        assert answer[0][0] == 200, answer
        assert len(frames) == 1, f"{verb}: {frames}"
        named = {change["id"] for change in frames[0]["changes"]}
        assert set(items) <= named, f"{verb}: the frame names {named}, not every item of {items}"


def test_an_admitted_write_with_no_http_request_sends_one_frame(hub: Hub, seeded: dict[str, str]) -> None:
    """Astra, #771 finding 3: the registry's root, with nothing to cover for it.

    ``project.resource.add`` is admitted (the kernel path) and its service has
    no ``on_changed``. Called on the registry, with no HTTP request, only
    ``OperationRegistry.invoke`` can announce it. With that announcement
    removed this test fails; the HTTP middleware cannot make it pass.
    """
    from holdspeak.principals import Principal, PrincipalKind

    registry = hub.root.operations
    owner = Principal(PrincipalKind.OWNER, "the-owner")
    status, body = hub.call("POST", "/api/notes", {"title": "Filed directly", "body_markdown": "x"})
    assert status == 201, body
    ref = f"note:{body['note']['id'] if 'note' in body else body['id']}"

    for name, op in (("project.resource.add", "resource.add"), ("project.resource.remove", "resource.remove")):
        assert registry.descriptor(name).admission.rule == "admitted"
        frames = hub.frames_from(lambda: registry.invoke(
            owner, name, {"project_id": seeded["project"], "resource_ref": ref}))
        assert len(frames) == 1, f"{name}: {frames}"
        assert (frames[0]["kind"], frames[0]["id"], frames[0]["op"]) == ("project", seeded["project"], op)
        listed = {row["resource_ref"] for row in registry.invoke(
            owner, "project.resource.list", {"project_id": seeded["project"]})}
        assert (ref in listed) == (name == "project.resource.add")


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
    registry = hub.root.operations
    owner = Principal(PrincipalKind.OWNER, "the-owner")
    writes = [name for name, bound in registry.operations.items() if bound.descriptor.effect == "write"]
    assert len(writes) >= 60, "the walk lost the catalogue"

    counts: dict[str, int] = {}
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
        counts[name] = len(frames)
    assert not failed, f"the walk could not call: {failed}"
    silent = [name for name, count in counts.items() if count == 0]
    assert not silent, f"these write operations sent no desk_changed frame: {silent}"
    assert set(counts.values()) == {1}, {name: count for name, count in counts.items() if count != 1}
