"""Remote access settings use the Hub's durable config authority."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.config import Config  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    server = seeds._boot(tmp_path, monkeypatch)
    try:
        yield server
    finally:
        server.server.stop()
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_remote_settings_keep_partial_edits_across_a_hub_restart(
    hub: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = hub
    response = first.client.put(
        "/api/settings/remote",
        json={"enabled": True, "bind_host": "100.64.0.2", "port": 8765},
    )
    assert response.status_code == 200, response.text
    assert response.json()["enabled"] is True

    persisted = Config.load()
    assert persisted.remote.streamable_http_enabled is True
    assert persisted.remote.bind_host == "100.64.0.2"
    assert persisted.remote.port == 8765

    partial = first.client.put("/api/settings/remote", json={"port": 9876})
    assert partial.status_code == 200, partial.text
    assert partial.json()["bind_host"] == "100.64.0.2"
    assert partial.json()["port"] == 9876
    persisted = Config.load()
    assert persisted.remote.streamable_http_enabled is True
    assert persisted.remote.bind_host == "100.64.0.2"
    assert persisted.remote.port == 9876

    first.server.stop()
    restarted = seeds._boot(tmp_path, monkeypatch)
    try:
        readback = restarted.client.get("/api/settings/remote")
        assert readback.status_code == 200, readback.text
        assert readback.json()["enabled"] is True
        assert readback.json()["bind_host"] == "100.64.0.2"
        assert readback.json()["port"] == 9876
        assert restarted.client.get("/api/settings/hub").json()["system"]["remote"] is True
    finally:
        restarted.server.stop()
