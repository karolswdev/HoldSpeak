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
    # Betterment E5 (FOLLOWUPS E1): one attempt, killed at its timeout, then
    # the fallback; a timed-out CLI is not tried a second time.
    attempts = calls(fake_bin, "claude")
    assert len(attempts) == 1, attempts
    assert process_gone(attempts[0]["pid"]), "a sleeping CLI was not killed"


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


def _runs() -> list[tuple]:
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        return [tuple(r) for r in conn.execute(
            "SELECT profile_id, outcome, cost_usd FROM cli_engine_runs ORDER BY id"
        ).fetchall()]


def test_a_run_stopped_at_its_spend_limit_still_counts_its_cost(
    hub: str, fake_bin: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.fixtures.fake_agent_cli import CLAUDE_COST_USD

    _only_claude_on_path(fake_bin, monkeypatch)
    connected = _connect_claude(hub, spend_limit_usd=0.01)
    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    set_mode(fake_bin, "claude", "error")  # error_max_budget_usd, with its cost
    _call(hub, "POST", "/api/ask", {"prompt": "Long question"})
    assert ("library_provider_agent-claude", "failed", pytest.approx(CLAUDE_COST_USD)) in _runs(), _runs()
    (engine,) = _agent_rows(hub)
    assert engine["spend"]["todayUsd"] == pytest.approx(CLAUDE_COST_USD), engine["spend"]


def test_a_codex_run_is_recorded_through_its_json_parser(
    hub: str, fake_bin: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.fixtures.fake_agent_cli import CODEX_ANSWER

    (fake_bin / "claude").unlink()
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    connected = _ok(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-codex", "profile_id": "agent-codex", "expected_profile_revision": 0, "preset": "codex",
    }})
    status, assigned = _assign(hub, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    answer = _ok(hub, "POST", "/api/ask", {"prompt": "Hi"})
    assert answer["output"] == CODEX_ANSWER, answer
    assert "--json" in calls(fake_bin, "codex")[-1]["argv"]
    # Codex reports tokens, not dollars: one answered run, no cost.
    assert _runs() == [("library_provider_agent-codex", "answered", None)], _runs()
    (engine,) = _agent_rows(hub)
    assert engine["spend"]["reportsCost"] is False and engine["spend"]["weekUsd"] == 0.0, engine


def test_a_real_claude_code_stop_on_the_screen_turns_its_engine_row_verified(
    hub: str, fake_bin: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Programs PG21: the real Claude Code capture (tests/fixtures/
    usage_limit_captures.json) through the watcher's tick, then the Engines
    read: Claude Code verified with its stop and reset; Codex documented."""
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from holdspeak.agent_context import screen_watch
    from holdspeak.db import get_database

    capture = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "usage_limit_captures.json").read_text())
    for preset in ("claude", "codex"):
        _ok(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
            "request_id": f"connect-{preset}", "profile_id": f"agent-{preset}",
            "expected_profile_revision": 0, "preset": preset,
        }})
    before = {e["agentPreset"]: e.get("limitNotice") for e in _agent_rows(hub)}
    assert before["claude"]["verified"] is False and before["codex"]["verified"] is False, before

    def runner(argv: list[str]) -> SimpleNamespace:
        out = "" if argv[1] == "display-message" else capture["claude"]["screen"]
        return SimpleNamespace(returncode=0, stdout=out + "\n", stderr="")

    monkeypatch.setenv(screen_watch.SCREEN_RULES_ENV, "on")
    seen = datetime(2026, 10, 19, 13, 17, 36, tzinfo=timezone.utc)
    screen_watch.tick(screen_watch.ScreenStore(), records=[
        {"launch_id": "L1", "state": "launched", "session": "hs-L1", "profile_id": "claude-default"},
    ], sessions=[], db=get_database(), runner=runner, now=seen)

    after = {e["agentPreset"]: e.get("limitNotice") for e in _agent_rows(hub)}
    assert after["claude"] == {
        "verified": True, "notice": "You've hit your weekly limit · resets <date> at <time> (<zone>)",
        "stoppedAt": "2026-10-19T13:17:36Z", "resetsAt": "2026-10-24T08:00:00Z",
    }, after
    assert after["codex"]["verified"] is False, after


# ── Betterment E3: the model picker, one engine for each model ──────────────

# The shape the owner's LAN llama.cpp server really answers on /v1/models
# (read 2026-10-18 from 192.168.1.43:8080; trimmed): the context is meta.n_ctx.
_SERVED = [
    {"id": "alpha-7b", "object": "model", "owned_by": "llamacpp", "meta": {"n_ctx": 49152, "n_ctx_train": 262144}},
    {"id": "beta-13b", "object": "model", "owned_by": "llamacpp", "meta": {"n_ctx": 32768}},
    {"id": "gamma-3b", "object": "model", "owned_by": "llamacpp"},
]
PICKED_ANSWER = "ANSWER FROM THE PICKED MODEL"


class _ThreeModels(_ChatEngine):
    """One host, three models; the chat answer names the model it was asked for."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/").endswith("/models"):
            self._json({"object": "list", "data": _SERVED})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        self._json({"choices": [{"message": {"role": "assistant", "content": f"{PICKED_ANSWER} {body.get('model')}"}}]})


@pytest.fixture()
def three_models():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ThreeModels)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _define(base: str, url: str, profile_id: str, model: str, **extra: Any) -> tuple[int, Any]:
    return _call(base, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": f"define-{profile_id}", "profile_id": profile_id, "expected_profile_revision": 0,
        "label": url.split("//")[1].split("/")[0], "provider_family": "openai_compatible",
        "model": model, "endpoint": url, "requires_key": False, **extra,
    }, "secret": None})


