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
from pathlib import Path
from typing import Any

from holdspeak.project_doc_suggestions import (
    ProjectDocSuggestion,
    suggest_project_doc_update,
    suggestion_already_covered,
)
from holdspeak.plugins.dictation.contracts import StageResult, Utterance

_CODE_FENCE_RE = re.compile(r"^\s*```(?:text|markdown|md)?\s*(.*?)\s*```\s*$", re.DOTALL)
_MAX_REWRITE_ABSOLUTE_CHARS = 8_000

# Exact warning strings for a draft (pass 0) the runtime returned but we
# can't use. Keyed by the `reason` recorded on the resulting no-op.
_INVALID_DRAFT_WARNINGS = {
    "empty_rewrite": "runtime returned an empty rewrite; preserving input",
    "rewrite_too_long": "runtime rewrite exceeded length budget; preserving input",
}


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
    selected_activity = _selected_activity_context(utt)
    selected_lines = (
        [
            "",
            "The user chose to dictate with this local activity as context:",
            selected_activity,
        ]
        if selected_activity
        else []
    )
    return "\n".join(
        [
            "Rewrite the dictated text for direct insertion into the user's active app.",
            f"Project: {project_label}",
            f"Target profile: {target_id} ({target_label})",
            f"Target guidance: {target_directive}",
            *agent_lines,
            *selected_lines,
            "",
            "Project context from repo-local .hs files:",
            hs_context,
            "",
            "Rules:",
            "- Preserve the user's intent and do not invent facts.",
            "- Apply the .hs instructions, memory, workflows, issues, terms, and ignore guidance.",
            "- When the user chose a local-activity context above, ground the rewrite in that"
            " specific issue/PR/page and reference it by name.",
            "- Adapt wording to the target profile. For coding agents, write an actionable prompt.",
            "- If the text already fits, return it unchanged.",
            "- Return only the rewritten text. No explanation, preface, or code fence.",
            "",
            "Dictated text:",
            text,
        ]
    )


