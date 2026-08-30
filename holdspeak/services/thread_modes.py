"""HS-153-01: Thread modes -- a mode is a recipe with kind='mode'.

Each mode carries an allow-list of tool names and a short system prompt.
The executor's palette = mode allow-list intersection TOOL_NAMES; an
unknown thread (no mode) defaults to Desk's list.

Seeds are deterministic (hs-seed-mode-*) and idempotent: the seed path
creates them only when absent, reconcile-time ensures they exist on
every hub.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from .thread_tools import TOOL_NAMES, _TOOL_CLASSES

if TYPE_CHECKING:
    from ..db.core import Database

# ---------------------------------------------------------------------------
# Allow-list computation from the classification map
# ---------------------------------------------------------------------------

_EVIDENCE_READ = frozenset(
    name for name, (cls, _) in _TOOL_CLASSES.items() if cls == "evidence_read"
)
_CANDIDATE_BUILDER = frozenset(
    name for name, (cls, _) in _TOOL_CLASSES.items() if cls == "candidate_builder"
)

# Forward references: tools that are declared in a mode allow-list but
# not yet registered in TOOL_NAMES (they land in a parallel story).
# When a forward tool lands in TOOL_NAMES, remove it from this set.
FORWARD_TOOLS: frozenset[str] = frozenset()

# --- Desk: every evidence_read + candidate_builder ---
_DESK_TOOLS = frozenset(_EVIDENCE_READ | _CANDIDATE_BUILDER)

# --- Chase: Desk + the named People/follow-through effects + door.add_item ---
_CHASE_EXTRAS = frozenset({
    "people.commitment.transition",
    "people.agenda.add",
    "people.note.create",
    "follow_through.complete",
    "follow_through.commit_decision",
    "door.add_item",
})
_CHASE_TOOLS = frozenset(_DESK_TOOLS | _CHASE_EXTRAS)

# --- Draft: no tools ---
_DRAFT_TOOLS: frozenset[str] = frozenset()

# --- Plan: thought.* reads + door.get + memory.search + decision_record.* reads ---
_PLAN_TOOLS = frozenset(
    {name for name in _EVIDENCE_READ if name.startswith("thought.")}
    | {name for name in _EVIDENCE_READ if name.startswith("decision_record.")}
    | {"door.get", "memory.search"}
)


# ---------------------------------------------------------------------------
# Mode dataclass and seeds
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Mode:
    id: str
    name: str
    avatar: str
    system_prompt: str
    tools: frozenset[str]


MODE_SEEDS: tuple[Mode, ...] = (
    Mode(
        id="hs-seed-mode-desk",
        name="Desk",
        avatar="#6B7280",
        system_prompt="You have read access to the full desk. Observe and inform, never act.",
        tools=_DESK_TOOLS,
    ),
    Mode(
        id="hs-seed-mode-chase",
        name="Chase",
        avatar="#2563EB",
        system_prompt="You can read the desk and act on people and follow-through. Move work forward.",
        tools=_CHASE_TOOLS,
    ),
    Mode(
        id="hs-seed-mode-draft",
        name="Draft",
        avatar="#9333EA",
        system_prompt="Write freely. No tools, no context lookups, just composition.",
        tools=_DRAFT_TOOLS,
    ),
    Mode(
        id="hs-seed-mode-plan",
        name="Plan",
        avatar="#059669",
        system_prompt="Reflect on decisions, thoughts, and memory. Plan, do not execute.",
        tools=_PLAN_TOOLS,
    ),
)


def seed_modes(db: "Database") -> int:
    """Idempotent: create mode recipes that do not yet exist. Returns count created."""
    created = 0
    for mode in MODE_SEEDS:
        existing = db.recipes.get(mode.id, include_deleted=True)
        if existing is not None:
            continue
        db.recipes.upsert(
            recipe_id=mode.id,
            name=mode.name,
            avatar=mode.avatar,
            system_prompt=mode.system_prompt,
            tools=sorted(mode.tools),
            kind="mode",
        )
        created += 1
    return created


def mode_for_thread(db: "Database", thread_id: str) -> Optional[Mode]:
    """Return the Mode bound to a thread via threads.recipe_id, or None."""
    thread = db.threads.get(thread_id)
    if thread is None or not thread.recipe_id:
        return None
    recipe = db.recipes.get(thread.recipe_id)
    if recipe is None or recipe.kind != "mode":
        return None
    # Match against known seeds first (deterministic allow-lists)
    for seed in MODE_SEEDS:
        if seed.id == recipe.id:
            return seed
    # Custom mode: build from the recipe row
    return Mode(
        id=recipe.id,
        name=recipe.name,
        avatar=recipe.avatar,
        system_prompt=recipe.system_prompt,
        tools=frozenset(recipe.tools),
    )


def allowed_tools_for_thread(db: "Database", thread_id: str) -> frozenset[str]:
    """Return the effective tool palette for a thread.

    mode allow-list intersected with TOOL_NAMES; no mode -> Desk's list.
    """
    mode = mode_for_thread(db, thread_id)
    if mode is None:
        # Default to Desk
        return _DESK_TOOLS & TOOL_NAMES
    return mode.tools & TOOL_NAMES
