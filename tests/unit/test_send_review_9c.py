"""Review 9c: masked bytes never leave, and a sent row cannot dispatch twice."""
from __future__ import annotations

import uuid
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _philo10_send import DispatchSpy, destination, files, prepare, preview_digest, send
from test_channel_send_contract import hub  # noqa: F401 -- isolated real-hub fixture

SECRET = "https://example.com/webhook?key=private-value"


def note(hub, text: str) -> str:
    response = hub.client.post("/api/notes", json={"title": "Review draft", "body_markdown": text, "tags": []})
    assert response.status_code == 201, response.text
    return "note:" + response.json()["note"]["id"]


@pytest.mark.parametrize("path", ["inline", "prepared", "mcp", "telegram", "phone", "page", "call"])
def test_masked_payload_is_refused_on_every_send_door(hub, tmp_path: Path, monkeypatch, path: str) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.briefing_service import BriefingService
    from holdspeak.services.errors import ServiceError

    folder = tmp_path / "out"
    dest = destination(hub, folder)
    ref = note(hub, f"The link is {SECRET}")
    digest = preview_digest(hub, ref, dest)
    # Prepare keeps the old stored shape. Boundary validation must protect
    # this row too, without depending on any newly stored security flag.
    row = prepare(hub, ref, dest)["send"]
    spy = DispatchSpy(monkeypatch)
    if path == "call":
        from holdspeak.mcp.tools import dispatch
        from holdspeak.services.thread_tools import ThreadToolExecutor

        thread = hub.db.threads.create_thread(title="Owner call")
        executor = ThreadToolExecutor(hub.db, dispatch_fn=dispatch,
            principal=Principal(PrincipalKind.OWNER,"call-owner"), control_mode_fn=lambda:"yolo",
            held_egress=frozenset({"channel.send"}))
        held = executor.admit("call-turn",thread.id,{"id":"send-call","name":"channel.send","arguments":{"send_id":row["id"]}})
        assert held.state == "awaiting_decision"
        executor.decide(held,"approve")
        result = executor.execute(held)
        assert result.kind == "tool_execution_failed", result
        assert result.payload.get("code") == "payload_holds_credential", result
    elif path == "telegram":
        from holdspeak.services.briefing_service import token_hash

        made = hub.client.post("/api/reach/packages",json={"refs":[f"send:{row['id']}"]})
        assert made.status_code == 201, made.text
        briefing = BriefingService(hub.db)
        package = briefing.store.by_hash(token_hash(made.json()["token"]))
        with pytest.raises(ServiceError) as refusal:
            briefing.answer_package(package["id"], f"send:{row['id']}", "send", via="telegram")
        assert refusal.value.code == "payload_holds_credential"
    elif path in {"phone", "page"}:
        briefing = BriefingService(hub.db)
        with pytest.raises(ServiceError) as refusal:
            briefing.decide_item(Principal(PrincipalKind.OWNER, "review-owner"), f"send:{row['id']}", "send", via=path)
        assert refusal.value.code == "payload_holds_credential"
    elif path == "mcp":
        error, result = hub.mcp("channel.send", {"send_id": row["id"], "command_id": uuid.uuid4().hex})
        assert error, result
        assert result.get("code", result.get("error_code")) == "payload_holds_credential", result
    else:
        body = {"send_id": row["id"]} if path == "prepared" else {
            "document_ref": ref, "destination_id": dest, "preview_digest": digest,
        }
        response = send(hub, {**body, "command_id": uuid.uuid4().hex})
        assert response.status_code == 409, response.text
        assert response.json().get("code", response.json().get("error_code")) == "payload_holds_credential"
    assert not spy.calls
    assert not files(folder)
    assert hub.db.channel_sends.get(row["id"])["state"] == "prepared"


@pytest.mark.parametrize("text", [
    "github_pat_short", "api key=small-value", '{"token":"small-value"}',
    "https://hooks.slack.com/services/T/B/key", "https://example.com/?%6bey=hidden",
    "https://user:pass@example.com", "123456:abcdefghijklmnopqrst",
])
def test_hub_preview_marks_its_own_masked_payload(hub, tmp_path: Path, text: str) -> None:
    dest = destination(hub, tmp_path / "out")
    ref = note(hub, text)
    response = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest})
    assert response.status_code == 200, response.text
    assert response.json()["preview"].get("credential_blocked") is True
    assert prepare(hub, ref, dest)["send"]["preview"].get("credential_blocked") is True


def test_a_sent_prepared_id_returns_its_receipt_without_another_dispatch(hub, tmp_path: Path, monkeypatch) -> None:
    folder = tmp_path / "out"
    dest = destination(hub, folder)
    ref = note(hub, "The report is ready.")
    row = prepare(hub, ref, dest)["send"]
    spy = DispatchSpy(monkeypatch)
    command = {"send_id": row["id"], "command_id": "first-press"}
    first = send(hub, command)
    assert first.status_code == 200, first.text
    # Same-command replay and a new command on an already-sent id both
    # return the original receipt. Neither is permission to dispatch again.
    for body in (command, {**command, "command_id": "second-activation"}):
        replay = send(hub, body)
        assert replay.status_code == 200, replay.text
        assert replay.json()["send"] == first.json()["send"]
    assert spy.calls == 1
    assert len(files(folder)) == 1