def _profile_context(profile_id: str) -> tuple[int, list[int]]:
    from holdspeak.db import get_database

    target = f"library_provider_{profile_id}"
    with get_database()._connection() as conn:
        limit = conn.execute("SELECT context_limit FROM profiles WHERE id=?", (target,)).fetchone()[0]
        ceilings = [int(r[0]) for r in conn.execute(
            "SELECT context_ceiling FROM inference_deployments WHERE destination_id=?", (target,)
        ).fetchall()]
    return int(limit), ceilings


def test_check_lists_three_models_and_two_of_them_become_two_engines(hub: str, three_models: str) -> None:
    status, checked = _call(hub, "POST", "/api/setup/discover-models", {"base_url": three_models, "check_tools": True})
    assert status == 200, checked
    assert checked["models"] == ["alpha-7b", "beta-13b", "gamma-3b"]
    # The server's own context, by model; a model that does not say has none.
    assert checked["contexts"] == {"alpha-7b": 49152, "beta-13b": 32768}

    port = three_models.split(":")[2].split("/")[0]
    alpha, beta = f"engine-127-0-0-1-{port}-alpha-7b", f"engine-127-0-0-1-{port}-beta-13b"
    status, added_alpha = _define(hub, three_models, alpha, "alpha-7b", context_tokens=49152)
    assert status == 200, added_alpha
    status, added_beta = _define(hub, three_models, beta, "beta-13b", context_tokens=32768)
    assert status == 200, added_beta
    assert {added_alpha["provider"]["profile_id"], added_beta["provider"]["profile_id"]} == {alpha, beta}

    rows = _ok(hub, "GET", "/api/concierge/detect")["engines"]
    mine = {r["profileId"]: r for r in rows if r.get("profileId") in {alpha, beta}}
    assert set(mine) == {alpha, beta}, rows
    # Each engine is named by its own model, not by the first model served.
    assert mine[alpha]["name"] != mine[beta]["name"], (mine[alpha]["name"], mine[beta]["name"])

    # The context the Check read is stored on the profile and its deployment.
    assert _profile_context(alpha) == (49152, [49152])
    assert _profile_context(beta) == (32768, [32768])

    # And a job runs on the model he picked, with the real context in its route.
    status, assigned = _assign(hub, "ask.answer", [_entry(added_beta)])
    assert status < 300, assigned
    answer = _ok(hub, "POST", "/api/ask", {"prompt": "Which model are you?"})
    assert answer["output"] == f"{PICKED_ANSWER} beta-13b", answer
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        support = json.loads(conn.execute(
            "SELECT context_support_json FROM inference_route_plan_entries ORDER BY rowid DESC LIMIT 1"
        ).fetchone()[0])
    assert support["maximum_tokens"] == 32768, support


