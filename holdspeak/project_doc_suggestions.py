"""Local LLM suggestions for narrow project documentation updates.

The module deliberately proposes documentation only. It never writes to
project files; callers decide whether to show the suggestion to the user or
inject it into a coding-agent prompt.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

_ALLOWED_DIRS = {
    ".hs/memory",
    ".hs/decisions",
    ".hs/handoffs",
    ".hs/workflows",
    ".hs/issues",
}
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_MAX_CONTENT_CHARS = 1_800
_MAX_RATIONALE_CHARS = 320


@dataclass(frozen=True)
class ProjectDocSuggestion:
    """A user-reviewable proposal for a narrow `.hs/.../*.md` file."""

    target_path: str
    rationale: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {
            "target_path": self.target_path,
            "rationale": self.rationale,
            "content": self.content,
        }

    def to_injected_markdown(self) -> str:
        return "\n".join(
            [
                "Context preservation suggestion:",
                f"Suggested file: `{self.target_path}`",
                f"Rationale: {self.rationale}",
                "",
                "Suggested content:",
                "```md",
                self.content,
                "```",
                "",
                "If useful, update the repo docs with this narrow note before continuing.",
            ]
        )


def suggest_project_doc_update(
    runtime: Any,
    *,
    source_text: str,
    project_name: str,
    target_profile: Mapping[str, Any] | None = None,
    hs_context: str = "",
    agent_context: str = "",
    max_tokens: int = 360,
    temperature: float = 0.1,
) -> ProjectDocSuggestion | None:
    """Ask a rewrite-capable runtime for one safe project-doc suggestion."""

    rewrite = getattr(runtime, "rewrite", None)
    if not callable(rewrite):
        return None

    prompt = build_project_doc_suggestion_prompt(
        source_text=source_text,
        project_name=project_name,
        target_profile=target_profile,
        hs_context=hs_context,
        agent_context=agent_context,
    )
    try:
        raw = rewrite(prompt, max_tokens=max_tokens, temperature=temperature)
    except Exception:
        return None
    return parse_project_doc_suggestion(str(raw))


def build_project_doc_suggestion_prompt(
    *,
    source_text: str,
    project_name: str,
    target_profile: Mapping[str, Any] | None = None,
    hs_context: str = "",
    agent_context: str = "",
) -> str:
    """Prompt contract for project documentation suggestions."""

    target = dict(target_profile or {})
    return "\n".join(
        [
            "You inspect local voice-dictation and coding-agent context.",
            "If the exchange contains durable project knowledge worth preserving, propose exactly one tiny markdown file update.",
            "If there is no durable project knowledge, return exactly: NO_SUGGESTION",
            "",
            "Return JSON only when suggesting:",
            '{"target_path": ".hs/memory/specific-slug.md", "rationale": "...", "content": "..."}',
            "",
            "Rules:",
            "- Allowed target directories: .hs/memory, .hs/decisions, .hs/handoffs, .hs/workflows, .hs/issues.",
            "- The filename must be a lowercase dash-separated slug ending in .md.",
            "- Make the file super narrow: one reusable fact, decision, workflow, handoff, or active issue.",
            "- Do not include secrets, tokens, private keys, or credentials.",
            "- Do not tell HoldSpeak to write the file automatically.",
            "- Keep content under 1800 characters.",
            "",
            f"Project: {project_name or 'unknown'}",
            f"Target profile: {target.get('id', 'unknown')} ({target.get('label', 'Unknown')})",
            "",
            "Existing project context:",
            _bounded(hs_context, 4_000),
            "",
            "Recent agent context:",
            _bounded(agent_context, 2_000),
            "",
            "Current dictated/rewritten text:",
            _bounded(source_text, 2_000),
        ]
    )


def parse_project_doc_suggestion(text: str) -> ProjectDocSuggestion | None:
    """Parse and validate a suggestion from model output."""

    raw = _strip_code_fence(text.strip())
    if not raw or raw == "NO_SUGGESTION":
        return None
    try:
        data = json.loads(_json_object_slice(raw))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    target_path = str(data.get("target_path") or "").strip()
    rationale = _single_line(str(data.get("rationale") or ""))[:_MAX_RATIONALE_CHARS].strip()
    content = str(data.get("content") or "").strip()
    if not _valid_target_path(target_path) or not rationale or not content:
        return None
    if _looks_secret(content) or _looks_secret(rationale):
        return None
    if len(content) > _MAX_CONTENT_CHARS:
        content = content[:_MAX_CONTENT_CHARS].rstrip() + "\n\n[truncated]"
    return ProjectDocSuggestion(
        target_path=target_path,
        rationale=rationale,
        content=content,
    )


def validate_project_doc_target_path(path: str) -> str:
    """Return a safe relative `.hs/.../*.md` target path or raise ValueError."""

    cleaned = str(path or "").strip().replace("\\", "/")
    if not _valid_target_path(cleaned):
        raise ValueError(
            "target_path must be .hs/{memory,decisions,handoffs,workflows,issues}/lower-dash-slug.md"
        )
    return cleaned


def validate_project_doc_suggestion_payload(
    *,
    target_path: str,
    rationale: str,
    content: str,
) -> ProjectDocSuggestion:
    """Validate a user-reviewable project documentation suggestion payload."""

    cleaned_path = validate_project_doc_target_path(target_path)
    cleaned_rationale = _single_line(str(rationale or ""))[:_MAX_RATIONALE_CHARS].strip()
    cleaned_content = str(content or "").strip()
    if not cleaned_rationale:
        raise ValueError("rationale is required")
    if not cleaned_content:
        raise ValueError("content is required")
    if len(cleaned_content) > _MAX_CONTENT_CHARS:
        raise ValueError(f"content is too large; max is {_MAX_CONTENT_CHARS} characters")
    if _looks_secret(cleaned_content) or _looks_secret(cleaned_rationale):
        raise ValueError("suggestion appears to contain a secret or credential")
    return ProjectDocSuggestion(
        target_path=cleaned_path,
        rationale=cleaned_rationale,
        content=cleaned_content,
    )


def _valid_target_path(path: str) -> bool:
    if path.startswith("/") or "\\" in path:
        return False
    parts = path.split("/")
    if len(parts) != 3:
        return False
    if any(part in {"", ".", ".."} for part in parts):
        return False
    directory = "/".join(parts[:2])
    filename = parts[2]
    return directory in _ALLOWED_DIRS and bool(_SLUG_RE.match(filename))


def _strip_code_fence(text: str) -> str:
    match = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text


def _json_object_slice(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return text
    return text[start : end + 1]


def _single_line(text: str) -> str:
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def _bounded(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _looks_secret(text: str) -> bool:
    return bool(
        re.search(
            r"(api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+[a-z0-9._~+/-]{16,}|sk-[a-z0-9]{16,})",
            text,
            flags=re.IGNORECASE,
        )
    )
