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
    registry = tmp_path / "acli.yaml"
    registry.write_text(
        'version: 1\ncurrent_profile: "cloud:account"\nprofiles:\n'
        '  - site: beta.atlassian.net\n    cloud_id: cloud\n'
        '    account_id: account\n    email: user@example.com\n',
        encoding="utf-8",
    )
    adapter = JiraProviderAdapter(
        db=db, registry_path=registry,
        runner=_completed("switch broke\n" + "\n".join(CREDENTIAL_LINES)),
    )
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


# == Astra r1 on #1095 ======================================================

#: MUST 1: JSON-quoted labels, single or double quotes, quoted or bare value.
QUOTED_FIELDS = (
    '{"api_key":"qwertyuiop123"}',
    "{'password': 'hunter2pass'}",
    '{"access_token": zxcvbnm0987654321}',
    '{"client_secret" : "ATATT3xFfGF0-short"}',
)
QUOTED_SECRETS = ("qwertyuiop123", "hunter2pass", "zxcvbnm0987654321", "ATATT3xFfGF0-short")


def test_r1_quoted_json_labels_are_redacted_through_the_github_producer(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.mcp.families import project as family
    from holdspeak.services.github_provider import GitHubProviderAdapter

    stderr = "gh broke\n" + "\n".join(QUOTED_FIELDS)
    db = Database(tmp_path / "github-quoted.db")
    adapter = GitHubProviderAdapter(db=db, runner=_completed(stderr))
    monkeypatch.setattr(family, "_github_adapter", lambda: adapter)
    probe = family.dispatch("provider.github_connection", {}, OWNER)
    stored = _stored_error_details(db)
    found = json.dumps([probe, stored])
    assert [s for s in QUOTED_SECRETS if s in found] == [], found
    assert "gh broke" in probe["error_detail"]
    discover = family.dispatch("provider.github_discover", {}, OWNER)
    assert [s for s in QUOTED_SECRETS if s in json.dumps(discover)] == [], discover
    # A count or a flag after a label is not a secret shape the label can hide.
    assert redact_secrets('{"max_tokens": 512}') == '{"max_tokens": 512}'


#: MUST 2: a secret that crosses an old cut boundary.
_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvd25lcjEyMyJ9.c2lnbmF0dXJlMDEyMzQ1Ng"


def _crossing(position: int) -> str:
    """Spaces up to just before ``position``, then a JWT that runs across it
    and a URL password after it. Folding the spaces brings both to the front."""
    return " " * (position - 30) + _JWT + " https://octo:" + "hunter2pass" * 4 + "@github.com"


def test_r1_pipeline_events_redact_before_the_cut() -> None:
    from holdspeak.services.observer import _failure, _truncate

    for text in (_crossing(8192), _crossing(65536)):
        summary = _truncate({"error_detail": text})
        error, _code, _ = _failure(RuntimeError(text))
        for out in (summary, error or ""):
            assert "hunter2pass" not in out and _JWT[:20] not in out, out[:200]


@pytest.mark.parametrize("provider", ["sendgrid", "resend"])
def test_r1_the_email_receipt_redacts_before_the_parser_cut(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, provider: str,
) -> None:
    from holdspeak.services import channel_email

    message = _crossing(500)
    if provider == "sendgrid":
        body = json.dumps({"errors": [{"message": message, "field": None}]}).encode()
        excerpt = "; ".join(m for _f, m in channel_email.sendgrid_errors(body) if m)
        outcome = channel_email.SendGridProvider().interpret(400, {}, body)
    else:
        body = json.dumps({"statusCode": 422, "name": "validation_error", "message": message}).encode()
        excerpt = channel_email.resend_error(body, 422)[1]
        outcome = channel_email.ResendProvider().interpret(422, {}, body)
    for out in (excerpt, json.dumps(outcome.proof)):
        assert "hunter2pass" not in out and _JWT[:20] not in out, out[:300]


#: MUST 3: uvicorn's loggers go through the redactor too.
def test_r1_uvicorn_error_lines_are_redacted() -> None:
    import io
    import logging

    from holdspeak.logging_config import install_log_redaction

    install_log_redaction()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    for name in ("uvicorn.error", "uvicorn.access"):
        target = logging.getLogger(name)
        target.addHandler(handler)
        try:
            try:
                raise RuntimeError(STDERR)
            except RuntimeError:
                target.exception("request failed: %s", "api_key=zxcvbnm0987654321")
        finally:
            target.removeHandler(handler)
    text = stream.getvalue()
    assert "Traceback" in text and "request failed" in text
    assert _leaks(text) == [], text


def test_r1_the_hub_installs_log_redaction_before_uvicorn(monkeypatch: Any) -> None:
    """The real ``MeetingWebServer.start``: when it builds the uvicorn config,
    uvicorn's loggers already carry the redacting filter, and uvicorn is told
    not to install its own logging config."""
    import logging
    from unittest.mock import MagicMock

    from holdspeak import logging_config, web_server

    for name in logging_config._FOREIGN_LOGGERS:
        logging.getLogger(name).removeFilter(logging_config._FILTER)
    seen: dict[str, Any] = {}

    class _Stop(Exception):
        pass

    def _config(app: Any, **kwargs: Any) -> Any:
        seen["filtered"] = logging_config._FILTER in logging.getLogger("uvicorn.error").filters
        seen["log_config"] = kwargs.get("log_config", "unset")
        raise _Stop

    monkeypatch.setattr(web_server.uvicorn, "Config", _config)
    server = web_server.MeetingWebServer(web_server.WebRuntimeCallbacks(
        on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}),
    ))
    try:
        with pytest.raises(_Stop):
            server.start()
    finally:
        for sock in server._listen_sockets or []:
            sock.close()
    assert seen == {"filtered": True, "log_config": None}


