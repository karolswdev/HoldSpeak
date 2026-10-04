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
- Every ref it returns is one the Desk opens (``DESK_REF_KINDS``; fenced by
  ``web/src/desk/__tests__/memoryRefsOpen.test.ts`` against the real opener).
  A source with no Desk window is left out.
- The size is bounded whole: each rendered excerpt (ref, title and text) and
  the complete block.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ..grounding import GroundingBlock, hydrate_refs_detailed
from ..logging_config import get_logger

log = get_logger("memory_grounding")

MEMORY_MAX_EXCERPTS = 8
MEMORY_EXCERPT_CHARS = 600   # one rendered excerpt: ref, title and text
MEMORY_TITLE_CHARS = 120
MEMORY_BLOCK_CHARS = 5200    # the complete block, heading lines included
MEMORY_BLOCK_HEADING = "MEMORY"
_CUT = " [cut]"

# The ref kinds this helper returns: the names the Desk opens
# (web/src/desk/openObject.ts ``refOpener``).  The web test
# ``memoryRefsOpen.test.ts`` reads this tuple from this file and puts every
# kind through the real opener; keep it one flat tuple of string literals.
DESK_REF_KINDS = ("meeting", "note", "artifact", "thread", "decision", "desk_decision", "action_item")

# Memory's name for a source -> the name the Desk opens.  A kind that is in
# neither this map nor ``DESK_REF_KINDS`` has no Desk window and is left out.
_DESK_KIND = {"action": "action_item", "transcript": "meeting"}

# The same record under the other names the product uses for it.  A drafter's
# inventory says ``action_item:`` / ``item:`` / ``decision:``; memory says
# ``action:`` / ``project_item:`` / ``decision_record:`` or ``desk_decision:``.
# Exclusion covers every name, so it works before the selection limit.
_EXCLUDE_ALIASES = {
    "action_item": ("action",),
    "action": ("action_item",),
    "item": ("project_item",),
    "meeting": ("transcript",),
    "transcript": ("meeting",),
    "decision": ("decision_record", "desk_decision"),
    "decision_record": ("decision",),
    "desk_decision": ("decision",),
}


def _split(ref: str) -> tuple[str, str]:
    kind, sep, rest = str(ref or "").strip().partition(":")
    return (kind.strip().lower(), rest.split("#", 1)[0].strip()) if sep else ("", "")


def _exclusion_names(refs: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for ref in refs:
        kind, rest = _split(ref)
        if not kind or not rest:
            continue
        names.add(f"{kind}:{rest}")
        names.update(f"{alias}:{rest}" for alias in _EXCLUDE_ALIASES.get(kind, ()))
    return names


def _clip(text: str, cap: int) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= cap:
        return text
    return text[: max(0, cap - len(_CUT))].rstrip() + _CUT


@dataclass(frozen=True)
class MemoryExcerpt:
    """One remembered source, cut to a bounded size."""

    ref: str  # kind:id, as memory names it
    kind: str
    title: str
    text: str

    def line(self) -> str:
        if self.title and self.text:
            return f"- {self.ref}: {self.title} -- {self.text}"
        return f"- {self.ref}: {self.text or self.title}"


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
    """One block as a Desk-openable excerpt whose RENDERED line fits ``cap``."""
    kind = _DESK_KIND.get(block.kind, block.kind)
    if kind not in DESK_REF_KINDS:
        return None  # no Desk window opens it: not a citable source
    ref = f"{kind}:{str(block.ref).split('#', 1)[0]}"
    prefix = len(f"- {ref}: ")
    if cap - prefix <= len(_CUT):
        return None  # the bound has no room for any words
    title = _clip(block.title, min(MEMORY_TITLE_CHARS, cap - prefix))
    text = " ".join(str(block.text or "").split())
    if text == title or (title and text.startswith(title) and len(text) <= len(title) + 1):
        text = ""
    if not text and not title:
        return None
    # "- <ref>: <title> -- <text>": the text takes what the line has left.
    room = cap - prefix - (len(title) + len(" -- ") if title else 0)
    text = _clip(text, room) if text and room > len(_CUT) else ""
    if not text and not title:
        return None
    return MemoryExcerpt(ref=ref, kind=kind, title=title, text=text)


def memory_context(
    db: Any,
    *,
    project_id: str | None = None,
    query: str | None = None,
    exclude_refs: Iterable[str] = (),
    max_excerpts: int = MEMORY_MAX_EXCERPTS,
    excerpt_chars: int = MEMORY_EXCERPT_CHARS,
    block_chars: int = MEMORY_BLOCK_CHARS,
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
    excluded = _exclusion_names(exclude_refs)
    scope = [f"project:{project}"] if project else None

    passes: list[str | None] = []
    if question:
        passes.append(question)  # relevance (project-scoped when a project is set)
    if project:
        passes.append(None)  # then the project's attached sources

    excerpts: list[MemoryExcerpt] = []
    seen: set[str] = set(excluded)
    # The whole block is bounded: the two marker lines, then each line.
    used = 2 * (len(MEMORY_BLOCK_HEADING) + 16)
    for pass_query in passes:
        try:
            result = hydrate_refs_detailed(
                db, [], [], "summary",
                qualified_refs=scope,
                query=pass_query,
                include_memory=True,
                # Applied by grounding BEFORE its selection limit.
                exclude_refs=sorted(seen),
            )
        except Exception as exc:  # memory never fails a drafter
            log.warning("memory read failed (%s); the drafter runs without it", exc)
            continue
        for block in result.blocks:
            excerpt = _excerpt(block, excerpt_chars)
            if excerpt is None or excerpt.ref in seen:
                continue
            cost = len(excerpt.line()) + 1
            if used + cost > block_chars:
                return MemoryContext(tuple(excerpts))
            used += cost
            seen.update(_exclusion_names([excerpt.ref]))
            excerpts.append(excerpt)
            if len(excerpts) >= max_excerpts:
                return MemoryContext(tuple(excerpts))
    return MemoryContext(tuple(excerpts))