def test_an_old_host_only_engine_still_loads_and_runs(hub: str, three_models: str) -> None:
    # Before E3 the face minted the id from host and port only, and sent no context.
    port = three_models.split(":")[2].split("/")[0]
    legacy = f"engine-127-0-0-1-{port}"
    status, added = _define(hub, three_models, legacy, "alpha-7b")
    assert status == 200, added
    assert _profile_context(legacy) == (16384, [16384])

    rows = _ok(hub, "GET", "/api/concierge/detect")["engines"]
    assert [r["profileId"] for r in rows if r.get("profileId") == legacy] == [legacy], rows
    status, assigned = _assign(hub, "ask.answer", [_entry(added)])
    assert status < 300, assigned
    answer = _ok(hub, "POST", "/api/ask", {"prompt": "Still here?"})
    assert answer["output"] == f"{PICKED_ANSWER} alpha-7b", answer


def test_re_adding_an_engine_takes_the_context_its_check_read(hub: str, three_models: str) -> None:
    """Betterment E6 (FOLLOWUPS E3): an engine first added with no context
    (16,384) and added again after a Check that read 49,152 runs at 49,152.
    It kept its first context before: the deployment was reused."""
    port = three_models.split(":")[2].split("/")[0]
    profile = f"engine-127-0-0-1-{port}-alpha-7b"
    status, first = _define(hub, three_models, profile, "alpha-7b")
    assert status == 200, first
    assert _profile_context(profile) == (16384, [16384])
    revision = int(first["provider"]["profile_revision"])
    status, again = _call(hub, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": f"define-again-{profile}", "profile_id": profile, "expected_profile_revision": revision,
        "label": three_models.split("//")[1].split("/")[0], "provider_family": "openai_compatible",
        "model": "alpha-7b", "endpoint": three_models, "requires_key": False, "context_tokens": 49152,
    }, "secret": None})
    assert status == 200, again
    limit, ceilings = _profile_context(profile)
    assert limit == 49152
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        bound = conn.execute(
            "SELECT d.context_ceiling FROM inference_deployments d JOIN model_profile_binding_revisions b "
            "ON b.deployment_head_id=d.deployment_id WHERE b.binding_id=? ORDER BY b.revision DESC LIMIT 1",
            (f"binding-{profile}",)
        ).fetchone()
    assert bound is not None and int(bound[0]) == 49152, (bound, ceilings)
    # The same Check again changes nothing.
    status, same = _call(hub, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": f"define-same-{profile}", "profile_id": profile,
        "expected_profile_revision": int(again["provider"]["profile_revision"]),
        "label": three_models.split("//")[1].split("/")[0], "provider_family": "openai_compatible",
        "model": "alpha-7b", "endpoint": three_models, "requires_key": False, "context_tokens": 49152,
    }, "secret": None})
    assert status == 200, same
    assert _profile_context(profile)[1] == ceilings


@pytest.mark.parametrize("bad", [0, 100, "49152", 1.5, True, 20_000_000])
def test_a_junk_context_size_is_refused(hub: str, three_models: str, bad: Any) -> None:
    status, refused = _define(hub, three_models, "engine-junk", "alpha-7b", context_tokens=bad)
    assert status == 400, refused


# ── Betterment E4: Add an engine, by kind ───────────────────────────────────

# The shape OpenRouter answers on /api/v1/models (trimmed): the context is
# `context_length`. The first two are catalog preset models.
_OPENROUTER = [
    {"id": "qwen/qwen3-8b", "name": "Qwen: Qwen3 8B", "context_length": 131072},
    {"id": "qwen/qwen3.5-35b-a3b", "name": "Qwen: Qwen3.5 35B A3B", "context_length": 262144},
    {"id": "anthropic/claude-x", "name": "Anthropic: Claude X", "context_length": 200000},
]
OPENROUTER_KEY = "sk-or-stub-key"


