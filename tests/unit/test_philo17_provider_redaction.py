"""PHILO-17 redact: no credential a CLI or an HTTP service echoes reaches a
ServiceError, a stored row, a send receipt or an MCP tool result.

One family per test: the shared redactor, acli (Jira, Confluence), gh
(provider, actuators), the send channels (gh/acli CLI, email, Slack), the
model providers. Every fake answer carries the same synthetic credentials.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.redaction import redact_error, redact_secrets, redact_source_error

OWNER = Principal(PrincipalKind.OWNER, "test-philo17-redact-owner")

#: Synthetic credentials, one per shape the brief names. The Slack one is
#: built at run time so the repository's push protection does not read it
#: as a real token.
_SLACK = "xox" + "b-123456789012-abcdefghijklmnop"
CREDENTIAL_LINES = (
    "token ghp_AAAAbbbbCCCCddddEEEEffffGGGGhhhh1234",
    "push github_pat_11AAAAAAA0bbbbbbbbbbbb_cccccccccccccccccccccccc",
    "Authorization: Bearer abcDEF0123456789ghijKLMN",
    "Authorization: Basic dXNlcjpodW50ZXIycGFzcw==",
    "curl -H 'Basic Zm9vOmJhcjEyMzQ1Njc4OQ=='",
    "fetch https://octo:hunter2pass@github.com/acme/app.git",
    "GET https://api.example.com/x?token=qwertyuiop123&page=2",
    "config api_key=zxcvbnm0987654321",
    "acli ATATT3xFfGF0abcdefghijklmnopqrstuvwxyz0123456789",
    "openai: Incorrect API key provided: sk-proj-AbCdEf0123456789GhIjKlMnOpQr",
    "slack " + _SLACK,
)
SECRETS = (
    "ghp_AAAA", "github_pat_11AAAA", "abcDEF0123456789", "dXNlcjpodW50ZXIycGFzcw",
    "Zm9vOmJhcjEyMzQ1Njc4OQ", "hunter2pass", "qwertyuiop123", "zxcvbnm0987654321",
    "ATATT3xFfGF0", "sk-proj-AbCdEf", _SLACK[:17],
)
SIGNED_OUT = "✗ Error: unauthorized: use 'acli jira auth login' to authenticate"
STDERR = "\n".join((SIGNED_OUT, *CREDENTIAL_LINES))


def _leaks(value: Any) -> list[str]:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return [secret for secret in SECRETS if secret in text]


def _completed(stderr: str = STDERR, returncode: int = 1, stdout: str = "") -> Any:
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0]) if args else list(kwargs.get("args", []))
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)
    return runner


def _stored_error_details(db: Database) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute("SELECT last_error_detail FROM watch_provider_connections").fetchall()
    return [str(row[0] or "") for row in rows]


# -- the shared redactor -------------------------------------------------

def test_the_shared_redactor_takes_every_shape_and_keeps_the_cause_words() -> None:
    out = redact_error(STDERR)
    assert _leaks(out) == [], out
    assert "acli jira auth login" in out
    assert "To get started with GitHub CLI, please run:  gh auth login" == redact_error(
        "To get started with GitHub CLI, please run:  gh auth login")
    assert redact_secrets("Basic authentication failed") == "Basic authentication failed"
    # Redact first, then cut: a cut never leaves the head of a secret.
    for cap in range(1, len(STDERR), 7):
        assert not any(secret[:8] in redact_error(STDERR, cap) for secret in SECRETS if len(secret) >= 8)
    assert len(redact_source_error("x" * 5000)) == 1000


# -- acli: Jira ----------------------------------------------------------

def test_jira_search_failure_holds_no_secret_in_its_result_or_its_mcp_answer(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.mcp.families import project as family
    from holdspeak.services.jira_provider import JiraProviderAdapter

    switch = "✓ Switched to account: alpha.atlassian.net [user@example.com]"
    status = "✓ Authenticated\n  Site: alpha.atlassian.net\n  Email: user@example.com\n"
    answers = iter([(switch, "", 0), (status, "", 0)])

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        out, err, code = next(answers, ("", STDERR, 1))
        return subprocess.CompletedProcess(list(args[0]), code, stdout=out, stderr=err)

    adapter = JiraProviderAdapter(db=Database(tmp_path / "jira.db"), runner=runner)
    monkeypatch.setattr(family, "_jira_adapter", lambda: adapter)
    result = family.dispatch(
        "provider.jira_search",
        {"connection_ref": "alpha.atlassian.net|user@example.com", "jql": "project = KAN"},
        OWNER,
    )
    assert result["state"] == "failed", result
    assert _leaks(result) == [], result
    assert "acli jira auth login" in result["error_detail"]


def test_jira_connection_failure_is_stored_with_no_secret(tmp_path: Any) -> None:
    from holdspeak.services.jira_provider import JiraProviderAdapter

    db = Database(tmp_path / "jira-conn.db")
    adapter = JiraProviderAdapter(db=db, runner=_completed("switch broke\n" + "\n".join(CREDENTIAL_LINES)))
    result = adapter.connection_status(OWNER, "alpha.atlassian.net|user@example.com")
    assert _leaks(result) == [], result
    stored = _stored_error_details(db)
    assert stored and all(_leaks(value) == [] for value in stored), stored
    assert any("acli auth switch failed" in value for value in stored), stored


# -- acli: Confluence ----------------------------------------------------

def test_confluence_discover_and_connection_hold_no_secret(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.mcp.families import project as family
    from holdspeak.services.confluence_provider import ConfluenceProviderAdapter

    db = Database(tmp_path / "confluence.db")
    adapter = ConfluenceProviderAdapter(db, runner=_completed("switch broke\n" + "\n".join(CREDENTIAL_LINES)))
    monkeypatch.setattr(family, "_confluence_adapter", lambda: adapter)
    result = family.dispatch(
        "provider.confluence_discover", {"connection_ref": "alpha.atlassian.net|user@example.com"}, OWNER,
    )
    assert result["state"] == "failed", result
    assert _leaks(result) == [], result
    status = adapter.connection_status(OWNER, "alpha.atlassian.net|user@example.com")
    assert _leaks(status) == [], status
    stored = _stored_error_details(db)
    assert stored and all(_leaks(value) == [] for value in stored), stored


# -- gh: the provider ----------------------------------------------------

def test_github_discover_and_probe_hold_no_secret(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.mcp.families import project as family
    from holdspeak.services.github_provider import GitHubProviderAdapter

    db = Database(tmp_path / "github.db")
    adapter = GitHubProviderAdapter(db=db, runner=_completed("gh broke\n" + "\n".join(CREDENTIAL_LINES)))
    monkeypatch.setattr(family, "_github_adapter", lambda: adapter)
    result = family.dispatch("provider.github_discover", {}, OWNER)
    assert result["state"] == "failed", result
    assert _leaks(result) == [], result
    probe = family.dispatch("provider.github_connection", {}, OWNER)
    assert _leaks(probe) == [], probe
    stored = _stored_error_details(db)
    assert stored and all(_leaks(value) == [] for value in stored), stored
    assert "gh broke" in stored[0]


def test_the_stored_provider_error_is_redacted_whoever_writes_it(tmp_path: Any) -> None:
    db = Database(tmp_path / "rows.db")
    db.automations.create_provider_connection(
        connection_id="c1", provider_id="github", transport="gh", external_connection_ref="",
        state="degraded", capability_manifest_json="{}", capability_revision="r", discovery_state="unknown",
    )
    db.automations.update_provider_connection("c1", last_error_detail=STDERR)
    assert _leaks(_stored_error_details(db)) == []


# -- gh: the actuators ---------------------------------------------------

def test_github_actuator_failures_raise_no_secret() -> None:
    from holdspeak.plugins.builtin import github_issue_actuator, github_pr_actuator

    failed = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr=STDERR)
    for interpret in (github_pr_actuator._interpret, github_issue_actuator._interpret):
        with pytest.raises(RuntimeError) as caught:
            interpret(failed, None)
        assert _leaks(str(caught.value)) == [], str(caught.value)


# -- the send channels (the receipt row) ---------------------------------

def test_send_channel_receipts_hold_no_secret() -> None:
    from holdspeak.services.channel_contract import CHANNELS, redact

    for line in CREDENTIAL_LINES:
        assert _leaks(redact(line)) == [], (line, redact(line))
    for name in ("github", "jira", "confluence"):
        channel = CHANNELS[name]
        for line in CREDENTIAL_LINES:
            completed = subprocess.CompletedProcess(["x"], 1, stdout="", stderr=f"{name} failed: {line}")
            outcome = channel.interpret(completed, b"the update body", {})
            assert _leaks(outcome.record() or {}) == [], (name, line, outcome)


# -- the model providers -------------------------------------------------

def test_model_provider_errors_hold_no_secret() -> None:
    from holdspeak.intel.parsing import _describe_cloud_exception

    class AuthenticationError(Exception):
        status_code = 401

    text = _describe_cloud_exception(
        AuthenticationError(STDERR), model="gpt", base_url="https://user:hunter2pass@llm.example.com/v1",
    )
    assert text.startswith("Cloud auth failed"), text
    assert _leaks(text) == [], text


# -- the actuator receipt row (every connector: gh, webhook, Slack) ------

def test_a_failed_actuator_stores_and_logs_no_secret(tmp_path: Any, caplog: pytest.LogCaptureFixture) -> None:
    from datetime import datetime

    from holdspeak.meeting_session import MeetingState
    from holdspeak.plugins.actuator_executor import ActuatorExecutor

    db = Database(tmp_path / "exec.db")
    db.meetings.save_meeting(MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[]))
    proposal = db.actuators.record_proposal(
        meeting_id="m1", window_id="w1", plugin_id="followup_ticket_actuator", plugin_version="1.0.0",
        idempotency_key="k1", target="github", action="create_issue", preview="Open a follow-up issue",
        payload={"repo": "acme/app", "title": "Follow up"}, reversible=True, required_capabilities=["actuator"],
    )
    db.actuators.transition_proposal(proposal.id, to_status="approved", actor="karol")

    def connector(_proposal: Any) -> Any:
        raise RuntimeError(STDERR)

    with caplog.at_level("ERROR"):
        result = ActuatorExecutor(db, connector=connector, allow_actuators=True).execute(proposal.id)
    assert result.status == "failed"
    assert _leaks(result.error or "") == [], result.error
    assert "acli jira auth login" in (result.error or "")
    assert _leaks(caplog.text) == [], caplog.text


# -- pipeline_events (agents read them over MCP) -------------------------

def test_pipeline_events_hold_no_secret() -> None:
    from holdspeak.services.observer import _failure, _truncate

    error, _code, _summary = _failure(RuntimeError(STDERR))
    assert _leaks(error or "") == [], error
    assert _leaks(_truncate({"error_detail": STDERR})) == []
    assert _leaks(_truncate({"error_detail": STDERR * 40})) == []


# -- the MCP error answer -------------------------------------------------

def test_an_mcp_error_answer_holds_no_secret_and_stays_json() -> None:
    from holdspeak.mcp.server import _tool_result

    answer = _tool_result({"error": STDERR, "code": "connector_refresh_failed"}, is_error=True)
    body = json.loads(answer["content"][0]["text"])
    assert body["code"] == "connector_refresh_failed"
    assert _leaks(body) == [], body
    assert "acli jira auth login" in body["error"]


# -- the log file ----------------------------------------------------------

def test_the_log_line_and_its_traceback_hold_no_secret() -> None:
    import logging
    import sys

    from holdspeak.logging_config import RedactingFormatter

    try:
        raise RuntimeError(STDERR)
    except RuntimeError:
        record = logging.LogRecord("holdspeak.x", logging.ERROR, __file__, 1, "failed: %s",
                                   ("api_key=zxcvbnm0987654321",), sys.exc_info())
    text = RedactingFormatter("%(message)s").format(record)
    assert "Traceback" in text
    assert _leaks(text) == [], text


# -- the model provider's dictation runtime --------------------------------

def test_the_dictation_runtime_error_holds_no_secret() -> None:
    from holdspeak.plugins.dictation import runtime_openai_compatible as runtime

    class _Completions:
        def create(self, **_kwargs: Any) -> Any:
            raise RuntimeError(STDERR)

    backend = runtime.OpenAICompatibleRuntime.__new__(runtime.OpenAICompatibleRuntime)
    backend._client = type("C", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()
    backend.model = "m"
    backend.load = lambda: None
    with pytest.raises(RuntimeError) as caught:
        backend.rewrite("hello")
    assert _leaks(str(caught.value)) == [], str(caught.value)
