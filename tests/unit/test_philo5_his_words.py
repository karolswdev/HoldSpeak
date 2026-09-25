"""Structural fences for the PHILO-5-04 ordinary-language rehearsal driver."""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo5_his_words", REPO / "scripts/philo5_his_words.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)


def test_owner_prompts_have_no_operation_tool_or_clock_names() -> None:
    for prompt in driver.PROMPTS.values():
        assert driver._ordinary_language_fence(prompt) == []
    assert driver.PROMPTS["tomorrow_brief"] == "Now it is tomorrow. Make my brief and tell me what is on it."


@pytest.mark.parametrize(
    "injected",
    [
        "Please call meeting.import with the recording.",
        "Use clock.python_wall and advance_days=1.",
        "Use monday_brief.generate now.",
    ],
)
def test_prompt_fence_turns_red_for_technical_instructions(injected: str) -> None:
    found = driver._ordinary_language_fence(injected)
    assert found


@pytest.mark.parametrize(
    "injected",
    [
        "Use the date 2026-09-24 in the request.",
        "Set the clock to evening before you run.",
        "Apply an offset of one day.",
        "Pass meeting_id=meeting-1.",
    ],
)
def test_prompt_fence_rejects_dates_offsets_and_argument_keys(injected: str) -> None:
    assert driver._ordinary_language_fence(injected)


class _TranscriptHub:
    def __init__(self, home: Path, transcript_path: Path) -> None:
        self.home = home
        self.transcript_path = transcript_path


def _mcp_exchange(
    *,
    request_id: int,
    tool: str,
    arguments: dict[str, object],
    result: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    return request, {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _mint_transcript(tmp_path: Path) -> tuple[Path, _TranscriptHub]:
    stage = tmp_path / "codex" / "turn"
    stage.mkdir(parents=True)
    successful_result = {
        "content": [{"type": "text", "text": "created"}],
        "structured_content": None,
    }
    refused_result = {
        "content": [{"type": "text", "text": "refused"}],
        "structured_content": None,
        "isError": True,
    }
    requests: list[tuple[dict[str, object], dict[str, object], str, dict[str, object], dict[str, object]]] = []
    for request_id, tool, arguments, result in (
        (1, "meeting.import", {"filename": "/tmp/meeting.wav"}, successful_result),
        (2, "meeting.run_intelligence", {"meeting_id": "meeting-1"}, refused_result),
    ):
        request, response = _mcp_exchange(
            request_id=request_id, tool=tool, arguments=arguments, result=result,
        )
        requests.append((request, response, tool, arguments, result))
    events = [
        {
            "type": "item.completed",
            "item": {
                "id": f"item-{request_id}",
                "type": "mcp_tool_call",
                "server": "holdspeak",
                "tool": tool,
                "arguments": arguments,
                "result": result,
                "error": None,
                "status": "completed",
            },
        }
        for request_id, (_request, _response, tool, arguments, result) in enumerate(requests, 1)
    ]
    (stage / "events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events)
    )
    transcript = tmp_path / "rehearsal-transcript.jsonl"
    transcript.write_text(
        "".join(
            json.dumps({
                "method": "POST",
                "path": "/api/mcp",
                "status": 200,
                "request_body": request,
                "response_body": response,
            }) + "\n"
            for request, response, _tool, _arguments, _result in requests
        )
    )
    return stage, _TranscriptHub(tmp_path / "hub-home", transcript)


def test_reconcile_accepts_success_and_refused_mcp_calls(tmp_path: Path) -> None:
    stage, hub = _mint_transcript(tmp_path)
    calls = driver._codex_mcp_calls(stage)
    assert len(calls) == 2
    assert any(call["result"].get("isError") for call in calls)

    audit = driver._reconcile_mcp_calls(stage, hub, 0)
    assert audit["codex_calls"] == 2
    assert len(audit["matches"]) == 2
    assert audit["unmatched_turn_exchanges"] == []


def test_canonical_result_projection_preserves_content_and_errors() -> None:
    codex = {
        "content": [{"type": "text", "text": "kept"}],
        "structured_content": {"id": "one"},
    }
    server = {
        "content": [{"type": "text", "text": "kept"}],
        "structuredContent": {"id": "one"},
        "isError": False,
    }
    assert driver._canonical_mcp_result(codex) == driver._canonical_mcp_result(server)

    refused = driver._canonical_mcp_result({"error": {"code": "denied"}})
    assert refused["isError"] is True
    assert refused["error"]["code"] == "denied"


@pytest.mark.parametrize("mutation", ["tool", "arguments", "result"])
def test_reconcile_rejects_client_server_mutations(tmp_path: Path, mutation: str) -> None:
    stage, hub = _mint_transcript(tmp_path)
    rows = [json.loads(line) for line in hub.transcript_path.read_text().splitlines()]
    if mutation == "tool":
        rows[0]["request_body"]["params"]["name"] = "desk.create"
    elif mutation == "arguments":
        rows[0]["request_body"]["params"]["arguments"] = {"filename": "/tmp/other.wav"}
    else:
        rows[0]["response_body"]["result"]["content"][0]["text"] = "changed"
    hub.transcript_path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    with pytest.raises(RuntimeError, match="no unused matching"):
        driver._reconcile_mcp_calls(stage, hub, 0)


def test_audit_rejects_hub_file_shell_mutation(tmp_path: Path) -> None:
    stage, hub = _mint_transcript(tmp_path)
    events = [json.loads(line) for line in (stage / "events.jsonl").read_text().splitlines()]
    events.append({
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": f"sqlite3 {hub.home / 'holdspeak.db'} 'UPDATE meetings SET title=title'",
        },
    })
    (stage / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))
    (stage / "brief.md").write_text("ROLE: ask\nPlease import the recording.\n")

    with pytest.raises(RuntimeError, match="non-MCP write"):
        driver._audit_codex_turn(stage, "turn", hub, {"meeting.import"}, 0)


def test_audit_rejects_non_mcp_http_writes_inside_turn(tmp_path: Path) -> None:
    stage, hub = _mint_transcript(tmp_path)
    rows = [json.loads(line) for line in hub.transcript_path.read_text().splitlines()]
    rows.append({"method": "POST", "path": "/api/meetings/import", "status": 201})
    hub.transcript_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    (stage / "brief.md").write_text("ROLE: ask\nPlease import the recording.\n")

    with pytest.raises(RuntimeError, match="non-MCP HTTP writes"):
        driver._audit_codex_turn(stage, "turn", hub, {"meeting.import"}, 0)


def test_reconcile_requires_post_mcp_transport(tmp_path: Path) -> None:
    stage, hub = _mint_transcript(tmp_path)
    rows = [json.loads(line) for line in hub.transcript_path.read_text().splitlines()]
    rows[0]["method"] = "GET"
    hub.transcript_path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    with pytest.raises(RuntimeError, match="no unused matching"):
        driver._reconcile_mcp_calls(stage, hub, 0)


def test_requested_codex_config_separates_auth_and_hub_homes(tmp_path: Path) -> None:
    config = driver._requested_config(tmp_path / "hub-home")
    assert config["command"].endswith("/.venv/bin/holdspeak-mcp")
    assert config["cwd"] == str(driver.REPO)
    assert config["args"] == []
    assert config["required"] is True
    assert config["env"]["HOME"] != str(Path.home())
    assert config["timeout"]["tool_seconds"] > 0


def test_run_dir_is_unique(tmp_path: Path) -> None:
    first = driver._unique_run_dir(tmp_path, "real")
    second = driver._unique_run_dir(tmp_path, "real")
    assert first != second
    assert first.parent == second.parent == tmp_path