def _default_refine_prompt_builder(utt: Utterance, draft: str, hs_context: str) -> str:
    """HS-39-01: ask the model to critique + tighten its own prior draft.

    Used for passes 2..N of multi-pass rewriting. Deliberately narrower than
    the draft prompt — it carries the project + target context but not the
    agent-reply lines, keeping the model focused on improving the draft rather
    than re-deriving it from scratch.
    """
    project = utt.project or {}
    project_name = project.get("name") if isinstance(project, dict) else None
    project_label = str(project_name or "current project")
    target = _target_profile(utt)
    target_id = target.get("id", "unknown")
    target_label = target.get("label", "Unknown")
    target_directive = _target_directive(str(target_id))
    selected_activity = _selected_activity_context(utt)
    selected_lines = (
        [
            "",
            "Keep the draft grounded in the local-activity context the user chose:",
            selected_activity,
        ]
        if selected_activity
        else []
    )
    return "\n".join(
        [
            "Improve the draft rewrite below for direct insertion into the user's active app.",
            f"Project: {project_label}",
            f"Target profile: {target_id} ({target_label})",
            f"Target guidance: {target_directive}",
            *selected_lines,
            "",
            "Project context from repo-local .hs files:",
            hs_context,
            "",
            "Rules:",
            "- Tighten wording and fix errors while preserving the user's intent.",
            "- Do not invent facts or add requests the user did not make.",
            "- Keep the result adapted to the target profile.",
            "- If the draft is already good, return it unchanged.",
            "- Return only the improved text. No explanation, preface, or code fence.",
            "",
            "Current draft:",
            draft,
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
        rewrite_passes: int = 1,
        refine_prompt_builder: Callable[[Utterance, str, str], str] | None = None,
        latency_budget_ms: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._runtime = runtime
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._suggest_project_docs = suggest_project_docs
        self._prompt_builder = prompt_builder or _default_prompt_builder
        # HS-39-01: multi-pass refinement. `rewrite_passes` >= 1; pass 0 is the
        # draft, passes 1..N-1 critique + tighten the prior draft. The latency
        # budget gates each extra pass; a None budget never skips.
        self._rewrite_passes = max(1, int(rewrite_passes))
        self._refine_prompt_builder = refine_prompt_builder or _default_refine_prompt_builder
        self._latency_budget_ms = latency_budget_ms
        self._clock = clock if clock is not None else time.perf_counter

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        start = self._clock()
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

        best: str | None = None
        passes_run = 0
        pass_ms: list[float] = []
        warnings: list[str] = []
        budget_skipped = False

        for pass_index in range(self._rewrite_passes):
            # Latency-budget gate, applied only to *extra* passes (>= 1) so the
            # first draft is never skipped. Project the next pass at the cost of
            # the last one; skip the remainder if it would breach the budget.
            if pass_index >= 1 and self._latency_budget_ms is not None:
                elapsed_ms = (self._clock() - start) * 1000.0
                projected_ms = pass_ms[-1] if pass_ms else 0.0
                if elapsed_ms + projected_ms > self._latency_budget_ms:
                    budget_skipped = True
                    warnings.append(
                        f"skipped refine pass {pass_index + 1}/{self._rewrite_passes}: "
                        f"would exceed {self._latency_budget_ms:.0f}ms budget"
                    )
                    break

            if pass_index == 0:
                prompt = self._prompt_builder(utt, text, hs_context)
            else:
                prompt = self._refine_prompt_builder(utt, best or text, hs_context)

            pass_start = self._clock()
            try:
                raw = rewrite(
                    prompt,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                )
            except Exception as exc:
                if pass_index == 0:
                    return self._noop(
                        start,
                        text,
                        "rewrite_failed",
                        utt=utt,
                        warnings=[
                            f"runtime rewrite failed; preserving input ({type(exc).__name__})"
                        ],
                    )
                # Refine failure: fail open to the best draft so far so a blip
                # on an extra pass never regresses below single-pass output.
                warnings.append(
                    f"refine pass {pass_index + 1} failed; keeping prior draft "
                    f"({type(exc).__name__})"
                )
                break
            pass_ms.append((self._clock() - pass_start) * 1000.0)

            cleaned = _clean_rewrite_text(str(raw))
            invalid_reason = _invalid_draft_reason(text, cleaned)
            if invalid_reason is not None:
                if pass_index == 0:
                    return self._noop(
                        start,
                        text,
                        invalid_reason,
                        utt=utt,
                        warnings=[_INVALID_DRAFT_WARNINGS[invalid_reason]],
                    )
                # A bad refine (empty / over budget) is discarded; keep best.
                warnings.append(
                    f"refine pass {pass_index + 1} {invalid_reason}; keeping prior draft"
                )
                break
            best = cleaned
            passes_run += 1

        # `best` is guaranteed non-None: pass 0 either returned a no-op above or
        # set `best`. Anything past pass 0 only ever improves or is discarded.
        rewritten = best if best is not None else text
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
            elapsed_ms=(self._clock() - start) * 1000.0,
            warnings=warnings,
            metadata={
                "reason": "rewritten",
                "changed": output_text != text,
                "context_dir": _context_dir(utt),
                "target_profile": _target_profile(utt),
                "project_doc_suggestion": suggestion.to_dict() if suggestion else None,
                "project_doc_suggestion_status": suggestion_status,
                "rewrite_passes_configured": self._rewrite_passes,
                "rewrite_passes_run": passes_run,
                "rewrite_pass_ms": [round(ms, 3) for ms in pass_ms],
                "rewrite_budget_skipped": budget_skipped,
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
            elapsed_ms=(self._clock() - start) * 1000.0,
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
        if suggestion is None:
            return None, "no_suggestion"
        # HS-39-04: don't re-propose what the target doc already says.
        if suggestion_already_covered(suggestion.content, _existing_doc_text(utt, suggestion.target_path)):
            return None, "already_covered"
        return suggestion, "suggested"


def _existing_doc_text(utt: Utterance, target_path: str) -> str:
    """Current contents of the suggestion's target `.hs/*.md`, or '' if absent."""
    project = utt.project or {}
    root = project.get("root") if isinstance(project, dict) else None
    if not root or not target_path:
        return ""
    try:
        path = Path(str(root)) / target_path
        if path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ""


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


def _selected_activity_context(utt: Utterance) -> str:
    """HS-53-07: the record the user chose via "Dictate with this", named for the model.

    The dictation runner pins the selected ``ActivityRecord`` at ``records[0]`` of
    the activity bundle and records its id in ``selected_record_id``. We surface a
    one-line, source-cited reference so the rewrite can ground the dictation in
    that issue/PR/page. Empty string when nothing was selected (the default daily
    path), so the prompt is byte-identical without a pin.
    """
    if not isinstance(utt.activity, dict):
        return ""
    selected_id = utt.activity.get("selected_record_id")
    if selected_id in (None, ""):
        return ""
    records = utt.activity.get("records")
    if not isinstance(records, list):
        return ""
    record = next(
        (r for r in records if isinstance(r, dict) and r.get("id") == selected_id),
        None,
    )
    if record is None:
        return ""
    entity_type = str(record.get("entity_type") or "").strip()
    entity_id = str(record.get("entity_id") or "").strip()
    if entity_type and entity_id:
        head = f"{entity_type} {entity_id}"
    else:
        head = str(record.get("title") or record.get("url") or "").strip()
    if not head:
        return ""
    parts = [head]
    title = str(record.get("title") or "").strip()
    if title and title != head:
        parts.append(f"titled \"{title}\"")
    url = str(record.get("url") or "").strip()
    if url:
        parts.append(f"({url})")
    return " ".join(parts)


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


def _invalid_draft_reason(original: str, cleaned: str) -> str | None:
    """Why a cleaned rewrite can't be used, or None if it's good.

    Shared by every pass: an empty or over-budget rewrite is rejected. On pass
    0 the caller turns this into a no-op; on a refine pass it discards the draft
    and keeps the best prior result.
    """
    if not cleaned:
        return "empty_rewrite"
    if _rewrite_too_long(original, cleaned):
        return "rewrite_too_long"
    return None
