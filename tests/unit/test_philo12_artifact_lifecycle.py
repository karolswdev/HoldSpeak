"""PHILO-12-01 -- Phase 10's Send lifecycle over a real artifact producer.

The source is minted by ``synthesize_and_persist`` from durable meeting
intelligence rows.  The lifecycle fences then use the real hub over HTTP and
MCP, so a green result proves the artifact follows the existing preview,
prepare and owner-press paths.
"""
from __future__ import annotations

import hashlib
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot
from test_philo9_steward_admission import AGENT_ID, _agent, _tool
from _philo12_artifacts import mint_meeting_synthesis


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _rows(hub: Hub, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(row) for row in conn.execute(sql, params)]


def _destination(hub: Hub, folder: Path, *, name: str = "Artifact folder") -> str:
    folder.mkdir(parents=True, exist_ok=True)
    response = hub.client.post(
        "/api/channels/destinations",
        json={"name": name, "channel": "file", "folder": str(folder)},
    )
    assert response.status_code == 200, response.text
    return response.json()["destination"]["id"]


def _mint_artifact(hub: Hub) -> tuple[str, str]:
    """Mint one artifact through the sibling lane's real producer helper."""
    return mint_meeting_synthesis(hub.db), ""


def test_artifact_preview_equals_frozen_payload_and_is_read_only(
    hub: Hub, tmp_path: Path
) -> None:
    document_ref, _body = _mint_artifact(hub)
    destination_id = _destination(hub, tmp_path / "artifact-preview")
    before_operations = _rows(hub, "SELECT * FROM kernel_operations")

    preview_response = hub.client.post(
        "/api/channels/preview",
        json={"document_ref": document_ref, "destination_id": destination_id},
    )
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    payload = preview["preview"]["text"].encode("utf-8")
    assert preview["payload_digest"] == hashlib.sha256(payload).hexdigest()
    assert _rows(hub, "SELECT * FROM channel_sends") == []
    assert _rows(hub, "SELECT * FROM kernel_operations") == before_operations

    prepared_response = hub.client.post(
        "/api/channels/sends",
        json={"document_ref": document_ref, "destination_id": destination_id},
    )
    assert prepared_response.status_code == 200, prepared_response.text
    send = prepared_response.json()["send"]
    assert send["preview"] == preview["preview"]
    assert send["payload_digest"] == preview["payload_digest"]
    stored_payload = _rows(
        hub, "SELECT payload FROM channel_sends WHERE id = ?", (send["id"],)
    )[0]["payload"]
    assert stored_payload == payload


