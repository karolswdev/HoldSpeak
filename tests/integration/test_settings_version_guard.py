"""HS-130-07: `/api/settings` optimistic-concurrency (version) guard.

Two open surfaces write partial trees to the same settings document. Without a
version guard the second write silently clobbers the first (last-writer-wins,
because each surface merges its own stale copy of the untouched subtree). The
guard makes a PUT carry the `_revision` it read; a stale revision is rejected
with a reconcilable 409 rather than blindly merged.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            on_settings_applied=MagicMock(),
        )
    )
    return TestClient(server.app)


def test_get_carries_a_revision(client: TestClient, settings_path: Path) -> None:
    body = client.get("/api/settings").json()
    assert isinstance(body.get("_revision"), str) and body["_revision"]


def test_revision_changes_after_a_write(client: TestClient, settings_path: Path) -> None:
    first = client.get("/api/settings").json()["_revision"]
    # HS-139-01: use a living field (desk_sounds) instead of the deleted theme.
    resp = client.put("/api/settings", json={"ui": {"desk_sounds": False}})
    assert resp.status_code == 200, resp.text
    after = resp.json()["settings"]["_revision"]
    assert after != first
    # A fresh GET agrees with the write's returned revision.
    assert client.get("/api/settings").json()["_revision"] == after


def test_matching_revision_is_accepted(client: TestClient, settings_path: Path) -> None:
    rev = client.get("/api/settings").json()["_revision"]
    resp = client.put(
        "/api/settings", json={"_revision": rev, "ui": {"desk_sounds": False}}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


def test_stale_revision_is_rejected_with_409(
    client: TestClient, settings_path: Path
) -> None:
    # Both surfaces read the same revision.
    rev0 = client.get("/api/settings").json()["_revision"]
    # Surface A writes a different subtree — the document moves forward.
    a = client.put(
        "/api/settings",
        json={"_revision": rev0, "dictation": {"pipeline": {"enabled": True}}},
    )
    assert a.status_code == 200, a.text
    # Surface B, still holding rev0, writes yet another subtree. Its stale copy
    # of the pipeline subtree would clobber A's edit — so it is rejected.
    b = client.put(
        "/api/settings",
        json={"_revision": rev0, "ui": {"desk_sounds": False}},
    )
    assert b.status_code == 409, b.text
    payload = b.json()
    assert payload["success"] is False
    assert "reload" in payload["error"].lower()
    # The conflict hands back the current revision so B can reconcile.
    assert payload["revision"] == a.json()["settings"]["_revision"]


def test_no_write_loss_after_reconcile(
    client: TestClient, settings_path: Path
) -> None:
    rev0 = client.get("/api/settings").json()["_revision"]
    a = client.put(
        "/api/settings",
        json={"_revision": rev0, "dictation": {"pipeline": {"enabled": True}}},
    )
    assert a.status_code == 200
    rev1 = a.json()["settings"]["_revision"]
    # B reloads to rev1 and reapplies its edit — now it lands.
    b = client.put(
        "/api/settings", json={"_revision": rev1, "ui": {"desk_sounds": False}}
    )
    assert b.status_code == 200, b.text
    # Neither write was lost.
    persisted = Config.load(path=settings_path)
    assert persisted.dictation.pipeline.enabled is True
    assert persisted.ui.desk_sounds is False


def test_legacy_put_without_revision_still_applies(
    client: TestClient, settings_path: Path
) -> None:
    # The guard is opt-in per writer: a patch that omits `_revision` keeps the
    # historical last-writer-wins behavior (existing callers are not broken).
    resp = client.put("/api/settings", json={"ui": {"desk_sounds": False}})
    assert resp.status_code == 200, resp.text
    assert Config.load(path=settings_path).ui.desk_sounds is False