class _StubOpenRouter(_ChatEngine):
    """A stub OpenRouter: it lists models only for its key, and answers chat
    with the model it was asked for. Nothing leaves this machine."""

    def _keyed(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {OPENROUTER_KEY}"

    def do_GET(self) -> None:  # noqa: N802
        if not self._keyed():
            self.send_response(401)
            self.end_headers()
        elif self.path.rstrip("/").endswith("/api/v1/models"):
            self._json({"data": _OPENROUTER})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if not self._keyed():
            self.send_response(401)
            self.end_headers()
            return
        self._json({"choices": [{"message": {"role": "assistant", "content": f"{PICKED_ANSWER} {body.get('model')}"}}]})


@pytest.fixture()
def stub_openrouter(monkeypatch: pytest.MonkeyPatch):
    """The OpenRouter tile points at the stub (the rig's only change)."""
    from holdspeak.services import concierge_service

    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubOpenRouter)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/api/v1"
    monkeypatch.setattr(concierge_service, "SERVICE_TILES", tuple(
        {**tile, "baseUrl": url} if tile["id"] == "openrouter" else tile for tile in concierge_service.SERVICE_TILES
    ))
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()


def test_detect_names_the_four_services_with_their_addresses_and_presets(hub: str) -> None:
    detected = _ok(hub, "GET", "/api/concierge/detect")
    tiles = {tile["id"]: tile for tile in detected["services"]}
    assert [tile["name"] for tile in detected["services"]] == ["OpenRouter", "OpenAI", "Anthropic", "Gemini"]
    assert tiles["openrouter"]["baseUrl"] == "https://openrouter.ai/api/v1"
    assert tiles["openai"]["baseUrl"] == "https://api.openai.com/v1"
    assert tiles["anthropic"]["baseUrl"] == "https://api.anthropic.com/v1"
    assert tiles["gemini"]["baseUrl"] == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert tiles["anthropic"]["host"] == "api.anthropic.com"
    # The six signed catalog presets are OpenRouter's; the face shows them on top.
    presets = tiles["openrouter"]["presets"]
    assert len(presets) == 6, presets
    assert presets[0] == {
        "id": "preset_openrouter_qwen3_8b", "label": "OpenRouter · Quick Qwen",
        "summary": "A small, fast Qwen for short Notes and everyday work.",
        "model": "qwen/qwen3-8b", "contextTokens": 131072,
    }
    assert all(not tiles[name]["presets"] for name in ("openai", "anthropic", "gemini"))
    # The rig switch is off: no agent is on this Mac, and each one says how to get it.
    agents = {agent["preset"]: agent for agent in detected["agents"]}
    assert set(agents) == {"claude", "codex", "pi", "gemini"}
    assert agents["claude"] == {
        "preset": "claude", "name": "Claude Code", "vendor": "ANTHROPIC", "vendorScope": "cloud",
        "installed": False, "added": False, "install": "npm install -g @anthropic-ai/claude-code",
    }
    assert agents["gemini"]["install"] == "npm install -g @google/gemini-cli"


def test_the_agent_tile_says_installed_then_added(hub: str, fake_bin: Path) -> None:
    agents = {a["preset"]: a for a in _ok(hub, "GET", "/api/concierge/detect")["agents"]}
    assert agents["claude"]["installed"] is True and agents["claude"]["added"] is False
    _connect_claude(hub)
    agents = {a["preset"]: a for a in _ok(hub, "GET", "/api/concierge/detect")["agents"]}
    assert agents["claude"]["added"] is True and agents["codex"]["added"] is False


