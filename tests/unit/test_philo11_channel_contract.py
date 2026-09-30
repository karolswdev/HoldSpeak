"""PHILO-11-01 -- generic document references on the Phase 10 channel contract.

These fences use the real hub, the real project-update producer, and the real
HTTP/MCP operation registry.  The source worker owns the eight-source producer
matrix; this file checks the shared channel lifecycle and its provenance seam.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import _boot, destination  # noqa: E402
from _philo11_documents import OWNER, mint_documents  # noqa: E402
from test_philo5_the_loop import Hub  # noqa: E402
from test_philo9_steward_admission import AGENT_ID, _agent, _tool  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def documents(hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    return mint_documents(hub.db, OWNER, people_keystore_path=tmp_path / "people.key")


def _rows(hub: Hub, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(row) for row in conn.execute(sql, params)]


def test_generic_document_ref_is_one_wire_for_http_mcp_and_history_filter(
    hub: Hub, documents: dict[str, str], tmp_path: Path,
) -> None:
    ref = documents["project_update"]
    dest = destination(hub, tmp_path / "out")
    descriptors = {name: hub.root.operations.descriptor(name) for name in (
        "channel.preview", "channel.prepare", "channel.send", "channel.sends")}
    for descriptor in descriptors.values():
        assert "update_id" not in descriptor.args_schema["properties"]
    assert descriptors["channel.preview"].args_schema["required"] == ["document_ref", "destination_id"]

    preview = hub.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": dest,
    })
    assert preview.status_code == 200, preview.text
    is_error, mcp_preview = hub.mcp("channel.preview", {
        "document_ref": ref, "destination_id": dest,
    })
    assert not is_error
    assert mcp_preview["document_ref"] == ref
    assert mcp_preview["payload_digest"] == preview.json()["payload_digest"]

    prepared = hub.client.post("/api/channels/sends", json={
        "document_ref": ref, "destination_id": dest,
    })
    assert prepared.status_code == 200, prepared.text
    send_id = prepared.json()["send"]["id"]
    frozen_json = json.loads(_rows(hub, "SELECT document_json FROM channel_sends WHERE id=?", (send_id,))[0]["document_json"])
    assert frozen_json["label"] == "REV 1" and frozen_json["slug"] == "philo-11"
    assert frozen_json["title"].startswith("Philo 11 — update r1")
    listed = hub.client.get("/api/channels/sends", params={"document_ref": ref})
    assert listed.status_code == 200, listed.text
    assert [row["id"] for row in listed.json()["sends"]] == [send_id]


@pytest.mark.parametrize("kind", ["project_update", "desk_decision"])
def test_prepared_send_uses_frozen_bytes_and_name_after_source_is_deleted(
    hub: Hub, documents: dict[str, str], tmp_path: Path, kind: str,
) -> None:
    ref = documents[kind]
    dest = destination(hub, tmp_path / "out")
    prepared = hub.client.post("/api/channels/sends", json={
        "document_ref": ref, "destination_id": dest,
    }).json()["send"]
    frozen = prepared["preview"]["text"]
    with hub.db._connection() as conn:
        if kind == "project_update":
            conn.execute("DELETE FROM project_updates WHERE id=?", (ref.split(":", 1)[1],))
        else:
            conn.execute("UPDATE desk_decisions SET deleted=1 WHERE id=?", (ref.split(":", 1)[1],))

    missing_preview = hub.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": dest,
    })
    assert missing_preview.status_code == 404, missing_preview.text
    assert missing_preview.json()["code"] == "document_not_found"

    sent = hub.client.post("/api/channels/send", json={"send_id": prepared["id"]})
    assert sent.status_code == 200, sent.text
    body = sent.json()
    assert body["outcome"] == "sent"
    path = Path(body["send"]["file_path"])
    assert path.read_text() == frozen
    frozen_document = prepared["document_json"]
    label_slug = "-".join(re.findall(r"[a-z0-9]+", str(frozen_document["label"]).lower()))
    assert f"-{frozen_document['slug']}-{label_slug}-" in path.name
    assert path.suffix == ".md"
    if kind == "desk_decision":
        assert _rows(hub, "SELECT * FROM project_update_deliveries") == []


def test_legacy_prepared_non_file_row_does_not_reread_deleted_source(
    hub: Hub, documents: dict[str, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Phase 10 row has no provenance; GitHub still sends its frozen bytes after source deletion.

    The only direct row edit is the nullable ``document_json`` column.  The destination and prepared
    row both come through the real HTTP operations, and the CLI edge is canned only at its process
    boundary so this fence can run without a GitHub account.
    """
    from holdspeak.services import channel_cli

    calls: list[tuple[str, ...]] = []

    def runner(argv: Any, **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(str(part) for part in argv))
        if tuple(argv[:3]) == ("gh", "api", "user"):
            return subprocess.CompletedProcess(argv, 0, '{"login":"octo-owner"}', "")
        return subprocess.CompletedProcess(
            argv, 0, "https://github.com/acme/payments/issues/1#issuecomment-7\n", "",
        )

    monkeypatch.setattr(channel_cli, "CLI_RUNNER", runner)
    destination_response = hub.client.post("/api/channels/destinations", json={
        "name": "Payments issue", "channel": "github", "repo": "acme/payments",
        "kind": "issue", "number": 1,
    })
    assert destination_response.status_code == 200, destination_response.text
    destination_id = destination_response.json()["destination"]["id"]
    ref = documents["project_update"]
    prepared_response = hub.client.post("/api/channels/sends", json={
        "document_ref": ref, "destination_id": destination_id,
    })
    assert prepared_response.status_code == 200, prepared_response.text
    prepared = prepared_response.json()["send"]
    with hub.db._connection() as conn:
        conn.execute("UPDATE channel_sends SET document_json=NULL WHERE id=?", (prepared["id"],))
        conn.execute("DELETE FROM project_updates WHERE id=?", (ref.split(":", 1)[1],))

    sent = hub.client.post("/api/channels/send", json={"send_id": prepared["id"]})
    assert sent.status_code == 200, sent.text
    assert sent.json()["outcome"] == "sent"
    assert any(call[:3] == ("gh", "api", "user") for call in calls)
    assert any(call[:3] == ("gh", "issue", "comment") for call in calls)


