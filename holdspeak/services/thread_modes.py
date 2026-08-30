"""HS-153-01/03: Thread modes -- a mode is a recipe with kind='mode'.

Each mode carries an allow-list of tool names, a short system prompt,
and an optional list of guardrail note ids (HS-153-03).
The executor's palette = mode allow-list intersection TOOL_NAMES; an
unbound thread (no mode) returns None from ``palette_for`` and the
caller falls back to ``CHAT_PALETTE`` (the 152 addendum).

Seeds are deterministic (hs-seed-mode-*) and idempotent: the seed path
creates them only when absent, reconcile-time ensures they exist on
every hub.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from .thread_tools import TOOL_NAMES, _TOOL_CLASSES

_log = logging.getLogger(__name__)

# Set of mode ids whose unclassified-tool warning has already been emitted.
_warned_modes: set[str] = set()

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
    guardrails: tuple[str, ...] = ()  # HS-153-03: guardrail note ids


# HS-153-03: per-mode guardrail enablement (D3).
# Chase enables both seeds; Desk enables egress-guard; Draft/Plan none.
_CHASE_GUARDRAILS = (
    "hs-seed-guardrail-effect-guard",
    "hs-seed-guardrail-egress-guard",
)
_DESK_GUARDRAILS = (
    "hs-seed-guardrail-egress-guard",
)

MODE_SEEDS: tuple[Mode, ...] = (
    Mode(
        id="hs-seed-mode-desk",
        name="Desk",
        avatar="#6B7280",
        system_prompt="You have read access to the full desk. Observe and inform, never act.",
        tools=_DESK_TOOLS,
        guardrails=_DESK_GUARDRAILS,
    ),
    Mode(
        id="hs-seed-mode-chase",
        name="Chase",
        avatar="#2563EB",
        system_prompt="You can read the desk and act on people and follow-through. Move work forward.",
        tools=_CHASE_TOOLS,
        guardrails=_CHASE_GUARDRAILS,
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
    # Custom mode: build from the recipe row.
    # HS-153-03: guardrails stored as a JSON array in the tools_json sibling key.
    guardrail_ids = _extract_guardrails_from_db(db, recipe.id)
    return Mode(
        id=recipe.id,
        name=recipe.name,
        avatar=recipe.avatar,
        system_prompt=recipe.system_prompt,
        tools=frozenset(recipe.tools),
        guardrails=guardrail_ids,
    )


def allowed_tools_for_thread(db: "Database", thread_id: str) -> frozenset[str]:
    """Return the effective tool palette for a thread.

    mode allow-list intersected with TOOL_NAMES; no mode -> Desk's list.

    .. deprecated:: HS-153-01
        Callers in ThreadService should use ``palette_for`` instead,
        which returns None when no mode is bound (caller uses CHAT_PALETTE).
        This function is kept for backward compat.
    """
    palette = palette_for(db, thread_id)
    if palette is None:
        return _DESK_TOOLS & TOOL_NAMES
    return palette


def palette_for(db: "Database", thread_id: str) -> Optional[frozenset[str]]:
    """Return the mode's palette for a thread, or None when no mode is bound.

    When None, the caller should fall back to ``CHAT_PALETTE``.
    When empty (Draft mode), the caller should omit the ``tools`` key entirely
    so the pass loop runs one pass (no tool schemas).

    Unclassified names in a custom mode's allow-list are dropped and logged
    ONCE per (mode id) at WARNING (fail-closed).
    """
    mode = mode_for_thread(db, thread_id)
    if mode is None:
        return None
    # Intersect with TOOL_NAMES; log unclassified names for custom modes
    unknown = mode.tools - TOOL_NAMES - FORWARD_TOOLS
    if unknown and mode.id not in _warned_modes:
        _warned_modes.add(mode.id)
        _log.warning(
            "Mode %r (%s) references unclassified tools (dropped, fail-closed): %s",
            mode.name, mode.id, sorted(unknown),
        )
    return mode.tools & TOOL_NAMES


# ---------------------------------------------------------------------------
# HS-153-03: Guardrails
# ---------------------------------------------------------------------------


def _extract_guardrails_from_db(db: "Database", recipe_id: str) -> tuple[str, ...]:
    """Read guardrail ids from a recipe's tools_json when stored as an object."""
    try:
        with db._connection() as conn:
            row = conn.execute(
                "SELECT tools_json FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()
            if not row:
                return ()
            raw = row[0] if isinstance(row, (tuple, list)) else row["tools_json"]
            if raw and isinstance(raw, str):
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "guardrails" in parsed:
                    return tuple(str(g) for g in parsed["guardrails"])
    except Exception:
        pass
    return ()


def guardrails_for_thread(
    db: "Database", thread_id: str,
) -> list[dict[str, Any]]:
    """Return the loaded guardrail notes enabled on the thread's mode.

    Each entry: {id, title, instruction, trigger_tools, n_messages}.
    Returns [] when no mode is bound or the mode has no guardrails.
    """
    mode = mode_for_thread(db, thread_id)
    if mode is None or not mode.guardrails:
        return []
    result: list[dict[str, Any]] = []
    for gid in mode.guardrails:
        note = db.notes.get(gid)
        if note is None:
            continue
        # Parse the YAML front matter from body_markdown.
        parsed = _parse_guardrail_note(note)
        if parsed is not None:
            result.append(parsed)
    return result


def _parse_guardrail_note(note: Any) -> Optional[dict[str, Any]]:
    """Extract guardrail config from a note's YAML front matter.

    Expected format in body_markdown:
        ---
        instruction: ...
        trigger_tools: [...]
        n_messages: N
        ---
    """
    body = str(note.body_markdown or "")
    if not body.startswith("---"):
        return None
    parts = body.split("---", 2)
    if len(parts) < 3:
        return None
    front = parts[1].strip()
    if not front:
        return None
    try:
        import yaml
        data = yaml.safe_load(front)
    except Exception:
        # Fallback: try JSON
        try:
            data = json.loads(front)
        except Exception:
            return None
    if not isinstance(data, dict):
        return None
    return {
        "id": note.id,
        "title": note.title,
        "instruction": str(data.get("instruction", "")),
        "trigger_tools": list(data.get("trigger_tools", [])),
        "n_messages": int(data.get("n_messages", 6)),
    }


def seed_guardrails(db: "Database") -> int:
    """Idempotent: create guardrail notes that do not yet exist. Returns count created."""
    _GUARDRAIL_SEEDS = [
        {
            "id": "hs-seed-guardrail-effect-guard",
            "title": "Effect guard",
            "tags": ["guardrail"],
            "body_markdown": (
                "---\n"
                "instruction: >\n"
                "  Flag any tool call that writes to a person's ledger\n"
                "  (people.commitment.transition, people.agenda.add,\n"
                "  people.note.create) without naming a specific source\n"
                "  (meeting, decision record, or owner directive) in its\n"
                "  arguments. A call with no source is a violation.\n"
                "trigger_tools:\n"
                '  - "people.*"\n'
                "n_messages: 6\n"
                "---\n"
            ),
        },
        {
            "id": "hs-seed-guardrail-egress-guard",
            "title": "Egress guard",
            "tags": ["guardrail"],
            "body_markdown": (
                "---\n"
                "instruction: >\n"
                "  Flag any pending tool call whose result would carry\n"
                "  people-sourced data (a people.* read) to a cloud\n"
                "  egress boundary. Reading people data on a local\n"
                "  boundary is fine; sending it over a cloud route is a\n"
                "  violation.\n"
                "trigger_tools:\n"
                '  - "people.*"\n'
                "n_messages: 4\n"
                "---\n"
            ),
        },
    ]
    created = 0
    for seed in _GUARDRAIL_SEEDS:
        existing = db.notes.get(seed["id"], include_deleted=True)
        if existing is not None:
            continue
        db.notes.upsert(
            note_id=seed["id"],
            title=seed["title"],
            body_markdown=seed["body_markdown"],
            tags=seed["tags"],
        )
        created += 1
    return created


def toggle_guardrail_on_mode(
    db: "Database",
    recipe_id: str,
    guardrail_id: str,
    enable: bool,
) -> bool:
    """Toggle a guardrail on/off for a mode recipe. Returns True if changed.

    Stores guardrails as the ``guardrails`` key in the ``tools_json`` object.
    When the column is a plain array (old format), it is migrated to
    ``{"tools": [...], "guardrails": [...]}`` on first write.
    """
    recipe = db.recipes.get(recipe_id)
    if recipe is None or recipe.kind != "mode":
        return False
    # Read raw tools_json
    with db._connection() as conn:
        row = conn.execute(
            "SELECT tools_json FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()
        if not row:
            return False
        raw = row[0] if isinstance(row, (tuple, list)) else row["tools_json"]
    try:
        parsed = json.loads(raw) if raw else []
    except Exception:
        parsed = []
    # Normalize to object format
    if isinstance(parsed, list):
        obj = {"tools": parsed, "guardrails": []}
    elif isinstance(parsed, dict):
        obj = parsed
        if "guardrails" not in obj:
            obj["guardrails"] = []
        if "tools" not in obj:
            obj["tools"] = []
    else:
        obj = {"tools": [], "guardrails": []}
    current = list(obj["guardrails"])
    if enable and guardrail_id not in current:
        current.append(guardrail_id)
    elif not enable and guardrail_id in current:
        current.remove(guardrail_id)
    else:
        return False  # no change
    obj["guardrails"] = current
    # Write back
    with db._connection() as conn:
        conn.execute(
            "UPDATE recipes SET tools_json = ? WHERE id = ?",
            (json.dumps(obj, separators=(",", ":")), recipe_id),
        )
    return True