def test_openrouter_with_a_chosen_model_runs_with_no_address_typed(hub: str, stub_openrouter: str) -> None:
    """The face's five presses on the hub: the tile's address, Check with the
    pasted key, Use on the chosen model; then a job runs on that model."""
    tile = next(t for t in _ok(hub, "GET", "/api/concierge/detect")["services"] if t["id"] == "openrouter")
    url = tile["baseUrl"]
    assert url == stub_openrouter
    status, checked = _call(hub, "POST", "/api/setup/discover-models", {
        "base_url": url, "api_key": OPENROUTER_KEY, "check_tools": True,
    })
    assert status == 200 and checked["ok"] is True, checked
    assert checked["models"] == ["anthropic/claude-x", "qwen/qwen3-8b", "qwen/qwen3.5-35b-a3b"]
    assert checked["contexts"]["qwen/qwen3.5-35b-a3b"] == 262144

    port = url.split(":")[2].split("/")[0]
    profile_id = f"engine-127-0-0-1-{port}-qwen-qwen3-5-35b-a3b"
    added = _ok(hub, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": "openrouter-use", "profile_id": profile_id, "expected_profile_revision": 0,
        "label": "OpenRouter", "provider_family": "openai_compatible", "model": "qwen/qwen3.5-35b-a3b",
        "endpoint": url, "requires_key": True, "context_tokens": 262144,
    }, "secret": {"value": OPENROUTER_KEY}})
    status, assigned = _assign(hub, "ask.answer", [_entry(added)])
    assert status < 300, assigned
    answer = _ok(hub, "POST", "/api/ask", {"prompt": "Which model are you?"})
    assert answer["output"] == f"{PICKED_ANSWER} qwen/qwen3.5-35b-a3b", answer


def test_an_anthropic_engine_is_no_dead_end(hub: str) -> None:
    """DECISIONS #9: an Anthropic profile reads as a service (NOT_SET with no
    key), never NOT_SUPPORTED."""
    from holdspeak.db import get_database

    get_database().profiles.upsert(profile_id="cloud-anthropic", name="Anthropic", kind="openAICompatible",
                                   base_url="https://api.anthropic.com/v1", model="claude-x", requires_key=True)
    rows = _ok(hub, "GET", "/api/concierge/detect")["engines"]
    claude = next(r for r in rows if r.get("legacyLabel") == "Anthropic")
    assert claude["state"] == "NOT_SET", claude

# ── Betterment E5: What runs where ──────────────────────────────────────────

def _editor(base: str, scope: dict, capability: str) -> dict:
    return _ok(base, "POST", "/api/inference/assignments/editor", {"scope": scope, "capability_id": capability})


def _define_fallback(base: str, url: str) -> dict:
    return _ok(base, "POST", "/api/inference/model-library/define-endpoint", {"draft": {
        "request_id": "define-what", "profile_id": "engine-what", "expected_profile_revision": 0,
        "label": "Stub", "provider_family": "openai_compatible", "model": "stub-fallback",
        "endpoint": url, "requires_key": False,
    }, "secret": None})