@pytest.mark.parametrize("kind", ["project_update", "desk_decision"])
def test_inline_send_refuses_changed_preview_then_sends_new_preview(
    hub: Hub, documents: dict[str, str], tmp_path: Path, kind: str,
) -> None:
    ref = documents[kind]
    dest = destination(hub, tmp_path / "out")
    old_preview = hub.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": dest,
    }).json()
    with hub.db._connection() as conn:
        if kind == "project_update":
            conn.execute("UPDATE project_updates SET body_md=? WHERE id=?",
                         ("# Changed source\n\nThe new durable text.\n", ref.split(":", 1)[1]))
        else:
            conn.execute("UPDATE desk_decisions SET decision_markdown=? WHERE id=?",
                         ("Render the changed durable decision.", ref.split(":", 1)[1]))
    refused = hub.client.post("/api/channels/send", json={
        "document_ref": ref, "destination_id": dest,
        "preview_digest": old_preview["payload_digest"],
    })
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "preview_changed"
    fresh = hub.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": dest,
    }).json()
    sent = hub.client.post("/api/channels/send", json={
        "document_ref": ref, "destination_id": dest,
        "preview_digest": fresh["payload_digest"],
    })
    assert sent.status_code == 200 and sent.json()["outcome"] == "sent", sent.text
    assert Path(sent.json()["send"]["file_path"]).read_text() == fresh["preview"]["text"]
    operation = _rows(hub, "SELECT * FROM kernel_operations WHERE operation_id=?",
                      (sent.json()["operation_id"],))[0]
    assert operation["target_ref"] == f"document:{ref}"
    assert sent.json()["receipt"]["outcome"] == "succeeded"
    if kind == "project_update":
        rows = _rows(hub, "SELECT * FROM project_update_deliveries WHERE update_id=?",
                     (ref.split(":", 1)[1],))
        assert len(rows) == 1 and rows[0]["outcome"] == "sent"
    else:
        assert _rows(hub, "SELECT * FROM project_update_deliveries") == []


