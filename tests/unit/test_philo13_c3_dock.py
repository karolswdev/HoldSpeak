"""PHILO-13 C3 producer-to-frame fence.

The test uses the real isolated hub, database, ChannelService, destination,
document materialization and send boundary. Only the file adapter's terminal
answer is selected for the failed/unknown rows; settlement and the existing
desk_changed producer remain real.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition
from holdspeak.services.channel_contract import Outcome


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import _boot  # noqa: E402

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.mark.parametrize("state", ["sent", "failed", "unknown"])
def test_real_channel_settlement_emits_dock_invalidation(
    hub: Any,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    from _philo10_send import destination, prepare, room, sends

    _project_id, update_id = room(hub)
    send_destination = destination(hub, Path.home() / f"c3-dock-{state}")
    prepared = prepare(hub, update_id, send_destination)
    send_id = prepared["send"]["id"]
    frame_start = len(hub.frames)

    if state != "sent":
        from holdspeak.services.channel_contract import FileChannel

        monkeypatch.setattr(
            FileChannel,
            "dispatch",
            lambda _channel, _row, _seam=None: Outcome(state, f"c3_{state}"),
        )

    response = hub.client.post("/api/channels/send", json={"send_id": send_id})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["outcome"] == state

    durable = next(row for row in sends(hub) if row["id"] == send_id)
    assert durable["state"] == state
    changed = [
        data for frame_type, data in hub.frames[frame_start:]
        if frame_type == "desk_changed" and data.get("kind") == "send"
    ]
    assert changed == [{
        "kind": "send", "id": send_id, "op": state, "origin": "hub",
        # One frame for the write; `changes` names each object it touched.
        "changes": [{"kind": "send", "id": send_id, "op": state}],
    }]
