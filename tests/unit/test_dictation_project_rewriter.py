"""Tests for the opt-in project-aware dictation rewrite stage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from holdspeak.plugins.dictation.builtin.project_rewriter import ProjectRewriter
from holdspeak.plugins.dictation.contracts import StageResult, Utterance


def _utt(text: str = "can you fix the cli thing") -> Utterance:
    return Utterance(
        raw_text=text,
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
        project={
            "name": "HoldSpeak",
            "hs": {
                "instructions": "Format dictation as concise coding-agent tasks.",
                "prompt_context": "## .hs/instructions.md\nFormat dictation as concise coding-agent tasks.",
                "context_dir": "/repo/.hs",
            },
        },
        activity={
            "target": {
                "id": "codex_cli",
                "label": "Codex CLI",
                "confidence": 0.92,
                "source": "hints",
            }
        },
    )


class _RewriteRuntime:
    backend = "fake"

    def __init__(self, text: str = "Fix the CLI issue concisely.") -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    def rewrite(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15) -> str:
        self.calls.append(
            {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        )
        return self.text


class _SequenceRewriteRuntime:
    backend = "fake"

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def rewrite(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15) -> str:
        self.calls.append(
            {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        )
        return self.responses.pop(0)


class _FailingRewriteRuntime:
    backend = "fake"

    def rewrite(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15) -> str:
        _ = (prompt, max_tokens, temperature)
        raise TimeoutError("endpoint timed out")


def test_project_rewriter_uses_hs_context_and_returns_rewritten_text() -> None:
    runtime = _RewriteRuntime()
    stage = ProjectRewriter(runtime)

    result = stage.run(_utt(), prior=[])

    assert result.text == "Fix the CLI issue concisely."
    assert result.metadata["reason"] == "rewritten"
    assert result.metadata["changed"] is True
    assert result.metadata["target_profile"]["id"] == "codex_cli"
    assert runtime.calls
    assert ".hs/instructions.md" in runtime.calls[0]["prompt"]
    assert "Target profile: codex_cli (Codex CLI)" in runtime.calls[0]["prompt"]
    assert "acceptance criteria" in runtime.calls[0]["prompt"]
    assert "can you fix the cli thing" in runtime.calls[0]["prompt"]


def test_project_rewriter_threads_latest_prior_text() -> None:
    runtime = _RewriteRuntime("Implement the bridge fix.")
    stage = ProjectRewriter(runtime)
    prior = [
        StageResult(
            stage_id="pre",
            text="please implement the bridge fix",
            intent=None,
            elapsed_ms=0.0,
        )
    ]

    result = stage.run(_utt(), prior=prior)

    assert result.text == "Implement the bridge fix."
    assert "please implement the bridge fix" in runtime.calls[0]["prompt"]


def test_project_rewriter_includes_recent_agent_question() -> None:
    runtime = _RewriteRuntime("Yes, please delete `tmp/old.py`.")
    stage = ProjectRewriter(runtime)
    utt = _utt("yeah do that")
    activity = dict(utt.activity)
    activity["agent"] = {
        "agent": "claude",
        "cwd": "/repo",
        "awaiting_response": True,
        "last_assistant_text": "Should I delete `tmp/old.py`?",
    }
    utt = Utterance(
        raw_text=utt.raw_text,
        audio_duration_s=utt.audio_duration_s,
        transcribed_at=utt.transcribed_at,
        project=utt.project,
        activity=activity,
    )

    result = stage.run(utt, prior=[])

    assert result.text == "Yes, please delete `tmp/old.py`."
    assert "Recent agent message awaiting user response" in runtime.calls[0]["prompt"]
    assert "Should I delete `tmp/old.py`?" in runtime.calls[0]["prompt"]


def test_project_rewriter_prefers_agent_summary_over_raw_question() -> None:
    runtime = _RewriteRuntime("Continue the summarizer bridge implementation.")
    stage = ProjectRewriter(runtime)
    utt = _utt("keep going")
    activity = dict(utt.activity)
    activity["agent"] = {
        "agent": "codex",
        "cwd": "/repo",
        "awaiting_response": True,
        "last_assistant_text": "Should I implement the summarizer bridge?",
        "summary": {
            "provider": "codex",
            "generated_at": "2026-05-10T00:00:00Z",
            "summary": "Codex is waiting for confirmation to implement the external-agent summarizer bridge.",
        },
    }
    utt = Utterance(
        raw_text=utt.raw_text,
        audio_duration_s=utt.audio_duration_s,
        transcribed_at=utt.transcribed_at,
        project=utt.project,
        activity=activity,
    )

    result = stage.run(utt, prior=[])

    assert result.text == "Continue the summarizer bridge implementation."
    assert "Recent agent context summary" in runtime.calls[0]["prompt"]
    assert "external-agent summarizer bridge" in runtime.calls[0]["prompt"]
    assert "Recent agent message awaiting user response" not in runtime.calls[0]["prompt"]


def test_project_rewriter_noops_without_hs_context() -> None:
    runtime = _RewriteRuntime()
    stage = ProjectRewriter(runtime)
    utt = Utterance(
        raw_text="plain",
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
        project={"name": "NoHS"},
    )

    result = stage.run(utt, prior=[])

    assert result.text == "plain"
    assert result.metadata["reason"] == "no_hs_context"
    assert runtime.calls == []


def test_project_rewriter_preserves_text_for_empty_runtime_output() -> None:
    runtime = _RewriteRuntime("```text\n\n```")
    stage = ProjectRewriter(runtime)

    result = stage.run(_utt("keep this"), prior=[])

    assert result.text == "keep this"
    assert result.metadata["reason"] == "empty_rewrite"
    assert result.warnings


def test_project_rewriter_preserves_text_when_rewrite_is_too_long() -> None:
    runtime = _RewriteRuntime("x" * 10_000)
    stage = ProjectRewriter(runtime)

    result = stage.run(_utt("short request"), prior=[])

    assert result.text == "short request"
    assert result.metadata["reason"] == "rewrite_too_long"
    assert result.warnings == ["runtime rewrite exceeded length budget; preserving input"]


def test_project_rewriter_preserves_text_when_runtime_fails() -> None:
    stage = ProjectRewriter(_FailingRewriteRuntime())

    result = stage.run(_utt("ship the endpoint fallback"), prior=[])

    assert result.text == "ship the endpoint fallback"
    assert result.metadata["reason"] == "rewrite_failed"
    assert result.warnings == ["runtime rewrite failed; preserving input (TimeoutError)"]


def test_project_rewriter_appends_project_doc_suggestion_for_coding_agents() -> None:
    runtime = _SequenceRewriteRuntime(
        [
            "Document the flat-file compatibility rule.",
            (
                '{"target_path": ".hs/memory/project-context-flat-files.md", '
                '"rationale": "Preserves a reusable HoldSpeak convention.", '
                '"content": "Flat .hs_* files are read-only compatibility inputs; canonical edits go into .hs/."}'
            ),
        ]
    )
    stage = ProjectRewriter(runtime)

    result = stage.run(_utt("remember flat files are read only"), prior=[])

    assert result.text.startswith("Document the flat-file compatibility rule.")
    assert "Context preservation suggestion:" in result.text
    assert ".hs/memory/project-context-flat-files.md" in result.text
    assert result.metadata["project_doc_suggestion"] == {
        "target_path": ".hs/memory/project-context-flat-files.md",
        "rationale": "Preserves a reusable HoldSpeak convention.",
        "content": "Flat .hs_* files are read-only compatibility inputs; canonical edits go into .hs/.",
    }
    assert len(runtime.calls) == 2
    assert "Allowed target directories" in runtime.calls[1]["prompt"]


def test_project_rewriter_skips_project_doc_suggestion_for_non_agent_targets() -> None:
    runtime = _SequenceRewriteRuntime(["Polished browser prose."])
    stage = ProjectRewriter(runtime)
    utt = _utt("remember this")
    activity = dict(utt.activity)
    activity["target"] = {
        "id": "browser",
        "label": "Browser",
        "confidence": 0.78,
        "source": "hints",
    }
    utt = Utterance(
        raw_text=utt.raw_text,
        audio_duration_s=utt.audio_duration_s,
        transcribed_at=utt.transcribed_at,
        project=utt.project,
        activity=activity,
    )

    result = stage.run(utt, prior=[])

    assert result.text == "Polished browser prose."
    assert result.metadata["project_doc_suggestion"] is None
    assert len(runtime.calls) == 1


# --- HS-39-01: multi-pass rewriting ---------------------------------------


class _DraftThenFailRuntime:
    backend = "fake"

    def __init__(self, draft: str) -> None:
        self.draft = draft
        self.calls = 0

    def rewrite(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15) -> str:
        _ = (prompt, max_tokens, temperature)
        self.calls += 1
        if self.calls == 1:
            return self.draft
        raise TimeoutError("refine endpoint timed out")


class _FakeClock:
    """Deterministic perf-counter stand-in. Returns each tick once, then holds."""

    def __init__(self, ticks: list[float]) -> None:
        self._ticks = list(ticks)
        self._last = ticks[0] if ticks else 0.0

    def __call__(self) -> float:
        if self._ticks:
            self._last = self._ticks.pop(0)
        return self._last


def test_project_rewriter_single_pass_is_byte_identical() -> None:
    runtime = _RewriteRuntime()
    # suggest_project_docs=False isolates the rewrite passes from the separate
    # suggestion call so we can count rewrite passes directly.
    stage = ProjectRewriter(runtime, suggest_project_docs=False)  # default rewrite_passes=1

    result = stage.run(_utt(), prior=[])

    assert result.text == "Fix the CLI issue concisely."
    assert len(runtime.calls) == 1  # exactly one rewrite call, like pre-Phase-39
    assert result.warnings == []
    assert result.metadata["reason"] == "rewritten"
    assert result.metadata["rewrite_passes_configured"] == 1
    assert result.metadata["rewrite_passes_run"] == 1
    assert result.metadata["rewrite_budget_skipped"] is False
    assert len(result.metadata["rewrite_pass_ms"]) == 1


def test_project_rewriter_multi_pass_refines_prior_draft() -> None:
    runtime = _SequenceRewriteRuntime(["Draft one.", "Refined two."])
    stage = ProjectRewriter(runtime, rewrite_passes=2, suggest_project_docs=False)

    result = stage.run(_utt(), prior=[])

    assert result.text == "Refined two."  # the refined draft propagates
    assert len(runtime.calls) == 2
    # Pass 2 is the refine prompt and carries the pass-1 draft.
    assert "Improve the draft rewrite below" in runtime.calls[1]["prompt"]
    assert "Current draft:" in runtime.calls[1]["prompt"]
    assert "Draft one." in runtime.calls[1]["prompt"]
    assert result.metadata["rewrite_passes_run"] == 2
    assert result.metadata["rewrite_budget_skipped"] is False
    assert len(result.metadata["rewrite_pass_ms"]) == 2


def test_project_rewriter_skips_extra_pass_over_budget() -> None:
    runtime = _SequenceRewriteRuntime(["Draft only."])  # pass 2 never runs
    # start=0, pass0 start=0, pass0 end=0.1s (=100ms), budget check=0.1s, final=0.1s
    clock = _FakeClock([0.0, 0.0, 0.1, 0.1, 0.1])
    stage = ProjectRewriter(
        runtime,
        rewrite_passes=2,
        suggest_project_docs=False,
        latency_budget_ms=150.0,
        clock=clock,
    )

    result = stage.run(_utt(), prior=[])

    assert result.text == "Draft only."  # best-so-far kept; refine skipped
    assert len(runtime.calls) == 1
    assert result.metadata["rewrite_budget_skipped"] is True
    assert result.metadata["rewrite_passes_run"] == 1
    assert result.metadata["rewrite_pass_ms"] == [100.0]
    assert any("skipped refine pass 2/2" in w for w in result.warnings)


def test_project_rewriter_refine_failure_keeps_best_draft() -> None:
    runtime = _DraftThenFailRuntime("Solid first draft.")
    stage = ProjectRewriter(runtime, rewrite_passes=2, suggest_project_docs=False)

    result = stage.run(_utt("do the thing"), prior=[])

    assert result.text == "Solid first draft."  # never regress below single-pass
    assert result.metadata["reason"] == "rewritten"
    assert result.metadata["rewrite_passes_run"] == 1
    assert any("refine pass 2 failed" in w for w in result.warnings)


def test_project_rewriter_refine_empty_keeps_best_draft() -> None:
    runtime = _SequenceRewriteRuntime(["Good draft.", "```text\n\n```"])
    stage = ProjectRewriter(runtime, rewrite_passes=2, suggest_project_docs=False)

    result = stage.run(_utt(), prior=[])

    assert result.text == "Good draft."
    assert result.metadata["rewrite_passes_run"] == 1
    assert any("refine pass 2 empty_rewrite" in w for w in result.warnings)
