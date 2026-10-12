"""PHILO-5-04: bounded rehearsal capture on the real graph-walk hub.

The recorder is optional, sits around the real MeetingWebServer app, and keeps
only MCP JSON-RPC bodies. These tests exercise the production hub process so a
unit-only ASGI double cannot accidentally certify the Codex proof path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import graph_walk as gw


TOKEN = "philo5-04-recording-test"


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_recording_is_opt_in_and_transcript_path_is_fenced(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plain = gw.Hub(home, token=TOKEN)
    assert plain.transcript_path is None

    with pytest.raises(gw.Refused, match="not under the hub's temporary HOME"):
        gw.Hub(home, token=TOKEN, record_rehearsal=True,
               transcript_path=tmp_path / "outside.jsonl")


@pytest.mark.timeout(180)
def test_real_hub_records_complete_mcp_bodies_and_redacts_other_requests(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    hub = gw.Hub(home, token=TOKEN, record_rehearsal=True).start()
    try:
        # Hub.start() performs the real health request. These two calls are the
        # same endpoint used by the Codex proxy: catalogue, then operation.
        assert hub.api("GET", "/health?token=query-secret")[0] == 200
        listed = hub.mcp({"jsonrpc": "2.0", "id": 1,
                          "method": "tools/list", "params": {}})
        called = hub.mcp({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "desk.list", "arguments": {"kind": "decisions"}},
        })
        restart = hub.restart()
        after_restart = hub.mcp({"jsonrpc": "2.0", "id": 3,
                                 "method": "tools/list", "params": {}})
        assert listed.get("jsonrpc") == "2.0"
        assert called.get("jsonrpc") == "2.0"
        assert after_restart.get("jsonrpc") == "2.0"
        assert restart["same_db_path"]
        assert hub.transcript_path is not None
        assert hub.transcript_path.is_relative_to(home.resolve())
        assert len([row for row in hub.http_exchanges if row.get("path") == "/api/mcp"]) >= 3
        transcript_path = hub.transcript_path
    finally:
        hub.stop()
    rows = _lines(transcript_path)

    mcp_rows = [row for row in rows if row["path"] == "/api/mcp"]
    assert len(mcp_rows) >= 2
    by_id = {
        row["request_body"]["id"]: row
        for row in mcp_rows
        if isinstance(row.get("request_body"), dict)
    }
    assert by_id[1]["request_body"] == {
        "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {},
    }
    assert by_id[1]["response_body"] == listed
    assert by_id[2]["request_body"]["method"] == "tools/call"
    assert by_id[2]["response_body"] == called
    assert by_id[3]["response_body"] == after_restart
    for row in (by_id[1], by_id[2], by_id[3]):
        assert row["method"] == "POST"
        assert row["status"] == 200
        assert row["path"] == "/api/mcp"
        assert row["started_at"] <= row["finished_at"]
        assert isinstance(row["duration_ms"], (int, float))

    non_mcp = [row for row in rows if row["path"] != "/api/mcp"]
    assert non_mcp
    assert all(row == {"method": "GET", "path": "/health", "status": 200}
               for row in non_mcp)
    serialized = json.dumps(rows)
    assert TOKEN not in serialized
    assert "query-secret" not in serialized
    assert "Authorization" not in serialized
    assert "token=" not in serialized


def test_import_op_cites_the_hash_already_computed_for_the_real_fixture(
    tmp_path: Path,
) -> None:
    """The hash citation is unit-fenced; the real-hub producer is tested above."""
    fixture_home = tmp_path / "home"
    fixture_home.mkdir()
    fixture = fixture_home / "fixture.wav"
    fixture.write_bytes(b"fixture bytes")
    expected_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()

    class FakeHub:
        """Transport double only; the fixture bytes and hash are real."""

        home = fixture_home

        def mcp(self, request: dict[str, Any]) -> dict[str, Any]:
            return {
                "jsonrpc": "2.0", "id": request["id"],
                "result": {"content": [{"type": "text", "text": json.dumps({
                    "meeting_id": "m-1", "transcription_status": "importing",
                })}], "isError": False},
            }

    provenance: dict[str, Any] = {"fixture_hashes": {}, "restarts": [],
                                  "boundary_substitutions": [], "clock": {}}
    result = gw.run_step(
        {"kind": "op", "name": "meeting.import",
         "args": {"path": str(fixture), "title": "Words"}},
        page=None, hub=FakeHub(), provenance=provenance, variables={},
    )
    assert result["fixture"] == {"path": str(fixture), "sha256": expected_hash}
