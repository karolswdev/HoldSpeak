"""Engines, against a real hub: an agent CLI as an engine (Betterment E1).

A real MeetingWebServer (``_boot``: isolated HOME and DB). The rig sets
``HOLDSPEAK_CLI_ENGINES=off``; each test here turns it on and puts the fake
``claude``/``codex`` (tests/fixtures/fake_agent_cli.py) first on PATH. The
owner's real CLIs never run.
"""
from __future__ import annotations

import dataclasses
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import (
    CLAUDE_ANSWER,
    calls,
    install_fake_agent_clis,
    path_with,
    process_gone,
    set_mode,
)

TOKEN = "desk-engines"
FALLBACK_ANSWER = "FALLBACK ENGINE ANSWER"

pytestmark = pytest.mark.timeout(180, method="thread")


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


class _ChatEngine(BaseHTTPRequestHandler):
    """A loopback OpenAI-compatible fallback: /models and one chat answer."""

    def _json(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/").endswith("/models"):
            self._json({"object": "list", "data": [{"id": "stub-fallback", "object": "model"}]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._json({"choices": [{"message": {"role": "assistant", "content": FALLBACK_ANSWER}}]})

    def log_message(self, *_args: Any) -> None:
        return


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


@pytest.fixture()
def fake_bin(hub: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    return bin_dir


@pytest.fixture()
def fallback_engine():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ChatEngine)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _connect_claude(base: str, **extra: Any) -> dict:
    return _ok(base, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-claude", "profile_id": "agent-claude",
        "expected_profile_revision": 0, "preset": "claude", **extra,
    }})


def _assign(base: str, capability: str, entries: list[dict]) -> tuple[int, Any]:
    return _call(base, "POST", "/api/inference/assignments/set", {
        "command_id": f"assign-{capability}", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": capability},
        "entries": entries,
    })


def _entry(connected: dict) -> dict:
    return {
        "profile_id": connected["provider"]["profile_id"],
        "profile_revision": int(connected["provider"]["profile_revision"]),
    }


def test_an_ask_assigned_to_claude_code_returns_the_cli_answer(hub: str, fake_bin: Path) -> None:
    connected = _connect_claude(hub)
    assert connected["provider"]["provider_family"] == "cli_agent", connected
    assert connected["receipt"]["assignments_unchanged"] is True

    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned

    answer = _ok(hub, "POST", "/api/ask", {"prompt": "What is two plus two?"})
    assert answer["output"] == CLAUDE_ANSWER, answer
    assert answer["egress"] == {"scope": "cloud", "host": "api.anthropic.com"}, answer["egress"]
    assert answer["route"]["lamp"] == "cloud" and answer["route"]["fallback"] is False, answer["route"]

    (call,) = calls(fake_bin, "claude")
    assert "What is two plus two?" in call["prompt"]
    assert call["argv"][:3] == ["-p", "--tools", ""]
    assert "--max-budget-usd" not in call["argv"]  # no limit by default (decision #10)
    assert call["cwd_entries"] == []


def test_a_cli_past_its_timeout_is_killed_and_the_chain_falls_back(
    hub: str, fake_bin: Path, fallback_engine: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.intel import cli_engine

    monkeypatch.setitem(
        cli_engine.PRESETS, "claude", dataclasses.replace(cli_engine.PRESETS["claude"], timeout_seconds=4.0),
    )
    set_mode(fake_bin, "claude", "sleep")
    claude = _connect_claude(hub)
    fallback = _ok(hub, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": "define-fallback", "profile_id": "engine-fallback", "expected_profile_revision": 0,
        "label": "Fallback", "provider_family": "openai_compatible", "model": "stub-fallback",
        "endpoint": fallback_engine, "requires_key": False,
    }, "secret": None})
    status, assigned = _assign(hub, "ask.answer", [_entry(claude), _entry(fallback)])
    assert status < 300, assigned

    answer = _ok(hub, "POST", "/api/ask", {"prompt": "Say hello."})
    assert answer["output"] == FALLBACK_ANSWER, answer
    # The retry policy may try the transient leg again before the fallback;
    # every attempt was killed at its timeout.
    attempts = calls(fake_bin, "claude")
    assert attempts, "the CLI never ran"
    assert all(process_gone(call["pid"]) for call in attempts), "a sleeping CLI was not killed"


def test_spend_limit_is_passed_and_speech_work_is_refused(hub: str, fake_bin: Path, fallback_engine: str) -> None:
    connected = _connect_claude(hub, spend_limit_usd=0.5, model="opus")
    status, refused = _assign(hub, "speech.rewrite", [_entry(connected)])
    assert status == 400 and refused.get("code") == "inference_assignment_incompatible", (status, refused)
    # The same job takes an OpenAI-compatible engine: the refusal is the CLI rule.
    endpoint = _ok(hub, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": "define-speech", "profile_id": "engine-speech", "expected_profile_revision": 0,
        "label": "Speech", "provider_family": "openai_compatible", "model": "stub-fallback",
        "endpoint": fallback_engine, "requires_key": False,
    }, "secret": None})
    status, accepted = _assign(hub, "speech.rewrite", [_entry(endpoint)])
    assert status < 300, accepted

    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    _ok(hub, "POST", "/api/ask", {"prompt": "Hi"})
    argv = calls(fake_bin, "claude")[0]["argv"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.50"
    assert argv[argv.index("--model") + 1] == "opus"

    status, codex = _call(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-codex", "profile_id": "agent-codex", "expected_profile_revision": 0,
        "preset": "codex", "spend_limit_usd": 1.0,
    }})
    assert status == 422 and codex.get("code") == "cli_engine_spend_limit_unsupported", (status, codex)