def test_artifact_body_change_refuses_old_preview_before_owner_send(
    hub: Hub, tmp_path: Path
) -> None:
    document_ref, _body = _mint_artifact(hub)
    destination_id = _destination(hub, tmp_path / "artifact-changed")
    old_preview_response = hub.client.post(
        "/api/channels/preview",
        json={"document_ref": document_ref, "destination_id": destination_id},
    )
    assert old_preview_response.status_code == 200, old_preview_response.text
    old_preview = old_preview_response.json()

    artifact_id = document_ref.split(":", 1)[1]
    with hub.db._connection() as conn:
        stored = conn.execute(
            "SELECT body_markdown FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()["body_markdown"]
        conn.execute(
            "UPDATE artifacts SET body_markdown = ?, updated_at = ? WHERE id = ?",
            (f"{stored}\n\nThe stored body changed.\n", "2026-09-30T10:00:00", artifact_id),
        )

    refused = hub.client.post(
        "/api/channels/send",
        json={
            "document_ref": document_ref,
            "destination_id": destination_id,
            "preview_digest": old_preview["payload_digest"],
        },
    )
    assert refused.status_code == 409, refused.text
    body = refused.json()
    assert body["code"] == "preview_changed"
    assert body["receipt"]["outcome"] == "preview_changed"
    assert _rows(hub, "SELECT * FROM channel_sends") == []

    fresh = hub.client.post(
        "/api/channels/preview",
        json={"document_ref": document_ref, "destination_id": destination_id},
    ).json()
    sent = hub.client.post(
        "/api/channels/send",
        json={
            "document_ref": document_ref,
            "destination_id": destination_id,
            "preview_digest": fresh["payload_digest"],
        },
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["outcome"] == "sent"
    assert Path(sent.json()["send"]["file_path"]).read_text() == fresh["preview"]["text"]


def test_artifact_send_and_discard_have_one_terminal_winner(
    hub: Hub, tmp_path: Path
) -> None:
    document_ref, _body = _mint_artifact(hub)
    destination_id = _destination(hub, tmp_path / "artifact-winner")
    prepared_response = hub.client.post(
        "/api/channels/sends",
        json={"document_ref": document_ref, "destination_id": destination_id},
    )
    assert prepared_response.status_code == 200, prepared_response.text
    prepared = prepared_response.json()["send"]
    send_id = prepared["id"]
    barrier = threading.Barrier(2)
    answers: dict[str, Any] = {}

    def press(kind: str) -> None:
        barrier.wait(5)
        if kind == "send":
            answers[kind] = hub.client.post(
                "/api/channels/send", json={"send_id": send_id}
            )
        else:
            answers[kind] = hub.client.post(
                f"/api/channels/sends/{send_id}/discard", json={}
            )

    threads = [threading.Thread(target=press, args=(kind,)) for kind in ("send", "discard")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)

    assert sorted(answer.status_code for answer in answers.values()) == [200, 409]
    loser = next(answer for answer in answers.values() if answer.status_code == 409)
    assert loser.json()["code"] == "send_already_settled"
    assert loser.json()["receipt"]["outcome"] == "send_already_settled"
    row = _rows(hub, "SELECT state FROM channel_sends WHERE id = ?", (send_id,))[0]
    assert row["state"] in {"sent", "discarded"}


def test_external_agent_cannot_press_send_for_an_artifact(
    hub: Hub, tmp_path: Path
) -> None:
    document_ref, _body = _mint_artifact(hub)
    destination_id = _destination(hub, tmp_path / "artifact-agent")
    prepared_response = hub.client.post(
        "/api/channels/sends",
        json={"document_ref": document_ref, "destination_id": destination_id},
    )
    assert prepared_response.status_code == 200, prepared_response.text
    prepared = prepared_response.json()["send"]

    agent = _agent(hub, identity=f"{AGENT_ID}-artifact")
    is_error, refused = _tool(
        agent, "channel.send", {"send_id": prepared["id"]}
    )
    assert is_error is True
    assert refused["code"] == "owner_principal_required"
    assert refused["receipt"]["outcome"] == "owner_principal_required"
    assert _rows(hub, "SELECT state FROM channel_sends WHERE id = ?", (prepared["id"],))[0]["state"] == "prepared"


def test_thread_can_prepare_an_artifact_but_does_not_send_it(
    hub: Hub, tmp_path: Path
) -> None:
    document_ref, _body = _mint_artifact(hub)
    destination_id = _destination(hub, tmp_path / "artifact-thread")
    from holdspeak.services.thread_tools import CHAT_PALETTE, ThreadToolExecutor

    assert {"channel.destinations", "channel.prepare"} <= CHAT_PALETTE
    thread = hub.db.threads.create_thread(title="Artifact lifecycle thread")

    def dispatch(name: str, arguments: dict[str, Any], principal: Any) -> Any:
        return hub.root.operations.invoke(principal, name, arguments)

    executor = ThreadToolExecutor(
        hub.db,
        dispatch_fn=dispatch,
        principal=Principal(PrincipalKind.OWNER, "philo12-thread-owner"),
        control_mode_fn=lambda: "yolo",
        allowed_names=CHAT_PALETTE,
    )
    listed = executor.execute(
        executor.admit(
            "artifact-thread-destinations",
            thread.id,
            {"id": "destinations", "name": "channel.destinations", "arguments": {}},
        )
    )
    found = next(item for item in listed.payload["destinations"] if item["id"] == destination_id)
    prepared = executor.execute(
        executor.admit(
            "artifact-thread-prepare",
            thread.id,
            {
                "id": "prepare",
                "name": "channel.prepare",
                "arguments": {"document_ref": document_ref, "destination_id": found["id"]},
            },
        )
    )
    assert prepared.kind not in {"error", "tool_execution_failed"}, prepared.payload
    assert "send" in prepared.payload, prepared.payload
    assert prepared.payload["send"]["state"] == "prepared"
    assert prepared.payload["send"]["document_ref"] == document_ref
    assert _rows(hub, "SELECT state FROM channel_sends WHERE document_ref = ?", (document_ref,))


def test_tools_list_names_artifact_send_and_the_document_argument(
    hub: Hub,
) -> None:
    listed = hub.client.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert listed.status_code == 200, listed.text
    tools = {tool["name"]: tool for tool in listed.json()["result"]["tools"]}
    prepare = tools["channel.prepare"]
    description = prepare["description"].lower()
    assert "send this artifact to <destination>" in description
    assert "prepare a send" in description
    assert {"document_ref", "destination_id"} <= set(
        prepare["inputSchema"]["properties"]
    )
    assert prepare["inputSchema"]["required"] == ["document_ref", "destination_id"]
