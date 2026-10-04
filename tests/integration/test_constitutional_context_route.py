"""The Context face saves through the real route into the real database.

Scar (inventory 2026-10-03): `constitutional_context.py` read `db._conn`, an
attribute `Database` never had. Every read fell back to revision 0 without a
word, and every Save returned HTTP 500 with the Python error on the face.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def client(tmp_path):
    reset_database()
    get_database(tmp_path / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    yield TestClient(server.app)
    reset_database()


def test_save_then_read_returns_the_saved_text(client) -> None:
    saved = client.put("/api/constitutional-context", json={"content": "I lead three engineers."})
    assert saved.status_code == 200, saved.text
    assert saved.json()["context"]["revision"] == 1

    read = client.get("/api/constitutional-context").json()["context"]
    assert read["content"] == "I lead three engineers."
    assert read["revision"] == 1

    again = client.put("/api/constitutional-context", json={"content": "I lead four engineers."})
    assert again.json()["context"]["revision"] == 2

    history = client.get("/api/constitutional-context/history").json()["revisions"]
    assert [row["revision"] for row in history] == [2, 1]
    assert history[0]["content"] == "I lead four engineers."


def test_the_saved_text_reaches_a_run(client) -> None:
    from holdspeak.constitutional_context import (
        constitutional_receipt,
        constitutional_system_message,
    )

    client.put("/api/constitutional-context", json={"content": "Rust first."})
    assert constitutional_system_message() == "Rust first."
    assert constitutional_receipt()["revision"] == 1
