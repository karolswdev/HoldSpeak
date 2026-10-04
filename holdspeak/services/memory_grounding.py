"""Memory for the drafters: one scope in, bounded excerpts with refs out.

Ask and desk chat read long memory through ``holdspeak.grounding``
(``hydrate_refs_detailed``).  The processes that draft for the owner -- the
project update, the meeting summary, 1:1 Prep, the Steward -- read none.
This module is the one call they share.  It is NOT a second memory system:
it runs the same grounding call Ask runs and only bounds and formats the
result.

Contract:

- ``memory_context(db, project_id=..., query=...)`` returns a
  :class:`MemoryContext`: ranked excerpts, each with the ref it came from.
- With a project, the read stays inside that project: the relevance pass
  first (when there is a query), then the project's own attached sources.
- Without a project, it is the global relevance pass Ask uses, and it needs
  a query.
- Memory is an enrichment, never a precondition.  No index, no hits or any
  read failure give the empty context, and the drafter runs as it did before.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ..grounding import GroundingBlock, hydrate_refs_detailed
from ..logging_config import get_logger

log = get_logger("memory_grounding")

MEMORY_MAX_EXCERPTS = 8
MEMORY_EXCERPT_CHARS = 600
MEMORY_BLOCK_HEADING = "MEMORY"

# The same record under the two names the product uses for it.  A drafter's
# own inventory says ``action_item:`` / ``item:``; memory says ``action:`` /
# ``project_item:``.  Exclusion compares on the memory name.
_REF_KIND_ALIASES = {"action_item": "action", "item": "project_item"}


def _canonical(ref: str) -> str:
    kind, sep, rest = str(ref or "").strip().partition(":")
    if not sep:
        return str(ref or "").strip()
    kind = kind.strip().lower()
    return f"{_REF_KIND_ALIASES.get(kind, kind)}:{rest.split('#', 1)[0].strip()}"


@dataclass(frozen=True)
class MemoryExcerpt:
    """One remembered source, cut to a bounded size."""

    ref: str  # kind:id, as memory names it
    kind: str
    title: str
    text: str

    def line(self) -> str:
        body = " ".join(self.text.split())
        title = " ".join(self.title.split())
        if title and body and body != title and not body.startswith(title):
            return f"- {self.ref}: {title} -- {body}"
        return f"- {self.ref}: {body or title}"


@dataclass(frozen=True)
class MemoryContext:
    """What a drafter read from memory: the excerpts and their refs."""

    excerpts: tuple[MemoryExcerpt, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.excerpts)

    @property
    def refs(self) -> list[str]:
        return [excerpt.ref for excerpt in self.excerpts]

    @property
    def texts(self) -> dict[str, str]:
        """ref -> the words behind it (title and excerpt)."""
        return {e.ref: f"{e.title} {e.text}".strip() for e in self.excerpts}

    def prompt_block(self, heading: str = MEMORY_BLOCK_HEADING) -> str:
        """The marked context block for a prompt; ``""`` when memory is empty."""
        if not self.excerpts:
            return ""
        lines = [f"[{heading}]"]
        lines.extend(excerpt.line() for excerpt in self.excerpts)
        lines.append(f"[END {heading}]")
        return "\n".join(lines)


EMPTY_MEMORY = MemoryContext()


def _excerpt(block: GroundingBlock, cap: int) -> MemoryExcerpt | None:
    text = str(block.text or "").strip()
    title = str(block.title or "").strip()
    if not text and not title:
        return None
    if len(text) > cap:
        text = text[:cap].rstrip() + " [cut]"
    return MemoryExcerpt(
        ref=f"{block.kind}:{block.ref}", kind=block.kind, title=title, text=text,
    )


def memory_context(
    db: Any,
    *,
    project_id: str | None = None,
    query: str | None = None,
    exclude_refs: Iterable[str] = (),
    max_excerpts: int = MEMORY_MAX_EXCERPTS,
    excerpt_chars: int = MEMORY_EXCERPT_CHARS,
) -> MemoryContext:
    """Read memory for one scope with the grounding call Ask uses.

    ``exclude_refs`` names what the drafter already holds, so memory adds
    only what is new to it.  Stale or unknown members are dropped: a drafter
    has no user to refuse, and a missing source is not a reason to stop.
    """
    project = str(project_id or "").strip()
    question = " ".join(str(query or "").split())
    if not project and not question:
        return EMPTY_MEMORY
    excluded = {_canonical(ref) for ref in exclude_refs if str(ref).strip()}
    scope = [f"project:{project}"] if project else None

    passes: list[str | None] = []
    if question:
        passes.append(question)  # relevance (project-scoped when a project is set)
    if project:
        passes.append(None)  # then the project's attached sources

    excerpts: list[MemoryExcerpt] = []
    seen: set[str] = set(excluded)
    for pass_query in passes:
        try:
            result = hydrate_refs_detailed(
                db, [], [], "summary",
                qualified_refs=scope,
                query=pass_query,
                include_memory=True,
                exclude_refs=sorted(excluded),
            )
        except Exception as exc:  # memory never fails a drafter
            log.warning("memory read failed (%s); the drafter runs without it", exc)
            continue
        for block in result.blocks:
            excerpt = _excerpt(block, excerpt_chars)
            if excerpt is None or _canonical(excerpt.ref) in seen:
                continue
            seen.add(_canonical(excerpt.ref))
            excerpts.append(excerpt)
            if len(excerpts) >= max_excerpts:
                return MemoryContext(tuple(excerpts))
    return MemoryContext(tuple(excerpts))