#: MUST 4: git stderr in a factory worktree command and its audit row.
def test_r1_factory_worktree_stderr_is_redacted_to_the_receipt(tmp_path: Any) -> None:
    from holdspeak.delivery.factory_launch import execute_worktree_create

    repo = tmp_path / "repo"
    repo.mkdir()
    db = Database(tmp_path / "steer.db")
    stderr = "fatal: unable to access: Authorization: Basic dXNlcjpwYXNz\ncurl -H 'Basic dXNlcjpwYXNz'"
    result = execute_worktree_create(
        {"name": "lane-a", "branch": "lane-a", "repo_path": str(repo), "path": str(tmp_path / "lane-a")},
        runner=lambda argv, cwd=None: subprocess.CompletedProcess(argv, 128, stdout="", stderr=stderr),
        audit=db.steering.record,
    )
    assert result["status"] == "error", result
    assert "dXNlcjpwYXNz" not in result["detail"], result
    rows = db.steering.list(limit=5)
    assert rows and all("dXNlcjpwYXNz" not in json.dumps(row.to_dict() if hasattr(row, "to_dict") else row,
                                                           default=str) for row in rows), rows
    # The steering audit itself, whoever calls it.
    db.steering.record(session_key="s", agent="a", pane_id=None, text="Basic dXNlcjpwYXNz", grounding=[],
                       submit=False, outcome="error", detail="Basic dXNlcjpwYXNz")
    assert "dXNlcjpwYXNz" not in json.dumps([r.to_dict() if hasattr(r, "to_dict") else r
                                             for r in db.steering.list(limit=5)], default=str)


#: P2 5: diagnostics stay.
def test_r1_diagnostics_stay_readable() -> None:
    for text in ("http://127.0.0.1:8080", "connect to http://localhost:11434 refused",
                 "Basic Authentication failed", "BASIC AUTHENTICATION FAILED", "basic authentication failed",
                 "Basic Authorization required"):
        assert redact_secrets(text) == text, text
    assert "dXNlcjpwYXNz" not in redact_secrets("Basic dXNlcjpwYXNz")
    assert "hunter2pass" not in redact_secrets("https://octo:hunter2pass@github.com")


