"""The agent CLI engine (Betterment engines E1): argv, prompt, output, process.

Every run uses the fake ``claude``/``codex`` in tests/fixtures/fake_agent_cli.py
on PATH inside the test's temp dir; never the owner's real CLIs.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.intel import cli_engine
from holdspeak.intel.cli_engine import (
    PRESETS,
    CliEngine,
    build_cli_argv,
    cli_endpoint,
    cli_vendor_host,
    messages_to_prompt,
    parse_cli_endpoint,
    parse_cli_output,
)
from holdspeak.kernel.provider_signals import (
    ProviderKnownNoGenerationTransient,
    ProviderPermanentNoGeneration,
)
from tests.fixtures.fake_agent_cli import (
    CLAUDE_ANSWER,
    CLAUDE_COST_USD,
    CODEX_ANSWER,
    calls,
    install_fake_agent_clis,
    path_with,
    process_gone,
    set_mode,
)


@pytest.fixture()
def fake_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = install_fake_agent_clis(tmp_path / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv(cli_engine.CLI_ENGINES_ENV, "on")
    return bin_dir


@pytest.fixture()
def egress(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record each egress the engine asks for, then run its sender (no broker)."""
    seen: list[dict[str, Any]] = []

    def run_external_egress(**kwargs: Any) -> Any:
        seen.append({k: kwargs[k] for k in ("connector_id", "destination", "allowed_destinations", "data_classes")})
        return kwargs["sender"](**kwargs["kwargs"])

    import holdspeak.kernel.external_egress as external_egress

    monkeypatch.setattr(external_egress, "run_external_egress", run_external_egress)
    return seen


def test_claude_argv_has_tools_off_and_no_fixed_spend_cap() -> None:
    argv = build_cli_argv(PRESETS["claude"], executable="/x/claude")
    assert argv[:4] == ["/x/claude", "-p", "--tools", ""]
    assert "--no-session-persistence" in argv and argv[argv.index("--output-format") + 1] == "json"
    assert "--max-budget-usd" not in argv and "0.10" not in argv
    limited = build_cli_argv(PRESETS["claude"], executable="/x/claude", model="sonnet", spend_limit_usd=0.5)
    assert limited[limited.index("--model") + 1] == "sonnet"
    assert limited[limited.index("--max-budget-usd") + 1] == "0.50"


def test_codex_argv_is_read_only_and_keeps_stdin_last() -> None:
    argv = build_cli_argv(PRESETS["codex"], executable="/x/codex", model="gpt-5", spend_limit_usd=2.0)
    assert argv == ["/x/codex", "exec", "--sandbox", "read-only", "--ephemeral", "-m", "gpt-5", "-"]


def test_endpoint_stores_preset_and_limit() -> None:
    assert cli_endpoint("claude") == "cli:claude"
    assert parse_cli_endpoint("cli:claude?spend_limit_usd=0.50") == (PRESETS["claude"], 0.5)
    assert parse_cli_endpoint("cli:codex") == (PRESETS["codex"], None)
    assert parse_cli_endpoint("cli:sh") is None
    assert parse_cli_endpoint("cli:claude?spend_limit_usd=-1") is None
    assert parse_cli_endpoint("https://api.anthropic.com/v1") is None
    assert cli_vendor_host("cli:claude") == "api.anthropic.com"
    assert cli_vendor_host("cli:codex") == "api.openai.com"


