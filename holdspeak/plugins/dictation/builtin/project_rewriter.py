"""Project-aware LLM rewrite stage for dictation.

This stage is intentionally opt-in. It uses repo-local `.hs/` context to
turn raw dictation into a cleaner prompt or typing payload, while failing
open to the prior text if no project context or rewrite-capable runtime is
available.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any

from holdspeak.project_doc_suggestions import ProjectDocSuggestion, suggest_project_doc_update
from holdspeak.plugins.dictation.contracts import StageResult, Utterance

_CODE_FENCE_RE = re.compile(r"^\s*```(?:text|markdown|md)?\s*(.*?)\s*```\s*$", re.DOTALL)
_MAX_REWRITE_ABSOLUTE_CHARS = 8_000


def _latest_text(prior: list[StageResult], default: str) -> str:
    if prior:
        return prior[-1].text
    return default


def _hs_prompt_context(utt: Utterance) -> str:
    project = utt.project or {}
    hs = project.get("hs") if isinstance(project, dict) else None
    if not isinstance(hs, dict):
        return ""
    return str(hs.get("prompt_context") or "").strip()


def _default_prompt_builder(utt: Utterance, text: str, hs_context: str) -> str:
    project = utt.project or {}
    project_name = project.get("name") if isinstance(project, dict) else None
    project_label = str(project_name or "current project")
    target = _target_profile(utt)
    target_id = target.get("id", "unknown")
    target_label = target.get("label", "Unknown")
    target_directive = _target_directive(str(target_id))
    agent_context = _agent_reply_context(utt)
    agent_summary = _agent_summary_context(utt)
    agent_lines = []
    if agent_summary:
        agent_lines = [
            "",
            "Recent agent context summary:",
            agent_summary,
        ]
    elif agent_context:
        agent_lines = [
            "",
            "Recent agent message awaiting user response:",
            agent_context,
        ]
    return "\n".join(
        [
            "Rewrite the dictated text for direct insertion into the user's active app.",
            f"Project: {project_label}",
            f"Target profile: {target_id} ({target_label})",
            f"Target guidance: {target_directive}",
            *agent_lines,
            "",
            "Project context from repo-local .hs files:",
            hs_context,
            "",
            "Rules:",
            "- Preserve the user's intent and do not invent facts.",
            "- Apply the .hs instructions, memory, workflows, issues, terms, and ignore guidance.",
            "- Adapt wording to the target profile. For coding agents, write an actionable prompt.",
            "- If the text already fits, return it unchanged.",
            "- Return only the rewritten text. No explanation, preface, or code fence.",
            "",
            "Dictated text:",
            text,
        ]
    )


class ProjectRewriter:
    """LLM-backed project-aware rewrite stage."""

    id = "project-rewriter"
    version = "0.1.0"
    requires_llm = True

    def __init__(
        self,
        runtime: Any,
        *,
        max_tokens: int = 512,
        temperature: float = 0.15,
        suggest_project_docs: bool = True,
        prompt_builder: Callable[[Utterance, str, str], str] | None = None,
    ) -> None:
        self._runtime = runtime
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._suggest_project_docs = suggest_project_docs
        self._prompt_builder = prompt_builder or _default_prompt_builder

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        start = time.perf_counter()
        text = _latest_text(prior, utt.raw_text)
        hs_context = _hs_prompt_context(utt)
        if not hs_context:
            return self._noop(start, text, "no_hs_context", utt=utt)

        rewrite = getattr(self._runtime, "rewrite", None)
        if not callable(rewrite):
            return self._noop(
                start,
                text,
                "unsupported_runtime",
                utt=utt,
                warnings=["runtime does not support project-aware rewrite"],
            )

        prompt = self._prompt_builder(utt, text, hs_context)
        try:
            raw = rewrite(
                prompt,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
        except Exception as exc:
            return self._noop(
                start,
                text,
                "rewrite_failed",
                utt=utt,
                warnings=[f"runtime rewrite failed; preserving input ({type(exc).__name__})"],
            )
        rewritten = _clean_rewrite_text(str(raw))
        if not rewritten:
            return self._noop(
                start,
                text,
                "empty_rewrite",
                utt=utt,
                warnings=["runtime returned an empty rewrite; preserving input"],
            )
        if _rewrite_too_long(text, rewritten):
            return self._noop(
                start,
                text,
                "rewrite_too_long",
                utt=utt,
                warnings=["runtime rewrite exceeded length budget; preserving input"],
            )
        suggestion, suggestion_status = self._suggestion_for(utt, rewritten, hs_context)
        output_text = (
            f"{rewritten}\n\n---\n{suggestion.to_injected_markdown()}"
            if suggestion is not None
            else rewritten
        )
        return StageResult(
            stage_id=self.id,
            text=output_text,
            intent=None,
            elapsed_ms=(time.perf_counter() - start) * 1000.0,
            warnings=[],
            metadata={
                "reason": "rewritten",
                "changed": output_text != text,
                "context_dir": _context_dir(utt),
                "target_profile": _target_profile(utt),
                "project_doc_suggestion": suggestion.to_dict() if suggestion else None,
                "project_doc_suggestion_status": suggestion_status,
            },
        )

    def _noop(
        self,
        start: float,
        text: str,
        reason: str,
        *,
        utt: Utterance,
        warnings: list[str] | None = None,
    ) -> StageResult:
        return StageResult(
            stage_id=self.id,
            text=text,
            intent=None,
            elapsed_ms=(time.perf_counter() - start) * 1000.0,
            warnings=warnings or [],
            metadata={
                "reason": reason,
                "changed": False,
                "context_dir": "",
                "target_profile": _target_profile(utt),
                "project_doc_suggestion": None,
                "project_doc_suggestion_status": "not_applicable",
            },
        )

    def _suggestion_for(
        self,
        utt: Utterance,
        rewritten: str,
        hs_context: str,
    ) -> tuple[ProjectDocSuggestion | None, str]:
        if not self._suggest_project_docs:
            return None, "disabled"
        target = _target_profile(utt)
        if target.get("id") not in {"codex_cli", "claude_code"}:
            return None, "skipped_target"
        project = utt.project or {}
        project_name = str(project.get("name") or "current project") if isinstance(project, dict) else "current project"
        suggestion = suggest_project_doc_update(
            self._runtime,
            source_text=rewritten,
            project_name=project_name,
            target_profile=target,
            hs_context=hs_context,
            agent_context=_agent_summary_context(utt) or _agent_reply_context(utt),
        )
        return suggestion, "suggested" if suggestion is not None else "no_suggestion"


def _context_dir(utt: Utterance) -> str:
    project = utt.project or {}
    hs = project.get("hs") if isinstance(project, dict) else None
    if isinstance(hs, dict):
        return str(hs.get("context_dir") or "")
    return ""


def _target_profile(utt: Utterance) -> dict[str, Any]:
    target = utt.activity.get("target") if isinstance(utt.activity, dict) else None
    if isinstance(target, dict):
        return dict(target)
    return {
        "id": "unknown",
        "label": "Unknown",
        "confidence": 0.0,
        "source": "none",
    }


def _agent_reply_context(utt: Utterance) -> str:
    agent = utt.activity.get("agent") if isinstance(utt.activity, dict) else None
    if not isinstance(agent, dict) or not bool(agent.get("awaiting_response")):
        return ""
    text = str(agent.get("last_assistant_text") or "").strip()
    if not text:
        return ""
    label = str(agent.get("agent") or "agent")
    cwd = str(agent.get("cwd") or "")
    prefix = f"{label} in {cwd}" if cwd else label
    return f"{prefix}: {text}"


def _agent_summary_context(utt: Utterance) -> str:
    agent = utt.activity.get("agent") if isinstance(utt.activity, dict) else None
    if not isinstance(agent, dict):
        return ""
    summary = agent.get("summary")
    if not isinstance(summary, dict):
        return ""
    text = str(summary.get("summary") or "").strip()
    if not text:
        return ""
    provider = str(summary.get("provider") or "agent")
    generated_at = str(summary.get("generated_at") or "")
    suffix = f" ({provider}, {generated_at})" if generated_at else f" ({provider})"
    return f"{text}{suffix}"


def _target_directive(profile_id: str) -> str:
    return {
        "codex_cli": "Produce a concise implementation request for Codex, including concrete acceptance criteria when useful.",
        "claude_code": "Produce a clear Claude Code task with project context and an explicit desired outcome.",
        "terminal_shell": "Produce shell-appropriate text only; avoid prose unless the user clearly dictated prose.",
        "browser": "Produce polished prose suitable for a web text field.",
        "editor": "Produce text suitable for insertion into a code editor or notes file.",
        "chat": "Produce conversational but concise chat text.",
        "unknown": "Use a generally useful concise rewrite.",
    }.get(profile_id, "Use a generally useful concise rewrite.")


def _clean_rewrite_text(value: str) -> str:
    text = value.strip()
    match = _CODE_FENCE_RE.match(text)
    if match:
        text = match.group(1).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def _rewrite_too_long(original: str, rewritten: str) -> bool:
    budget = min(_MAX_REWRITE_ABSOLUTE_CHARS, max(len(original) * 4 + 200, 400))
    return len(rewritten) > budget