#: P2 6: bounded cost on adversarial input.
def test_r1_adversarial_input_finishes_fast() -> None:
    import logging
    import time

    from holdspeak.logging_config import RedactingFormatter
    from holdspeak.services.observer import _failure, _truncate

    hostile = ("a-" * 100_000)[:200_000]
    record = logging.LogRecord("holdspeak.x", logging.ERROR, __file__, 1, "%s", (hostile,), None)
    for run in (lambda: redact_secrets(hostile), lambda: redact_error(hostile, 500),
                lambda: RedactingFormatter("%(message)s").format(record),
                lambda: _failure(RuntimeError(hostile)), lambda: _truncate({"x": hostile})):
        started = time.perf_counter()
        run()
        assert time.perf_counter() - started < 1.0


# == Astra r2 on #1095 ======================================================

def test_r2_the_observer_redacts_an_escaped_quoted_label_into_the_row(tmp_path: Any) -> None:
    from holdspeak.services.observer import _truncate, observed
    from holdspeak.services.sqlite_observer import SQLiteObserver

    nested = {"error_detail": '{"api_key":"qwertyuiop123"}', "password": "hunter2pass"}
    assert "qwertyuiop123" not in _truncate(nested) and "hunter2pass" not in _truncate(nested)
    assert "qwertyuiop123" not in redact_secrets('{\\"api_key\\":\\"qwertyuiop123\\"}')
    assert "qwertyuiop123" not in redact_secrets('{\\"api_key\\": \\"qwertyuiop123 and more\\"}')

    db = Database(tmp_path / "events.db")

    class Probe:
        _observer = SQLiteObserver(db._connection)

        @observed
        def read(self, principal: Any, query: dict) -> dict:
            return {"error_detail": '{"api_key":"qwertyuiop123"}'}

        @observed
        def fail(self, principal: Any) -> None:
            raise RuntimeError('{"api_key":"qwertyuiop123"} {"token": "zxcvbnm0987654321"}')

    Probe().read(OWNER, {"note": '{"password":"hunter2pass"}'})
    with pytest.raises(RuntimeError):
        Probe().fail(OWNER)
    with db._connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM pipeline_events")]
    assert len(rows) == 2
    dumped = json.dumps(rows, default=str)
    for secret in ("qwertyuiop123", "hunter2pass", "zxcvbnm0987654321"):
        assert secret not in dumped, dumped


def test_r2_long_values_are_never_abandoned(tmp_path: Any) -> None:
    from holdspeak.services.github_provider import GitHubProviderAdapter

    password = "p" * 600
    stderr = f"fatal: https://octo:{password}@github.com/acme/app.git\n" + '{"api_key":          "qwertyuiop123"}'
    db = Database(tmp_path / "gh-long.db")
    probe = GitHubProviderAdapter(db=db, runner=_completed(stderr)).connection_status(OWNER)
    found = json.dumps([probe, _stored_error_details(db)])
    assert "p" * 20 not in found, found[:300]
    assert "qwertyuiop123" not in found, found
    assert "p" * 20 not in redact_secrets(f"https://octo:{password}@x.com")
    assert "qwertyuiop123" not in redact_secrets('"api_key" :           "qwertyuiop123"')


def test_r2_the_64k_cut_never_splits_a_quoted_secret() -> None:
    from holdspeak.redaction import redact_bounded

    witness = " " * 65510 + '{"password":"alpha beta gamma"}'
    out = redact_bounded(witness)
    assert "beta" not in out and "gamma" not in out and "alpha" not in out, out[-200:]
    assert "beta" not in redact_error(witness, 70000)


def test_r2_the_cut_is_linear() -> None:
    import time

    from holdspeak.redaction import redact_bounded

    for hostile in ("a" * 65535 + " " + "tail", " ".join(["a" * 5000] * 40), ("a" * 70000 + " ") * 3):
        started = time.perf_counter()
        redact_bounded(hostile)
        redact_error(hostile, 500)
        assert time.perf_counter() - started < 1.0, len(hostile)