@pytest.mark.parametrize("kind", ["project_update", "desk_decision"])
def test_kernel_target_names_document_ref_and_external_agent_send_is_refused_over_mcp(
    hub: Hub, documents: dict[str, str], tmp_path: Path, kind: str,
) -> None:
    ref = documents[kind]
    dest = destination(hub, tmp_path / "out")
    is_error, prepared = hub.mcp("channel.prepare", {"document_ref": ref, "destination_id": dest})
    assert not is_error, prepared
    operation = _rows(hub, "SELECT * FROM kernel_operations WHERE operation_id=?",
                      (prepared["operation_id"],))[0]
    assert operation["target_ref"] == f"document:{ref}"

    agent = _agent(hub, identity=AGENT_ID)
    is_error, refused = _tool(agent, "channel.send", {"send_id": prepared["send"]["id"]})
    assert is_error
    assert refused["code"] == "owner_principal_required"
    assert refused["receipt"]["outcome"] == "owner_principal_required"
    assert _rows(hub, "SELECT * FROM channel_sends WHERE id=?", (prepared["send"]["id"],))[0]["state"] == "prepared"


def test_agent_brief_preview_and_prepare_keep_owner_overlay_and_payload(
    hub: Hub, documents: dict[str, str], tmp_path: Path,
) -> None:
    ref = documents["monday_brief"]
    dest = destination(hub, tmp_path / "out")
    owner_preview = hub.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": dest,
    })
    assert owner_preview.status_code == 200, owner_preview.text
    expected = owner_preview.json()
    assert "Avery" in expected["preview"]["text"]
    assert "You owe: 1" in expected["preview"]["text"]

    agent = _agent(hub, identity=f"{AGENT_ID}-brief")
    is_error, agent_preview = _tool(agent, "channel.preview", {
        "document_ref": ref, "destination_id": dest,
    })
    assert not is_error, agent_preview
    assert agent_preview["payload_digest"] == expected["payload_digest"]
    assert agent_preview["preview"] == expected["preview"]
    is_error, prepared = _tool(agent, "channel.prepare", {
        "document_ref": ref, "destination_id": dest,
    })
    assert not is_error, prepared
    assert prepared["send"]["preview"] == expected["preview"]
    assert prepared["send"]["state"] == "prepared"


def test_thread_palette_discovers_destination_then_prepares_without_send_admission(
    hub: Hub, documents: dict[str, str], tmp_path: Path,
) -> None:
    ref = documents["monday_brief"]
    destination(hub, tmp_path / "out", name="#leads")
    from holdspeak.services.thread_tools import CHAT_PALETTE, ThreadToolExecutor

    channel_family = {
        "channel.destinations", "channel.preview", "channel.prepare", "channel.sends",
    }
    assert CHAT_PALETTE & channel_family == {"channel.destinations", "channel.prepare"}
    thread = hub.db.threads.create_thread(title="Channel thread")

    def dispatch(name: str, args: dict[str, Any], principal: Any) -> Any:
        return hub.root.operations.invoke(principal, name, args)

    executor = ThreadToolExecutor(
        hub.db, dispatch_fn=dispatch, principal=OWNER, control_mode_fn=lambda: "yolo",
        allowed_names=CHAT_PALETTE,
    )
    listed = executor.execute(executor.admit(
        "turn-destinations", thread.id,
        {"id": "destinations", "name": "channel.destinations", "arguments": {}},
    ))
    found = next(item for item in listed.payload["destinations"] if item["name"] == "#leads")
    prepared = executor.execute(executor.admit(
        "turn-prepare", thread.id,
        {"id": "prepare", "name": "channel.prepare",
         "arguments": {"document_ref": ref, "destination_id": found["id"]}},
    ))
    assert prepared.payload["send"]["state"] == "prepared"
    assert "Avery" in prepared.payload["send"]["preview"]["text"]
    before = len(_rows(hub, "SELECT * FROM kernel_operations"))
    with pytest.raises(ValueError, match="Tool outside the admitted palette"):
        executor.admit("turn-send", thread.id, {"id": "send", "name": "channel.send", "arguments": {}})
    assert len(_rows(hub, "SELECT * FROM kernel_operations")) == before
