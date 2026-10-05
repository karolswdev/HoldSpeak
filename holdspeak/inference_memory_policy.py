"""Which AI jobs read memory, and how much: one table, keyed by capability id.

Every built-in inference capability (``inference_capabilities.
builtin_capability_definitions``) has one row here.  The fence
``tests/unit/test_memory_every_job.py`` fails when a built-in capability has
no row, so a new AI job forces a decision.  A capability id that is not in
the table (a plugin's ``meeting.plugin.*`` job, a saved definition) gets
``DEFAULT_POLICY``: memory on, with the drafter bounds.

This table is a side table on purpose: the capability definitions are sealed
(each has a digest), and a memory budget is not part of what a job requires
from a model.

A row says:

- ``scope``: ``"off"`` or ``"scoped"``.  Scoped memory stays inside the job's
  project when the job has one, and is the query pass otherwise
  (``services.memory_grounding.memory_context``).
- ``block_chars`` / ``max_excerpts``: the size of the MEMORY block.  The
  local model has a 32k-token context; the budget is characters, and no row
  is above the drafter default (5,200).
- ``reader``: how the job reads memory.  ``"memory_for"`` jobs call
  ``services.memory_grounding.memory_for`` and the budget above applies.
  ``"grounding"`` jobs (Ask, chat, Recipes, Sequences, the Workbench) read
  memory through the grounding call Ask uses; for them the row turns memory
  on or off, and the size is grounding's own cap.
- ``why``: one line for the reader of this table.

This module imports nothing from the rest of HoldSpeak, so any layer can read
it.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

# The drafter bounds (``services.memory_grounding.MEMORY_BLOCK_CHARS`` and
# ``MEMORY_MAX_EXCERPTS``; the fence holds them equal).
DEFAULT_MEMORY_CHARS = 5200
DEFAULT_MEMORY_EXCERPTS = 8

SCOPES = ("off", "scoped")
READERS = ("memory_for", "grounding", "none")


@dataclass(frozen=True)
class MemoryPolicy:
    """How one AI job reads memory."""

    scope: str
    block_chars: int = DEFAULT_MEMORY_CHARS
    max_excerpts: int = DEFAULT_MEMORY_EXCERPTS
    reader: str = "memory_for"
    why: str = ""

    @property
    def enabled(self) -> bool:
        return self.scope != "off"


def _off(why: str) -> MemoryPolicy:
    return MemoryPolicy(scope="off", block_chars=0, max_excerpts=0, reader="none", why=why)


def _drafter(why: str, *, chars: int = DEFAULT_MEMORY_CHARS, excerpts: int = DEFAULT_MEMORY_EXCERPTS) -> MemoryPolicy:
    return MemoryPolicy(scope="scoped", block_chars=chars, max_excerpts=excerpts, reader="memory_for", why=why)


def _grounding(why: str) -> MemoryPolicy:
    return MemoryPolicy(scope="scoped", reader="grounding", why=why)


DEFAULT_POLICY = _drafter("Not in the table: memory on, with the drafter bounds.")

_SPEECH = "Speech path: no generation from memory, and latency is the job."
_INFRA = "Infrastructure, not a job that writes for the owner."
_APPLE = "Runs in the Swift app, not in this process."

MEMORY_POLICIES: Mapping[str, MemoryPolicy] = MappingProxyType({
    # Thoughts, Ask and chat
    "thought.interview": _grounding("Ask grounding with the Thought's text; the Thought's own note is excluded."),
    "ask.answer": _grounding("Ask grounding with the question."),
    "chat.turn": _grounding("Thread grounding with the message; the thread itself is excluded."),
    "chat.guardrail": _off("A check on one message; memory does not change it."),
    "chat.compact": _off("Compacts the thread it has; memory adds nothing."),
    # Speech and dictation
    "speech.intent_classify": _off(_SPEECH),
    "speech.rewrite": _off(_SPEECH),
    "speech.punctuate": _off(_SPEECH),
    "speech.target_classify": _off(_SPEECH),
    "speech.transcribe": _off(_SPEECH),
    "speech.preload": _off(_SPEECH),
    "project_doc.suggest_update": _off("Dictation hot path; it has the project's .hs context."),
    # Meetings
    "meeting.live_analysis": _off(
        "Each live window would pay 100-400 ms for a memory read (measured 2026-10-04); "
        "the summary after the meeting reads memory."
    ),
    "meeting.bookmark_label": _off("A label from the words around one bookmark."),
    "meeting.auto_title": _off("A title from the transcript."),
    "meeting.deferred_analysis": _drafter("The meeting's project, less the meeting itself."),
    # Agents and tools
    "agent.plan": _drafter("No caller in this tree yet; on by default."),
    "agent.tool_turn": _grounding("The Recipe chat turn: grounding with the question."),
    "agent.code": _drafter("No caller in this tree yet; on by default."),
    "workbench.item": _grounding("Workbench grounding with the item."),
    "recipe.run": _grounding("Recipe grounding with the input."),
    "voice.reference_resolve": _off("The answer is a zone id from a closed list; latency is the job."),
    "sequence.step": _grounding("Sequence grounding with the step's prompt."),
    "workflow.node": _grounding("Workflow grounding with the node's prompt."),
    "project.update_draft": _drafter("The project's memory, less what the inventory holds."),
    "project.brief_prepare": _drafter("The project's memory for the purpose, less the manifest."),
    # Background
    "background.rails_summary": _drafter(
        "Earlier journal entries and notes on the same stories.", chars=1500, excerpts=3,
    ),
    "background.cadence_draft": _drafter(
        "The loop's project or its words, less the loop itself.", chars=2400, excerpts=4,
    ),
    "decision.promotion_draft": _drafter(
        "Earlier decisions and notes on the same subject, less the decision itself.",
        chars=3000, excerpts=5,
    ),
    "delivery.pr_review_draft": _drafter(
        "Decisions and notes on the PR's subject; the prompt already holds the diff.",
        chars=3000, excerpts=5,
    ),
    "calendar.snapshot_extract": _off("Extracts events from a snapshot; memory does not change it."),
    "memory.embed": _off("Memory's own embedder."),
    "memory.extract": _off("Memory's own fact reader: it reads one chunk, never recall."),
    "memory.consolidate": _off("Memory's own consolidator: it reads facts and observations, never recall."),
    # Internal
    "internal.inference.dispatch": _off(_INFRA),
    "internal.speech.runtime_assembly": _off(_INFRA),
    "internal.semantic_dispatch": _off(_INFRA),
    # The Swift app
    "apple.local_completion": _off(_APPLE),
    "apple.endpoint_completion": _off(_APPLE),
    "apple.structured_output": _off(_APPLE),
    "apple.mesh_serve": _off(_APPLE),
    "apple.coder_answer": _off(_APPLE),
    "apple.workbench.blueprint": _off(_APPLE),
    "apple.workbench.workflow": _off(_APPLE),
})


def memory_policy(capability_id: str) -> MemoryPolicy:
    """The row for ``capability_id``; ``DEFAULT_POLICY`` when there is none."""
    return MEMORY_POLICIES.get(str(capability_id or "").strip(), DEFAULT_POLICY)


def memory_enabled(capability_id: str) -> bool:
    """True when the job reads memory at all."""
    return memory_policy(capability_id).enabled


__all__ = [
    "DEFAULT_MEMORY_CHARS",
    "DEFAULT_MEMORY_EXCERPTS",
    "DEFAULT_POLICY",
    "MEMORY_POLICIES",
    "MemoryPolicy",
    "memory_enabled",
    "memory_policy",
]
