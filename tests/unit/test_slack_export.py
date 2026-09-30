"""PHILO-11-02 — legacy aftercare rendering and generic webhook guard.

Slack delivery is now owned by the channel contract. The old Slack proposal
connector and its truncating mrkdwn renderer are absent; the document source
still needs a complete Markdown projection, and the generic companion webhook
keeps its existing URL and host guard.
"""
from __future__ import annotations

import pytest

from holdspeak.slack_export import (
    build_url_webhook_connector,
    document_markdown_for,
    slack_webhook_host,
)


def _digest(**overrides):
    value = {
        "meeting_title": "API design follow-up",
        "meeting_date": "2026-06-11T10:00:00",
        "open_items": {
            "by_owner": [
                {"owner": "Priya", "items": [{"task": "Wire the rate limiter", "due": "Friday"}]},
                {"owner": None, "items": [{"task": "Pick a name", "due": None}]},
            ]
        },
        "decisions": [{"decision": "Ship the v2 API", "rationale": "the pilot asked for it"}],
        "since_last_meeting": {
            "previous_meeting": {"title": "API design kickoff"},
            "new_decisions": [{"decision": "Ship the v2 API"}],
            "new_actions": [],
            "closed_actions": [{"task": "Draft the spec"}],
            "changed": True,
        },
        "is_empty": False,
    }
    value.update(overrides)
    return value


def test_document_projection_keeps_the_complete_aftercare_body():
    text = document_markdown_for(_digest(), "digest")
    assert text.startswith("# API design follow-up\n2026-06-11")
    assert "## What we decided" in text
    assert "- Ship the v2 API. Why: the pilot asked for it" in text
    assert "- Priya: Wire the rate limiter (due Friday)" in text
    assert "- Unassigned: Pick a name" in text
    assert "## Since API design kickoff" in text
    assert "- Draft the spec" in text
    assert "truncated" not in text


def test_followup_projection_is_still_the_real_draft():
    text = document_markdown_for(_digest(), "followup")
    assert "# Follow-up: API design follow-up" in text
    assert "## What we decided" in text
    assert "Ship the v2 API" in text


def test_unknown_document_projection_is_named():
    with pytest.raises(ValueError, match="unknown export kind"):
        document_markdown_for(_digest(), "carrier-pigeon")


@pytest.mark.parametrize(
    "url, host",
    [
        ("https://hooks.slack.com/services/T0/B0/xyz", "hooks.slack.com"),
        ("https://HOOKS.SLACK.COM/services/x", "hooks.slack.com"),
        ("http://127.0.0.1:8901/hook", "127.0.0.1"),
        ("http://localhost:8901/hook", "localhost"),
    ],
)
def test_generic_webhook_url_rule(url, host):
    assert slack_webhook_host(url) == host


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "ftp://hooks.slack.com/x",
        "http://hooks.slack.com/services/x",
        "https://",
        "not a url",
    ],
)
def test_invalid_generic_webhook_urls_are_refused(url):
    with pytest.raises(ValueError):
        slack_webhook_host(url)


def test_old_slack_connector_is_not_exported():
    import holdspeak.slack_export as slack_export

    assert not hasattr(slack_export, "build_slack_connector")


def test_generic_companion_connector_still_has_a_transport_boundary():
    calls = []

    def fake_client(url, body):
        calls.append((url, body))
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200, body="ok")

    from holdspeak.plugins.actuators import ActuatorProposal

    connector = build_url_webhook_connector("https://example.test/hook", client=fake_client)
    result = connector(
        ActuatorProposal(
            target="webhook",
            action="post_message",
            preview="exact",
            payload={"body": {"text": "exact"}},
            reversible=False,
            required_capabilities=("actuator",),
        )
    )
    assert result["status"] == 200
    assert calls == [("https://example.test/hook", {"text": "exact"})]


def _proposal(payload):
    from holdspeak.plugins.actuators import ActuatorProposal

    return ActuatorProposal(
        target="webhook",
        action="post_message",
        preview="the exact message",
        payload=payload,
        reversible=False,
        required_capabilities=("actuator",),
    )


def test_generic_credential_never_rests_on_the_proposal():
    seen = {}

    def fake_client(url, body):
        seen["url"] = url
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200)

    stored = {"body": {"text": "hello"}}
    build_url_webhook_connector("https://example.test/hook", client=fake_client)(_proposal(stored))
    assert "url" not in stored
    assert seen["url"] == "https://example.test/hook"


def test_generic_smuggled_foreign_url_is_overwritten_before_egress():
    calls = []

    def fake_client(url, body):
        calls.append(url)
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200)

    connector = build_url_webhook_connector("https://example.test/hook", client=fake_client)
    connector(_proposal({"url": "https://evil.example/exfil", "body": {"text": "x"}}))
    assert calls == ["https://example.test/hook"]


def test_generic_host_gate_refuses_a_foreign_host_before_egress():
    from holdspeak.plugins.builtin.webhook_post_actuator import build_webhook_connector

    def must_not_post(url, body):
        pytest.fail("egress happened despite a foreign host")

    inner = build_webhook_connector(allowed_hosts=["127.0.0.1"], client=must_not_post)
    with pytest.raises(Exception):
        inner(_proposal({"url": "https://evil.example/exfil", "body": {"text": "x"}}))


def test_generic_non_2xx_is_recordable_as_failed():
    def failing_client(url, body):
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=500, body="boom")

    connector = build_url_webhook_connector("https://example.test/hook", client=failing_client)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        connector(_proposal({"body": {"text": "x"}}))
