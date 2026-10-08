"""PHILO-10-01: the shared rig of the Send fences (a real hub on an isolated HOME).

Every fence reaches the Send through the real transports (``TestClient`` over
the hub's app, ``/api/mcp``) and the real producers: a published update made by
the Room's own routes, a folder destination saved by ``channel.save_destination``,
the file channel's real dispatch. A spy counts the file channel's dispatches by
wrapping the REAL method (it never replaces what it counts).
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402,F401

SENTINEL = "SENTINEL-7f3a-body-never-in-argv-or-receipt"


def sent_text(body: str, name: str = "Payments ledger cutover") -> str:
    """A published update's Markdown as it leaves the desk (PHILO-15 B53
    ruling): the heading "<Project> · Update · <date>" leads, an unchecked
    claim is omitted. The date is the publication's (UTC) date: today."""
    from datetime import datetime, timezone

    from holdspeak.services.channel_contract import without_desk_marks

    return without_desk_marks(body, f"{name} · Update · {datetime.now(timezone.utc).date().isoformat()}")


def room(hub: Hub, *, name: str = "Payments ledger cutover", publish: bool = True, body: Optional[str] = None) -> tuple[str, str]:
    c = hub.client
    pid = c.post("/api/projects", json={"name": name}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    if body is not None:
        saved = c.put(f"/api/updates/{update}", json={"body_md": body})
        assert saved.status_code == 200, saved.text
    if publish:
        assert c.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    return pid, update


def destination(hub: Hub, folder: Path, name: str = "Team folder", **extra: Any) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    resp = hub.client.post("/api/channels/destinations", json={"name": name, "channel": "file",
                                                               "folder": str(folder), **extra})
    assert resp.status_code == 200, resp.text
    return resp.json()["destination"]["id"]


def document_ref(update: str) -> str:
    return f"project_update:{update}"


def desk_decision_ref(hub: Hub) -> str:
    """Mint a desk decision through the real producer for the Phase 11 source fence."""
    is_error, decision = hub.mcp("desk.create", {"kind": "decisions", "data": {
        "title": "Keep the cutover window",
        "status": "accepted",
        "context_markdown": "The migration is ready for the agreed window.",
        "decision_markdown": "Run the migration during the cutover window.",
        "consequences_markdown": "The support team monitors the result.",
    }})
    assert is_error is False, decision
    return f"desk_decision:{decision['id']}"


def source(hub: Hub, kind: str = "project_update") -> str:
    if kind == "project_update":
        _pid, update = room(hub)
        return document_ref(update)
    if kind == "desk_decision":
        return desk_decision_ref(hub)
    raise AssertionError(f"unknown Phase 11 source kind: {kind}")


def prepare(hub: Hub, update: str, dest: str, **extra: Any) -> dict[str, Any]:
    ref = update if ":" in update else document_ref(update)
    resp = hub.client.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest, **extra})
    assert resp.status_code == 200, resp.text
    return resp.json()


def preview_digest(hub: Hub, update: str, dest: str) -> str:
    ref = update if ":" in update else document_ref(update)
    resp = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest})
    assert resp.status_code == 200, resp.text
    return resp.json()["payload_digest"]


def send_body(hub: Hub, form: str, update: str, dest: str, key: str) -> dict[str, Any]:
    """The owner's press in either form: a prepared row or inline document_ref, destination and digest."""
    ref = update if ":" in update else document_ref(update)
    if form == "send_id":
        return {"send_id": prepare(hub, update, dest)["send"]["id"], "command_id": key}
    return {"document_ref": ref, "destination_id": dest, "preview_digest": preview_digest(hub, update, dest),
            "command_id": key}


def send(hub: Hub, body: dict[str, Any]) -> Any:
    return hub.client.post("/api/channels/send", json=body)


def files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file())


def ops(hub: Hub, name: Optional[str] = None) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.revision,"
            " r.outcome AS outcome, r.state AS receipt_state, (SELECT COUNT(*) FROM kernel_receipts x"
            " WHERE x.operation_id=o.operation_id) AS receipts"
            " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid")]
    return [r for r in rows if name is None or r["name"] == name]


def op(hub: Hub, operation_id: str) -> dict[str, Any]:
    found = [o for o in ops(hub) if o["operation_id"] == operation_id]
    assert found, operation_id
    return found[0]


def sends(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM channel_sends ORDER BY created_at, rowid")]


def history(hub: Hub, update: str) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM project_update_deliveries WHERE update_id=? ORDER BY delivered_at, rowid", (update,))]


def history_for_ref(hub: Hub, ref: str) -> list[dict[str, Any]]:
    """Return ended-send history for either the update projection or a new source kind."""
    if ref.startswith("project_update:"):
        return history(hub, ref.split(":", 1)[1])
    with hub.db._connection() as conn:
        rows = conn.execute(
            "SELECT state AS outcome, send_operation_id AS operation_id FROM channel_sends "
            "WHERE document_ref=? AND state IN ('sent','unknown') ORDER BY created_at, rowid", (ref,))
        return [dict(row) for row in rows]


class DispatchSpy:
    """Counts the file channel's REAL dispatches; can hold one before or after the real write."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, *, hold: str = "") -> None:
        from holdspeak.services.channel_contract import FileChannel

        self.calls = 0
        self.hold = hold
        self.entered = threading.Event()
        self.release = threading.Event()
        real: Callable[..., Any] = FileChannel.dispatch

        def dispatch(channel: Any, row: Any, *rest: Any) -> Any:
            self.calls += 1
            if self.hold == "before":
                self.entered.set()
                assert self.release.wait(60)
            outcome = real(channel, row, *rest)
            if self.hold == "after":
                self.entered.set()
                assert self.release.wait(60)
            return outcome

        monkeypatch.setattr(FileChannel, "dispatch", dispatch)


def reap_past_deadline(hub: Hub, seconds: float = 7200.0) -> dict[str, Any]:
    """The REAL liveness reaper, its clock moved past every execution deadline."""
    import time

    from holdspeak.services import project_kernel

    broker = project_kernel._broker(hub.root.channel_service._db)
    real = broker._clock
    broker._clock = lambda: time.time() + seconds
    try:
        return broker.reap_expired()
    finally:
        broker._clock = real


def in_thread(fn: Callable[[], Any]) -> tuple[threading.Thread, list[Any]]:
    box: list[Any] = []
    thread = threading.Thread(target=lambda: box.append(fn()), daemon=True)
    thread.start()
    return thread, box


def until(check: Callable[[], Any], timeout: float = 30.0) -> Any:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.02)
    raise AssertionError("condition never held")
