"""HS-38-03 — webhook write connector (HTTP POST, allow-listed host).

The `network:outbound` reference. These tests prove the actuator proposes a webhook
POST faithfully (and never acts), the connector POSTs only to an allow-listed host,
an off-list host is refused **before** egress (the HTTP client is never invoked), the
allow-list is config-driven and default-empty refuses all, and the full loop drives an
approved proposal to `executed` with the response status + an audit row — all with an
**injected client**, so the default suite makes no real HTTP call.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.config import MeetingConfig
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.actuator_executor import ActuatorExecutor
from holdspeak.plugins.actuators import ActuatorProposal
from holdspeak.plugins.builtin.webhook_post_actuator import (
    WebhookPostActuator,
    WebhookResponse,
    build_webhook_connector,
    register_webhook_post_actuator,
)
from holdspeak.plugins.contracts import PluginRun
from holdspeak.plugins.gated_connector import ConnectorOperationRefused
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.persistence import record_actuator_proposal

ACTUATOR_ID = WebhookPostActuator.id
HOOK_URL = "https://hooks.example.test/services/T000/B000/xyz"
HOOK_HOST = "hooks.example.test"

_CONTEXT = {
    "meeting_title": "Onboarding sync",
    "webhook_url": HOOK_URL,
    "action_items": [
        {"task": "Define the welcome screen copy", "owner": "Ana"},
        {"task": "Wire the sample project content", "owner": None},
    ],
}


class _FakeClient:
    """Records (url, body) and returns a canned WebhookResponse (or raises)."""

    def __init__(self, *, status: int = 200, raises: bool = False):
        self.calls: list[tuple[str, object]] = []
        self._status = status
        self._raises = raises

    def __call__(self, url, body):
        self.calls.append((url, body))
        if self._raises:
            raise ConnectionError("network down")
        return WebhookResponse(status=self._status, body="ok")


# ──────────────────────── The proposal is faithful ────────────────────


def test_actuator_proposes_faithful_webhook_post() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_webhook_post_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "proposed"
    out = result.output
    assert out["target"] == "webhook"
    assert out["action"] == "post_message"
    assert out["payload"]["url"] == HOOK_URL
    assert "text" in out["payload"]["body"]
    assert HOOK_HOST in out["preview"]


def test_actuator_without_url_is_error() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_webhook_post_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context={"meeting_title": "x"}, meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "error"  # run() raised → no proposal


def test_actuator_capability_off_blocks_proposing() -> None:
    host = PluginHost(default_timeout_seconds=1.0)  # no `actuator` capability
    register_webhook_post_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "blocked"


# ──────────────────────── Allow-list (config-driven) ──────────────────


def _proposal(url=HOOK_URL, body=None) -> ActuatorProposal:
    return ActuatorProposal(
        target="webhook",
        action="post_message",
        preview="x",
        payload={"url": url, "body": body if body is not None else {"text": "hi"}},
    )


def test_connector_posts_to_allow_listed_host() -> None:
    client = _FakeClient(status=200)
    connector = build_webhook_connector(allowed_hosts=[HOOK_HOST], client=client)

    result = connector(_proposal())

    assert result == {"status": 200, "host": HOOK_HOST}
    assert len(client.calls) == 1
    assert client.calls[0][0] == HOOK_URL
    assert client.calls[0][1] == {"text": "hi"}


def test_off_list_host_refused_before_egress() -> None:
    client = _FakeClient()
    connector = build_webhook_connector(allowed_hosts=[HOOK_HOST], client=client)

    with pytest.raises(ConnectorOperationRefused):
        connector(_proposal(url="https://evil.example.test/hook"))
    assert client.calls == []  # the HTTP client was never invoked → no egress


def test_default_empty_allow_list_refuses_all() -> None:
    client = _FakeClient()
    connector = build_webhook_connector(allowed_hosts=[], client=client)

    with pytest.raises(ConnectorOperationRefused):
        connector(_proposal())
    assert client.calls == []


def test_allow_list_comes_from_config() -> None:
    """The host allow-list is `MeetingConfig.webhook_allowed_hosts` (the resolved
    HS-38-01 deferral); the connector is built from it."""
    cfg = MeetingConfig(webhook_allowed_hosts=[" Hooks.Example.Test "])  # normalized
    assert cfg.webhook_allowed_hosts == [HOOK_HOST]
    client = _FakeClient(status=204)
    connector = build_webhook_connector(allowed_hosts=cfg.webhook_allowed_hosts, client=client)

    result = connector(_proposal())
    assert result == {"status": 204, "host": HOOK_HOST}


# ──────────────────────── Full loop (injected client) ─────────────────


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "hook.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Onboarding sync", segments=[])
    )
    return db


def _propose(db: Database, host: PluginHost) -> str:
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h1"
    )
    assert result.status == "proposed", result
    run = PluginRun(
        plugin_id=result.plugin_id,
        plugin_version=result.plugin_version,
        window_id="w1",
        meeting_id="m1",
        profile="balanced",
        status="proposed",
        idempotency_key=result.idempotency_key,
        started_at=0.0,
        finished_at=0.1,
        duration_ms=result.duration_ms,
        output=result.output,
    )
    record_actuator_proposal(db, run)
    proposals = db.actuators.list_proposals("m1")
    assert len(proposals) == 1
    return proposals[0].id


def test_full_loop_approve_execute_audit(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_webhook_post_actuator(host)
    client = _FakeClient(status=200)
    connector = build_webhook_connector(allowed_hosts=[HOOK_HOST], client=client)

    pid = _propose(db, host)
    executor = ActuatorExecutor(
        db, connector=connector, allow_actuators=True, allowed_actuator_ids=[ACTUATOR_ID]
    )

    # Execute BEFORE approval → refused, no POST.
    from holdspeak.plugins.actuator_executor import ActuatorExecutionError

    with pytest.raises(ActuatorExecutionError):
        executor.execute(pid)
    assert client.calls == []

    db.actuators.transition_proposal(pid, to_status="approved", actor="karol")
    executed = executor.execute(pid)

    assert executed.status == "executed"
    assert executed.result == {"status": 200, "host": HOOK_HOST}
    assert len(client.calls) == 1
    audit = db.actuators.list_audit(pid)
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]


def test_non_2xx_marks_failed_and_audits(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_webhook_post_actuator(host)
    client = _FakeClient(status=500)
    connector = build_webhook_connector(allowed_hosts=[HOOK_HOST], client=client)

    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(pid)

    assert result.status == "failed"
    assert "HTTP 500" in (result.error or "")
    assert len(client.calls) == 1  # it tried
    audit = db.actuators.list_audit(pid)
    assert audit[-1].to_status == "failed"


def test_transport_error_marks_failed(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_webhook_post_actuator(host)
    client = _FakeClient(raises=True)
    connector = build_webhook_connector(allowed_hosts=[HOOK_HOST], client=client)

    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(pid)
    assert result.status == "failed"
    assert "network down" in (result.error or "")


# ──────────────────────── Config validation ───────────────────────────


def test_config_webhook_hosts_default_empty_and_normalized() -> None:
    assert MeetingConfig().webhook_allowed_hosts == []
    cfg = MeetingConfig(webhook_allowed_hosts=[" A.test ", "a.test", "", "B.test"])
    assert cfg.webhook_allowed_hosts == ["a.test", "b.test"]  # lowercased, deduped


def test_config_webhook_hosts_rejects_non_list() -> None:
    with pytest.raises(ValueError, match="webhook_allowed_hosts"):
        MeetingConfig(webhook_allowed_hosts="hooks.example.test")  # type: ignore[arg-type]


# ──────────────────────── Default set unaffected ──────────────────────


def test_webhook_actuator_not_in_default_builtins() -> None:
    from holdspeak.plugins.builtin import register_builtin_plugins

    host = PluginHost(default_timeout_seconds=1.0)
    registered = register_builtin_plugins(host)
    assert ACTUATOR_ID not in registered  # gated/opt-in, never in the default set
