"""Tests for local project documentation suggestion proposals."""

from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak.project_doc_suggestions import (
    build_project_doc_suggestion_prompt,
    parse_project_doc_suggestion,
    suggest_project_doc_update,
    validate_project_doc_suggestion_payload,
)


class _SuggestionRuntime:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def rewrite(self, prompt: str, *, max_tokens: int = 360, temperature: float = 0.1) -> str:
        self.calls.append(
            {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        )
        return self.response


def test_parse_project_doc_suggestion_accepts_narrow_hs_path() -> None:
    suggestion = parse_project_doc_suggestion(
        json.dumps(
            {
                "target_path": ".hs/decisions/agent-hooks-context-channel.md",
                "rationale": "Captures the hook convention for future handoffs.",
                "content": "Agent hooks are optional context channels for cwd and recent questions.",
            }
        )
    )

    assert suggestion is not None
    assert suggestion.target_path == ".hs/decisions/agent-hooks-context-channel.md"
    assert "Context preservation suggestion" in suggestion.to_injected_markdown()


def test_parse_project_doc_suggestion_rejects_unsafe_or_broad_paths() -> None:
    assert parse_project_doc_suggestion('{"target_path": "README.md", "rationale": "x", "content": "x"}') is None
    assert parse_project_doc_suggestion('{"target_path": ".hs/memory/Bad_Name.md", "rationale": "x", "content": "x"}') is None
    assert parse_project_doc_suggestion('{"target_path": ".hs/memory/token.md", "rationale": "x", "content": "api_key=abc"}') is None


def test_validate_project_doc_suggestion_payload_rejects_unsafe_path() -> None:
    with pytest.raises(ValueError, match="target_path"):
        validate_project_doc_suggestion_payload(
            target_path=".hs/memory/BadName.md",
            rationale="Useful memory",
            content="Remember this.",
        )


def test_suggest_project_doc_update_uses_runtime_and_validates_response() -> None:
    runtime = _SuggestionRuntime(
        json.dumps(
            {
                "target_path": ".hs/memory/project-context-flat-files.md",
                "rationale": "Preserves the flat-file compatibility convention.",
                "content": "Flat .hs_* files are read-only compatibility inputs; canonical edits go into .hs/.",
            }
        )
    )

    suggestion = suggest_project_doc_update(
        runtime,
        source_text="Remember that flat .hs files are read-only.",
        project_name="HoldSpeak",
        target_profile={"id": "codex_cli", "label": "Codex CLI"},
        hs_context="## .hs/instructions.md\nUse narrow docs.",
        agent_context="Codex is implementing project context conventions.",
    )

    assert suggestion is not None
    assert suggestion.target_path == ".hs/memory/project-context-flat-files.md"
    assert runtime.calls
    assert "Allowed target directories" in runtime.calls[0]["prompt"]
    assert runtime.calls[0]["max_tokens"] == 360


def test_suggest_project_doc_update_returns_none_for_no_suggestion() -> None:
    runtime = _SuggestionRuntime("NO_SUGGESTION")

    assert (
        suggest_project_doc_update(
            runtime,
            source_text="hello",
            project_name="HoldSpeak",
        )
        is None
    )


def test_build_prompt_preserves_contract_language() -> None:
    prompt = build_project_doc_suggestion_prompt(
        source_text="document the handoff",
        project_name="HoldSpeak",
        target_profile={"id": "claude_code", "label": "Claude Code"},
    )

    assert "Return JSON only when suggesting" in prompt
    assert ".hs/handoffs" in prompt
    assert "Do not tell HoldSpeak to write the file automatically" in prompt
