"""Real `mermaid_architecture` plugin: LLM-backed diagram synthesizer.

Phase 16 / HS-16-01. Replaces the `DeterministicPlugin` stub previously
registered for `mermaid_architecture`.

The plugin:
  1. Builds a strict prompt asking the LLM for a one-line summary plus a
     single fenced ```mermaid block (any of the supported Mermaid
     diagram kinds).
  2. Calls the configured intel provider (local llama-cpp or cloud
     OpenAI-compatible) via `MeetingIntel._chat_completion_text`.
  3. Parses the response with `_extract_mermaid_block`, which
     validates that the block declares a known diagram kind on its
     first non-empty line and contains a minimum amount of structure
     (e.g. at least one edge for `flowchart`/`graph`, or a participant
     plus a message line for `sequenceDiagram`).
  4. Returns either the success shape (`summary`, `mermaid`,
     `diagram_kind`, `confidence_hint=1.0`, `active_intents`) or the
     failure shape (`summary`, `confidence_hint=0.0`, `active_intents`
     — `mermaid` key absent). Downstream rendering (HS-16-03 / HS-16-04)
     keys off the presence of the `mermaid` key.

The LLM call is injected via the `intel_call` constructor argument so
unit tests can stub it without wiring a real provider. The default
factory lazily constructs a `MeetingIntel` and caches it on the plugin
instance — loading a local GGUF model is expensive, so we don't want
to do it per `run()`.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.mermaid_architecture")


IntelChat = Callable[[list[dict[str, str]]], str]


_DIAGRAM_KINDS: tuple[str, ...] = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "erDiagram",
    "stateDiagram",
)

_KIND_PREFIX_RE = re.compile(
    r"^(flowchart|graph|sequenceDiagram|classDiagram|erDiagram|stateDiagram)"
    r"(?:[\s\-].*)?$",
    re.IGNORECASE,
)
_MERMAID_FENCE_RE = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


_SYSTEM_PROMPT = (
    "You are a software architecture diagram assistant.\n"
    "Given a meeting transcript and a set of active intents/tags, produce "
    "ONE concise Mermaid diagram (flowchart, graph, sequenceDiagram, "
    "classDiagram, erDiagram, or stateDiagram) capturing the architecture, "
    "data flow, or interaction the participants discussed.\n\n"
    "Output format — strictly:\n"
    "Line 1: a one-line plain-English summary (no markdown, no quotes).\n"
    "Line 2+: a single fenced code block tagged ```mermaid containing "
    "valid Mermaid syntax. The block's first non-empty line must start "
    "with a recognized diagram-kind keyword.\n\n"
    "Do not add prose, explanations, alternatives, or extra fences."
)


def _detect_diagram_kind(block_body: str) -> Optional[str]:
    """Return the canonical diagram kind from the block's first content line."""
    for line in block_body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        match = _KIND_PREFIX_RE.match(stripped)
        if match is None:
            return None
        prefix = match.group(1).lower()
        for kind in _DIAGRAM_KINDS:
            if prefix == kind.lower():
                return kind
        return None
    return None


def _has_min_structure(block_body: str, kind: str) -> bool:
    """Reject obviously-empty blocks per diagram kind."""
    if kind in ("flowchart", "graph"):
        if not re.search(r"--+>?|==+>?|-\.->", block_body):
            return False
        non_kind_lines = [ln for ln in block_body.splitlines() if ln.strip()][1:]
        ids: set[str] = set()
        for line in non_kind_lines:
            for tok in re.findall(r"\b[A-Za-z][\w]*\b", line):
                if tok.lower() in {"subgraph", "end", "direction", "click"}:
                    continue
                ids.add(tok)
                if len(ids) >= 2:
                    return True
        return False
    if kind == "sequenceDiagram":
        has_participant = bool(
            re.search(
                r"^\s*(participant|actor)\b",
                block_body,
                re.MULTILINE | re.IGNORECASE,
            )
        )
        has_message = bool(re.search(r"-?->>?|->", block_body))
        return has_participant and has_message
    if kind == "classDiagram":
        if re.search(r"^\s*class\s+\w+", block_body, re.MULTILINE | re.IGNORECASE):
            return True
        return any(token in block_body for token in ("<|--", "*--", "o--", "<|..", "..>"))
    if kind == "erDiagram":
        if any(token in block_body for token in ("||--", "}o--", "||..||", "}|..")):
            return True
        return bool(re.search(r"\b\w+\s*\{", block_body))
    if kind == "stateDiagram":
        return "[*]" in block_body or "-->" in block_body
    return True