def test_the_rig_switch_keeps_agent_engines_off(hub: str) -> None:
    status, refused = _call(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-off", "profile_id": "agent-claude", "expected_profile_revision": 0, "preset": "claude",
    }})
    assert status == 409 and refused.get("code") == "cli_engines_off", (status, refused)
    # Nothing on this machine's PATH is listed either (Found on this Mac).
    assert _agent_rows(hub) == []


# -- Betterment E2: Found on this Mac, one-press Add, spend and cost ---------


def _only_claude_on_path(bin_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the fake ``claude``: this machine's own CLIs stay off PATH."""
    (bin_dir / "codex").unlink()
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")


def _sign_in_fake_claude(tmp_path: Path) -> None:
    """A stored Claude Code token inside the rig's HOME (presence only is read)."""
    folder = tmp_path / "home" / ".claude"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "fake-token"}}))


def _agent_rows(base: str) -> list[dict]:
    return [e for e in _ok(base, "GET", "/api/concierge/detect")["engines"] if e["kind"] == "agent"]


def test_found_on_this_mac_lists_a_signed_in_claude_and_add_makes_it_an_engine(
    hub: str, fake_bin: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _only_claude_on_path(fake_bin, monkeypatch)
    _sign_in_fake_claude(tmp_path)

    (found,) = _agent_rows(hub)
    assert found["found"] is True and "profileId" not in found, found
    assert (found["name"], found["agentPreset"], found["signedIn"]) == ("Claude Code", "claude", "yes"), found
    assert (found["host"], found["vendor"]) == ("api.anthropic.com", "ANTHROPIC"), found

    _connect_claude(hub)
    (engine,) = _agent_rows(hub)
    assert not engine.get("found"), engine
    assert (engine["profileId"], engine["profileRevision"], engine["state"]) == ("agent-claude", 1, "READY"), engine
    assert (engine["name"], engine["vendor"], engine["signedIn"]) == ("Claude Code", "ANTHROPIC", "yes"), engine
    assert engine["spend"] == {
        "limitUsd": None, "canLimit": True, "reportsCost": True, "todayUsd": 0.0, "weekUsd": 0.0,
    }, engine["spend"]
    # The authority's fits ride on it: speech work is refused, answers are not.
    assert engine["fits"]["speech_recognition"]["state"] != "READY", engine["fits"]


def test_a_sign_in_the_hub_cannot_read_is_found_as_unknown(
    hub: str, fake_bin: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _only_claude_on_path(fake_bin, monkeypatch)
    (found,) = _agent_rows(hub)
    # The rig keeps agent state out: never "no", so the owner may try once.
    assert found["signedIn"] in {"unknown", "not_read"}, found


def test_the_engine_row_sums_the_reported_cost_and_says_not_signed_in(
    hub: str, fake_bin: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.fixtures.fake_agent_cli import CLAUDE_COST_USD

    _only_claude_on_path(fake_bin, monkeypatch)
    _sign_in_fake_claude(tmp_path)
    connected = _connect_claude(hub)
    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    _ok(hub, "POST", "/api/ask", {"prompt": "One"})
    _ok(hub, "POST", "/api/ask", {"prompt": "Two"})
    (engine,) = _agent_rows(hub)
    assert engine["spend"]["todayUsd"] == pytest.approx(2 * CLAUDE_COST_USD), engine["spend"]
    assert engine["spend"]["weekUsd"] == pytest.approx(2 * CLAUDE_COST_USD), engine["spend"]

    set_mode(fake_bin, "claude", "fail")  # "Invalid API key. Please run /login"
    _call(hub, "POST", "/api/ask", {"prompt": "Three"})
    (engine,) = _agent_rows(hub)
    assert (engine["signedIn"], engine["state"]) == ("no", "NOT_SET"), engine

    set_mode(fake_bin, "claude", "answer")
    _ok(hub, "POST", "/api/ask", {"prompt": "Four"})
    (engine,) = _agent_rows(hub)
    assert (engine["signedIn"], engine["state"]) == ("yes", "READY"), engine


def test_a_new_spend_limit_reaches_the_next_run(
    hub: str, fake_bin: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _only_claude_on_path(fake_bin, monkeypatch)
    connected = _connect_claude(hub)
    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    _ok(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "limit-claude", "profile_id": "agent-claude",
        "expected_profile_revision": int(connected["provider"]["profile_revision"]),
        "preset": "claude", "label": "Claude Code", "model": "default", "spend_limit_usd": 0.5,
    }})
    (engine,) = _agent_rows(hub)
    assert engine["spend"]["limitUsd"] == 0.5 and engine["profileRevision"] == 1, engine
    _ok(hub, "POST", "/api/ask", {"prompt": "Hi"})
    argv = calls(fake_bin, "claude")[-1]["argv"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.50", argv
