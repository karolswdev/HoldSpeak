"""Send from the Desk, hub half: the palette's `send` pick and his press.

The test diet (2026-10-11) moved the outcome legs of the palette walk out of
the browser suite. The palette row and its pick (the well opens on the
destination; no POST) are fenced in vitest
(web/src/desk/__tests__/palette.philo1314.test.tsx); the SAVED receipt the
well draws from a `sent` row is fenced in
web/src/desk/surface/send/__tests__/SendWell.test.tsx. This file proves the
hub half on a real hub: the preview the well shows writes nothing, and his
press makes one `sent` row and a real file in the folder.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _sends(hub: Hub, ref: str) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        rows = conn.execute("SELECT id, state, proof_json FROM channel_sends WHERE document_ref = ?", (ref,)).fetchall()
    return [{"id": r[0], "state": r[1], "proof": json.loads(r[2] or "{}")} for r in rows]


def _ops(hub: Hub) -> list[tuple[str, str]]:
    with hub.db._connection() as conn:
        return [(r[0], r[1]) for r in conn.execute(
            "SELECT operation_id, name FROM kernel_operations ORDER BY created_at").fetchall()]


def test_the_send_preview_writes_nothing_and_his_press_saves_one_file(hub: Hub, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo13_14_palette_glass.py::TestPaletteKnowsHisWeek::test_the_palette_knows_his_week_and_does_verbs
    (the `send` outcome leg: zero channel_sends rows and zero new
    kernel_operations rows until he presses Send; then one `sent` row and the
    file in the folder)."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    # The canvas week's decision, by the real producer (tests/e2e/chair_rig.py `_seed`).
    PrimitiveService(hub.db).create_decision(
        Principal(PrincipalKind.OWNER, "karol"), decision_id="d-freeze", title="Freeze the old ledger on Nov 5",
        status="accepted", decision_markdown="Freeze writes to the old ledger on Nov 5.")
    ref = "desk_decision:d-freeze"
    folder = tmp_path / "Team updates"
    folder.mkdir()
    made = hub.client.post("/api/channels/destinations",
                           json={"name": "Team updates", "channel": "file", "folder": str(folder)})
    assert made.status_code == 200, made.text
    dest = made.json()["destination"]["id"]

    # The well opens: destinations, the ended sends, the preview. Nothing is written.
    ops_before = _ops(hub)
    assert hub.client.get("/api/channels/destinations").status_code == 200
    assert hub.client.get("/api/channels/sends", params={"document_ref": ref}).json()["sends"] == []
    preview = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest})
    assert preview.status_code == 200, preview.text
    assert "Freeze writes to the old ledger on Nov 5." in preview.json()["preview"]["text"]
    assert _sends(hub, ref) == []
    assert [o for o in _ops(hub) if o not in ops_before] == []
    assert [p for p in folder.iterdir()] == []

    # His press: the well's inline form (SendWell.test.tsx asserts the wire).
    sent = hub.client.post("/api/channels/send", json={
        "document_ref": ref, "destination_id": dest,
        "preview_digest": preview.json()["payload_digest"], "command_id": "press-1"})
    assert sent.status_code == 200, sent.text
    rows = _sends(hub, ref)
    assert len(rows) == 1 and rows[0]["state"] == "sent", rows
    path = Path(rows[0]["proof"]["path"])
    assert path.resolve().parent == folder.resolve() and path.is_file(), rows
    # The well's history read: one sent row (drawn SAVED).
    history = hub.client.get("/api/channels/sends", params={"document_ref": ref}).json()["sends"]
    assert [s["state"] for s in history] == ["sent"], history
