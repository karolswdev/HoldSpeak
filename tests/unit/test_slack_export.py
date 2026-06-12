"""HS-61-01 — the Slack export engine: message builder, URL rule, connector.

The conditions under test: the message text is deterministic mrkdwn built
from the aftercare digest (it IS the preview AND the wire body); the length
cap truncates visibly, never silently; the URL rule is https-with-a-host
(plain http for loopback only); the connector allow-lists exactly the
configured URL's host, injects the credential in memory only, and refuses a
foreign host before egress.
"""
from __future__ import annotations

import pytest

from holdspeak.config import MeetingConfig
from holdspeak.plugins.actuators import ActuatorProposal
from holdspeak.slack_export import (
    SLACK_TEXT_LIMIT,
    TRUNCATION_NOTICE,
    build_slack_connector,
    slack_message_for,
    slack_webhook_host,
)


def _digest(**overrides):
    base = {
        "meeting_id": "m1",
        "meeting_title": "API design follow-up",
        "meeting_date": "2026-06-11T10:00:00",
        "open_items": {
            "total": 2,
            "by_owner": [
                {
                    "owner": "Priya",
                    "count": 1,
                    "items": [{"task": "Wire the rate limiter", "due": "Friday"}],
                },
                {
                    "owner": None,
                    "count": 1,
                    "items": [{"task": "Pick a name", "due": None}],
                },
            ],
        },
        "decisions": [
            {"decision": "Ship the v2 API", "rationale": "the pilot asked for it"},
        ],
        "since_last_meeting": {
            "previous_meeting": {"title": "API design kickoff"},
            "new_decisions": [{"decision": "Ship the v2 API"}],
            "new_actions": [],
            "closed_actions": [{"task": "Draft the spec"}],
            "changed": True,
        },
        "is_empty": False,
    }
    base.update(overrides)
    return base


# ── the message builder ──────────────────────────────────────────────────────


def test_digest_message_carries_decided_open_and_changed():
    text = slack_message_for(_digest(), "digest")
    assert text.startswith("*API design follow-up* (2026-06-11)")
    assert "*What we decided*" in text
    assert "• Ship the v2 API. Why: the pilot asked for it" in text
    assert "*Still open*" in text
    assert "• Priya: Wire the rate limiter (due Friday)" in text
    assert "• Unassigned: Pick a name" in text
    assert "*Since API design kickoff:* 1 new decision(s), 1 closed since last time" in text


def test_followup_message_is_the_draft_in_mrkdwn():
    text = slack_message_for(_digest(), "followup")
    # The HS-49-04 draft's markdown headers/bullets become mrkdwn.
    assert "*Follow-up: API design follow-up*" in text
    assert "*What we decided*" in text
    assert "• Ship the v2 API" in text
    assert not any(line.startswith(("#", "- ")) for line in text.splitlines())


def test_unknown_kind_raises():
    with pytest.raises(ValueError, match="unknown export kind"):
        slack_message_for(_digest(), "carrier-pigeon")


def test_the_cap_truncates_visibly_never_silently():
    huge = _digest(
        decisions=[
            {"decision": f"Decision number {i} with plenty of words", "rationale": None}
            for i in range(400)
        ]
    )
    text = slack_message_for(huge, "digest")
    assert len(text) <= SLACK_TEXT_LIMIT
    assert text.endswith(TRUNCATION_NOTICE)


def test_short_messages_are_untouched():
    text = slack_message_for(_digest(), "digest")
    assert TRUNCATION_NOTICE not in text


# ── the URL rule (one rule, shared by config + settings) ─────────────────────


@pytest.mark.parametrize(
    "url, host",
    [
        ("https://hooks.slack.com/services/T0/B0/xyz", "hooks.slack.com"),
        ("https://HOOKS.SLACK.COM/services/x", "hooks.slack.com"),
        ("http://127.0.0.1:8901/hook", "127.0.0.1"),
        ("http://localhost:8901/hook", "localhost"),
    ],
)
def test_valid_webhook_urls(url, host):
    assert slack_webhook_host(url) == host


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "http://hooks.slack.com/services/x",  # plain http off-loopback
        "ftp://hooks.slack.com/x",
        "https://",
        "not a url",
    ],
)
def test_invalid_webhook_urls_refused(url):
    with pytest.raises(ValueError):
        slack_webhook_host(url)


def test_config_field_enforces_the_same_rule():
    assert MeetingConfig().slack_webhook_url == ""  # default: invisible
    ok = MeetingConfig(slack_webhook_url=" https://hooks.slack.com/services/x ")
    assert ok.slack_webhook_url == "https://hooks.slack.com/services/x"
    with pytest.raises(ValueError, match="slack_webhook_url"):
        MeetingConfig(slack_webhook_url="http://evil.example/hook")


# ── the connector ────────────────────────────────────────────────────────────

URL = "https://hooks.slack.com/services/T0/B0/xyz"


def _proposal(payload):
    return ActuatorProposal(
        target="slack",
        action="post_message",
        preview="the exact message",
        payload=payload,
        reversible=False,
        required_capabilities=("actuator",),
    )


def test_connector_posts_the_stored_body_to_the_configured_url():
    calls = []

    def fake_client(url, body):
        calls.append((url, body))
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200, body="ok")

    connector = build_slack_connector(URL, client=fake_client)
    result = connector(_proposal({"body": {"text": "the exact message"}}))
    assert result["status"] == 200
    assert result["host"] == "hooks.slack.com"
    assert calls == [(URL, {"text": "the exact message"})]


def test_the_credential_never_rests_on_the_proposal():
    # The stored payload has no URL — the connector joins it in memory only.
    seen = {}

    def fake_client(url, body):
        seen["url"] = url
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200)

    stored = {"body": {"text": "hello"}}
    build_slack_connector(URL, client=fake_client)(_proposal(stored))
    assert "url" not in stored  # the input payload was not mutated
    assert seen["url"] == URL


def test_a_smuggled_foreign_url_is_refused_before_egress():
    # Even if a payload somehow carried its own URL, the connector overwrites
    # it with the configured one — the manifest's host is the only door.
    calls = []

    def fake_client(url, body):
        calls.append(url)
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=200)

    connector = build_slack_connector(URL, client=fake_client)
    connector(_proposal({"url": "https://evil.example/exfil", "body": {"text": "x"}}))
    assert calls == [URL]


def test_the_host_gate_refuses_a_foreign_host_before_egress():
    # The underlying Phase-38 gate is what the Slack connector's manifest
    # rides: a POST planned for a host that is not on the allow-list must be
    # refused with NO client call. (build_slack_connector always injects its
    # own URL, so the gate is reached with a mismatched host only if the
    # wiring is wrong somewhere — this locks the backstop.)
    from holdspeak.plugins.builtin.webhook_post_actuator import build_webhook_connector

    def must_not_post(url, body):  # pragma: no cover - the lock
        pytest.fail("egress happened despite a foreign host")

    inner = build_webhook_connector(allowed_hosts=["127.0.0.1"], client=must_not_post)
    with pytest.raises(Exception):
        inner(_proposal({"url": URL, "body": {"text": "x"}}))


def test_non_2xx_raises_for_the_executor_to_record_failed():
    def failing_client(url, body):
        from holdspeak.plugins.builtin.webhook_post_actuator import WebhookResponse

        return WebhookResponse(status=500, body="boom")

    connector = build_slack_connector(URL, client=failing_client)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        connector(_proposal({"body": {"text": "x"}}))