def test_typed_job_gets_its_schema_in_the_prompt() -> None:
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    prompt = messages_to_prompt(
        [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Summarize."}],
        {"type": "json_schema", "json_schema": {"name": "r", "schema": schema}},
    )
    assert prompt.startswith("Be brief.\n\nSummarize.")
    assert "Reply with JSON only" in prompt and json.dumps(schema, sort_keys=True) in prompt
    assert "JSON" not in messages_to_prompt([{"role": "user", "content": "Hi"}])


def test_claude_json_gives_text_cost_and_tokens() -> None:
    answer = parse_cli_output(json.dumps({
        "type": "result", "is_error": False, "result": "Four.", "total_cost_usd": 0.02,
        "usage": {"input_tokens": 10, "cache_read_input_tokens": 2, "output_tokens": 3},
    }))
    assert (answer.text, answer.cost_usd) == ("Four.", 0.02)
    assert answer.usage == {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}
    assert parse_cli_output("Plain text.\n").text == "Plain text."
    with pytest.raises(ProviderPermanentNoGeneration):
        parse_cli_output(json.dumps({"type": "result", "is_error": True}))


def test_claude_engine_runs_the_fake_on_stdin_in_an_empty_folder(fake_bin: Path, egress: list) -> None:
    engine = CliEngine.from_endpoint("cli:claude", model="default")
    out = engine.run_prompt(system_prompt="Answer in one word.", user_prompt="Two plus two?")
    assert out == CLAUDE_ANSWER
    (call,) = calls(fake_bin, "claude")
    assert "Two plus two?" in call["prompt"] and "Answer in one word." in call["prompt"]
    assert "Two plus two?" not in " ".join(call["argv"])  # the prompt is on stdin, never in ps
    assert call["cwd_entries"] == [] and "holdspeak-cli-engine-" in call["cwd"]
    assert call["argv"][:3] == ["-p", "--tools", ""] and "--max-budget-usd" not in call["argv"]
    assert egress == [{
        "connector_id": "meeting-intel-cli-agent", "destination": "api.anthropic.com",
        "allowed_destinations": ("api.anthropic.com",), "data_classes": ("model_input",),
    }]
    assert engine.last_cost_usd == CLAUDE_COST_USD
    assert engine.last_usage == {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16}
    assert engine.active_provider == "cli_agent" and engine.active_model == "claude-fake-1"


def test_spend_limit_reaches_the_cli(fake_bin: Path, egress: list) -> None:
    CliEngine.from_endpoint("cli:claude?spend_limit_usd=0.25", model="opus").run_prompt(user_prompt="Hi")
    argv = calls(fake_bin, "claude")[0]["argv"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.25"
    assert argv[argv.index("--model") + 1] == "opus"


def test_stream_is_one_delta_with_the_cost(fake_bin: Path, egress: list) -> None:
    deltas = list(CliEngine.from_endpoint("cli:claude").run_prompt_stream(
        messages=[{"role": "user", "content": "Hi"}],
    ))
    assert [d.kind for d in deltas] == ["text", "usage", "done"]
    assert deltas[0].text == CLAUDE_ANSWER and deltas[1].meta["cost_usd"] == CLAUDE_COST_USD


def test_codex_answers_plain_text(fake_bin: Path, egress: list) -> None:
    engine = CliEngine.from_endpoint("cli:codex")
    assert engine.run_prompt(user_prompt="Hi") == CODEX_ANSWER
    assert calls(fake_bin, "codex")[0]["argv"] == ["exec", "--sandbox", "read-only", "--ephemeral", "-"]
    assert egress[0]["destination"] == "api.openai.com"
    assert engine.last_cost_usd is None


def test_a_cli_past_its_timeout_is_killed(fake_bin: Path, egress: list, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(PRESETS, "claude", dataclasses.replace(PRESETS["claude"], timeout_seconds=3.0))
    set_mode(fake_bin, "claude", "sleep")
    with pytest.raises(ProviderKnownNoGenerationTransient):
        CliEngine.from_endpoint("cli:claude").run_prompt(user_prompt="Hi")
    assert process_gone(calls(fake_bin, "claude")[0]["pid"])


@pytest.mark.parametrize("mode", ["fail", "error"])
def test_a_failed_or_refused_run_is_permanent_no_generation(fake_bin: Path, egress: list, mode: str) -> None:
    set_mode(fake_bin, "claude", mode)
    with pytest.raises(ProviderPermanentNoGeneration):
        CliEngine.from_endpoint("cli:claude").run_prompt(user_prompt="Hi")


def test_switch_off_or_not_installed_runs_nothing(
    fake_bin: Path, egress: list, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv(cli_engine.CLI_ENGINES_ENV, "off")
    with pytest.raises(ProviderPermanentNoGeneration):
        CliEngine.from_endpoint("cli:claude").run_prompt(user_prompt="Hi")
    monkeypatch.setenv(cli_engine.CLI_ENGINES_ENV, "on")
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(ProviderPermanentNoGeneration):
        CliEngine.from_endpoint("cli:claude").run_prompt(user_prompt="Hi")
    assert calls(fake_bin, "claude") == [] and egress == []


def test_target_readiness_reads_the_switch_and_path(fake_bin: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from holdspeak.db.models import ProfileRecord
    from holdspeak.inference_targets import target_from_profile

    profile = ProfileRecord(id="agent-claude", name="Claude Code", kind="cliCommand", base_url="cli:claude", model="default")
    target = target_from_profile(profile)
    assert (target.kind, target.boundary, target.transport, target.engine) == ("cli_engine", "cloud", "subprocess", "cli_v1")
    assert target.ready
    monkeypatch.setenv(cli_engine.CLI_ENGINES_ENV, "off")
    assert target_from_profile(profile).readiness_reason == "Agent engines are off on this hub"
    monkeypatch.setenv(cli_engine.CLI_ENGINES_ENV, "on")
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    assert target_from_profile(profile).readiness_reason == "Claude Code is not installed on this Mac"


def test_the_mcp_tool_adds_an_engine_and_refuses_a_codex_limit(
    fake_bin: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp.families import model_library
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError

    owner = Principal(PrincipalKind.OWNER, "local-owner")
    db = Database(tmp_path / "cli-mcp.db")
    monkeypatch.setattr(model_library, "get_database", lambda: db)
    added = model_library.dispatch("model_library.connect_cli_engine", {"draft": {
        "request_id": "mcp-claude", "profile_id": "agent-claude", "expected_profile_revision": 0, "preset": "claude",
    }}, owner)
    assert added["provider"]["profile_id"] == "agent-claude" and added["provider"]["provider_family"] == "cli_agent"
    assert added["receipt"]["assignments_unchanged"] is True
    with pytest.raises(ServiceError) as refused:
        model_library.dispatch("model_library.connect_cli_engine", {"draft": {
            "request_id": "mcp-codex", "profile_id": "agent-codex", "expected_profile_revision": 0,
            "preset": "codex", "spend_limit_usd": 1.0,
        }}, owner)
    assert refused.value.code == "cli_engine_spend_limit_unsupported"
    with pytest.raises(ServiceError) as unknown:
        model_library.dispatch("model_library.connect_cli_engine", {"draft": {
            "request_id": "mcp-sh", "profile_id": "agent-sh", "expected_profile_revision": 0, "preset": "sh",
        }}, owner)
    assert unknown.value.code == "cli_engine_preset_unknown"