def test_a_single_job_is_set_with_a_capability_scope_and_read_back(hub: str, fallback_engine: str) -> None:
    """The face's row write: `capability:<cap>`; the editor reads it back as
    the row's own engine, and a sibling job still reads Everything else."""
    engine = _define_fallback(hub, fallback_engine)
    scope = {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
    before = _editor(hub, scope, "meeting.deferred_analysis")
    assert before["configured_assignment"] is None
    assert any(c["profile_id"] == "engine-what" for c in before["candidates"]), before["candidates"]
    status, written = _call(hub, "POST", "/api/inference/assignments/set", {
        "command_id": "what-summaries", "expected_revision": before["draft_base_revision"],
        "scope": scope, "entries": [_entry(engine)],
    })
    assert status < 300, written
    after = _editor(hub, scope, "meeting.deferred_analysis")
    assert after["configured_assignment"]["entries"][0]["profile_id"] == "engine-what"
    assert after["effective"]["inherited_from"] == "capability"
    live = _editor(hub, {"kind": "capability", "capability_id": "meeting.live_analysis"}, "meeting.live_analysis")
    assert live["configured_assignment"] is None and live["effective"]["status"] == "no_assignment", live["effective"]


def test_meeting_plugins_follow_the_summarys_engine(hub: str, fallback_engine: str) -> None:
    """FOLLOWUPS C4: with only Meeting summaries set, a plugin is no longer
    skipped as no_assignment; it runs on the summary's engine."""
    from holdspeak.inference_capabilities import installed_meeting_plugin_capability_definitions

    plugin = installed_meeting_plugin_capability_definitions()[0].id
    engine = _define_fallback(hub, fallback_engine)
    status, written = _assign(hub, "meeting.deferred_analysis", [_entry(engine)])
    assert status < 300, written
    effective = _editor(hub, {"kind": "capability", "capability_id": plugin}, plugin)["effective"]
    assert effective["status"] == "assigned", effective
    assert effective["inherited_from"] == "capability"
    assert effective["assignment"]["entries"][0]["profile_id"] == "engine-what"


def test_speech_never_takes_the_default_chat_engine(hub: str, fallback_engine: str) -> None:
    """FOLLOWUPS ST0: with Everything else on a chat server and no speech
    row, speech has no engine; it never routes to the chat server."""
    engine = _define_fallback(hub, fallback_engine)
    status, written = _call(hub, "POST", "/api/inference/assignments/set", {
        "command_id": "what-global", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [_entry(engine)],
    })
    assert status < 300, written
    speech = _editor(hub, {"kind": "group", "group_id": "speech_recognition"}, "speech.transcribe")
    # The rig hub has its own speech row (the built-in Whisper); with none,
    # speech has no engine (tests/unit/test_what_runs_where_resolve.py).
    assert speech["effective"].get("inherited_from") != "global", speech["effective"]
    assert all(e["profile_id"] != "engine-what" for e in (speech["effective"].get("assignment") or {}).get("entries", []))
    # And the speech picker lists no chat engine.
    assert not any(c["profile_id"] == "engine-what" for c in speech["candidates"]), speech["candidates"]
    # A text job still follows Everything else.
    answers = _editor(hub, {"kind": "capability", "capability_id": "ask.answer"}, "ask.answer")
    assert answers["effective"]["inherited_from"] == "global"


def test_speech_lists_no_agent(hub: str, fake_bin: Path) -> None:
    _connect_claude(hub)
    speech = _editor(hub, {"kind": "group", "group_id": "speech_recognition"}, "speech.transcribe")
    assert not any(c["profile_id"].endswith("agent-claude") for c in speech["candidates"]), speech["candidates"]


def test_speech_with_no_row_reads_no_engine_for_speech_on_every_face(hub: str, fallback_engine: str) -> None:
    """Betterment E6 (FOLLOWUPS E5): with no speech row, speech reads
    `no_assignment` (E5; was `no_compatible_assignment`). Each face that words
    it says "no engine for speech", never a broken or incompatible engine."""
    engine = _define_fallback(hub, fallback_engine)
    status, written = _call(hub, "POST", "/api/inference/assignments/set", {
        "command_id": "speech-global", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [_entry(engine)],
    })
    assert status < 300, written
    # The rig hub has its own speech rows (the built-in Whisper): clear them.
    for n, scope in enumerate(({"kind": "capability", "capability_id": "speech.transcribe"},
                               {"kind": "group", "group_id": "speech_recognition"})):
        speech = _editor(hub, scope, "speech.transcribe")
        if speech["configured_assignment"] is not None:
            _ok(hub, "POST", "/api/inference/assignments/clear", {
                "command_id": f"speech-clear-{n}", "expected_revision": speech["draft_base_revision"],
                "scope": scope, "capability_id": "speech.transcribe",
            })
    # The roster (the Chair, Needs you and the Engines window read it).
    roster = _ok(hub, "GET", "/api/inference/assignments")
    task = next(t for t in roster["task_overrides"] if t["id"] == "speech.transcribe")
    assert task["effective"]["status"] == "no_assignment", task["effective"]
    # Needs you: the meeting-path row says it in words.
    needs = _ok(hub, "GET", "/api/desk/needs-you?fresh=1")
    labels = json.dumps(needs)
    assert "No engine for speech" in labels, labels[:2000]
    assert "incompatible" not in labels.lower()

# ── Betterment E7: pi and Gemini CLI ────────────────────────────────────────

from tests.fixtures.fake_agent_cli import GEMINI_ANSWER, PI_ANSWER  # noqa: E402


@pytest.fixture()
def more_bin(hub: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin", names=("pi", "gemini"))
    # Only the fakes: this machine's own CLIs stay off PATH.
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    return bin_dir


def _pi_config(tmp_path: Path) -> None:
    """pi's own config inside the rig's HOME: a LAN provider (no key read)."""
    agent = tmp_path / "home" / ".pi" / "agent"
    agent.mkdir(parents=True, exist_ok=True)
    (agent / "models.json").write_text(json.dumps({"providers": {"lan-qwen": {
        "baseUrl": "http://192.168.1.43:8080/v1", "apiKey": "local", "models": [{"id": "qwen3.8-27b"}],
    }}}))
    (agent / "settings.json").write_text(json.dumps({"defaultProvider": "lan-qwen", "defaultModel": "qwen3.8-27b"}))


def _connect(base: str, preset: str, **extra: Any) -> dict:
    return _ok(base, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": f"connect-{preset}", "profile_id": f"agent-{preset}",
        "expected_profile_revision": 0, "preset": preset, **extra,
    }})