def _extract_mermaid_block(text: str) -> Optional[tuple[str, str]]:
    """Extract the first valid fenced Mermaid block.

    Returns `(block_body, diagram_kind)` on success, where `block_body`
    is the inner contents (no fences) and `diagram_kind` is the
    canonical name from `_DIAGRAM_KINDS`. Returns `None` if no fenced
    `mermaid` block is found, the first non-empty line declares an
    unknown kind, or the block does not meet the minimum-structure bar
    for its kind.
    """
    if not text:
        return None
    match = _MERMAID_FENCE_RE.search(text)
    if match is None:
        return None
    body = match.group(1).strip()
    if not body:
        return None
    kind = _detect_diagram_kind(body)
    if kind is None:
        return None
    if not _has_min_structure(body, kind):
        return None
    return (body, kind)


def _extract_summary(raw: str) -> str:
    """Pull the one-line summary preceding the first ```mermaid fence."""
    if not raw:
        return ""
    head = re.split(r"```mermaid", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    for line in head.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = stripped.lstrip("#-*> ").rstrip()
        return cleaned or stripped
    return ""


def _build_user_prompt(
    *,
    transcript: str,
    active_intents: list[str],
    tags: list[str],
    project_name: str,
) -> str:
    header_lines: list[str] = []
    if project_name:
        header_lines.append(f"Project: {project_name}")
    if active_intents:
        header_lines.append(f"Active intents: {', '.join(active_intents)}")
    if tags:
        header_lines.append(f"Tags: {', '.join(tags)}")
    header = ("\n".join(header_lines) + "\n\n") if header_lines else ""
    return (
        f"{header}Transcript:\n{transcript}\n\n"
        "Produce one Mermaid diagram per the system prompt."
    )


class MermaidArchitecturePlugin:
    """LLM-backed plugin emitting a Mermaid architecture diagram per window."""

    id: str = "mermaid_architecture"
    version: str = "0.1.0"
    kind: str = "artifact_generator"
    execution_mode: str = "deferred"
    required_capabilities: list[str] = ["llm"]

    def __init__(self, *, intel_call: Optional[IntelChat] = None) -> None:
        self._intel_call_override = intel_call
        self._cached_provider: Any = None

    def _call_intel(self, messages: list[dict[str, str]]) -> str:
        if self._intel_call_override is not None:
            return self._intel_call_override(messages)
        if self._cached_provider is None:
            from ...intel import build_configured_meeting_intel  # lazy import: optional deps

            self._cached_provider = build_configured_meeting_intel()
        return self._cached_provider._chat_completion_text(
            messages,
            temperature=0.2,
            max_tokens=800,
        )

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        active_intents = [
            str(intent).strip().lower()
            for intent in (context.get("active_intents") or [])
            if str(intent).strip()
        ]
        tags = [
            str(tag).strip()
            for tag in (context.get("tags") or [])
            if str(tag).strip()
        ]
        project_name = str(
            context.get("project_name") or context.get("project") or ""
        ).strip()

        def _failure(reason: str) -> dict[str, Any]:
            return {
                "summary": reason,
                "confidence_hint": 0.0,
                "active_intents": active_intents,
            }

        if not transcript:
            return _failure("mermaid_architecture: no transcript provided.")

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    transcript=transcript,
                    active_intents=active_intents,
                    tags=tags,
                    project_name=project_name,
                ),
            },
        ]

        try:
            raw = self._call_intel(messages)
        except Exception as exc:
            log.info("mermaid_architecture: intel call failed: %s", exc)
            return _failure(f"mermaid_architecture: intel call failed: {exc}")

        parsed = _extract_mermaid_block(raw or "")
        if parsed is None:
            return _failure(
                "mermaid_architecture: response did not contain a parseable Mermaid block."
            )

        block_body, diagram_kind = parsed
        summary = _extract_summary(raw)
        if not summary:
            summary = f"Architecture diagram ({diagram_kind})."

        return {
            "summary": summary,
            "mermaid": block_body,
            "diagram_kind": diagram_kind,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "MermaidArchitecturePlugin",
    "_extract_mermaid_block",
]