def _try(base: str, connected: dict) -> dict:
    """Try it under Answers: the hub's sample on the engine (the face's probe)."""
    status, assigned = _assign(base, "ask.answer", [_entry(connected)])
    assert status < 300, assigned
    return _ok(base, "POST", "/api/concierge/probe", {
        "task": True, "capabilityId": "ask.answer", "confirmOffMachine": True,
        "expectedProfileIds": [connected["provider"]["profile_id"]],
    })


def test_pi_and_gemini_are_found_when_installed_and_named_by_their_egress(
    hub: str, more_bin: Path, tmp_path: Path,
) -> None:
    _pi_config(tmp_path)
    found = {row["agentPreset"]: row for row in _agent_rows(hub)}
    assert set(found) == {"pi", "gemini"}, found
    assert found["gemini"]["name"] == "Gemini CLI" and found["gemini"]["vendor"] == "GOOGLE"
    assert found["gemini"]["vendorScope"] == "cloud"
    # pi's config sends its default model to the LAN box: that is the chip.
    assert (found["pi"]["host"], found["pi"]["vendorScope"]) == ("192.168.1.43", "private_network"), found["pi"]
    # The sign-in of either cannot be read: try once.
    assert found["pi"]["signedIn"] == "unknown" and found["gemini"]["signedIn"] == "unknown"


def test_pi_on_his_lan_model_answers_try_it_on_his_network(hub: str, more_bin: Path, tmp_path: Path) -> None:
    _pi_config(tmp_path)
    connected = _connect(hub, "pi", model="lan-qwen/qwen3.8-27b")
    (engine,) = [row for row in _agent_rows(hub) if row.get("profileId") == "agent-pi"]
    assert (engine["state"], engine["host"], engine["vendorScope"]) == ("READY", "192.168.1.43", "private_network")
    answer = _try(hub, connected)
    assert answer["ok"] is True and answer["state"] == "READY", answer
    assert answer["sampleOutput"] == PI_ANSWER
    assert answer["boundary"] == "private_network" and answer["host"] == "192.168.1.43", answer
    (call,) = calls(more_bin, "pi")
    assert call["argv"][:2] == ["--print", "--no-tools"] and "lan-qwen/qwen3.8-27b" in call["argv"]
    assert "What is 2 + 2?" in call["prompt"]


def test_the_owner_names_pis_host_and_only_pi_takes_one(hub: str, more_bin: Path) -> None:
    _connect(hub, "pi", egress_host="192.168.1.50")
    (engine,) = [row for row in _agent_rows(hub) if row.get("profileId") == "agent-pi"]
    assert engine["host"] == "192.168.1.50" and engine["vendorScope"] == "private_network"
    status, refused = _call(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-gemini-host", "profile_id": "agent-gemini", "expected_profile_revision": 0,
        "preset": "gemini", "egress_host": "192.168.1.50",
    }})
    assert status == 400 and refused["code"] == "cli_engine_host_invalid", refused


def test_gemini_answers_try_it_through_google(hub: str, more_bin: Path) -> None:
    connected = _connect(hub, "gemini")
    answer = _try(hub, connected)
    assert answer["ok"] is True and answer["sampleOutput"] == GEMINI_ANSWER, answer
    assert answer["boundary"] == "cloud" and answer["host"].upper() == "GENERATIVELANGUAGE.GOOGLEAPIS.COM", answer
    (call,) = calls(more_bin, "gemini")
    assert "--output-format" in call["argv"] and "What is 2 + 2?" in call["prompt"]
