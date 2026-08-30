"""Knowledge-domain data models: KB, Recipe, Note, Chain, Directory."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Any

from .mixins import Serializable


@dataclass
class NoteRecord(Serializable):
    """A first-class desk Note -- content/synced primitive (Primitive Framework).

    The desk's freeform markdown note, authorable on any surface (desktop / iPad /
    web) and synced to the desktop hub. Mirrors the meeting/artifact sync shape:
    ``last_modified`` drives last-write conflict resolution and ``deleted`` is a
    tombstone (a deleted note keeps its row so the tombstone propagates).
    """

    id: str
    title: str
    body_markdown: str
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class DecisionRecord(Serializable):
    """A first-class Desk architecture decision record (ADR)."""

    id: str
    title: str
    status: str
    deciders: list[str]
    decided_at: str | None
    context_markdown: str
    decision_markdown: str
    alternatives_json: str
    consequences_markdown: str
    superseded_by: str | None
    tags: list[str]
    created_at: str
    updated_at: str
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        try:
            alternatives = json.loads(self.alternatives_json)
        except (TypeError, ValueError):
            alternatives = []
        if not isinstance(alternatives, list):
            alternatives = []
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "deciders": list(self.deciders),
            "decided_at": self.decided_at,
            "context_markdown": self.context_markdown,
            "decision_markdown": self.decision_markdown,
            "alternatives": alternatives,
            "consequences_markdown": self.consequences_markdown,
            "superseded_by": self.superseded_by,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted": self.deleted,
        }


@dataclass
class KBRecord(Serializable):
    """A desk Knowledge Base -- organization/synced primitive (Primitive Framework).

    The desk's knowledge container: a named bag of member primitive ids. NOTE:
    this is DISTINCT from the existing ``project.yaml`` kb-map and the ``.hs/`` /
    ``.holdspeak/`` context files -- those are project-scoped dictation context. This
    KB is the desk's user-authored organizational grouping, synced like meetings.
    """

    id: str
    name: str
    member_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class RecipeRecord(Serializable):
    """A first-class Agent persona -- capability/synced primitive (Primitive Framework).

    The iPad's Tailored-Agents persona promoted to a canonical server object: a
    named, reusable prompt template (system + user) with an avatar, a role, an
    optional tool list and an optional owning KB. Runnable on the hub via the
    intel/LLM engine.

    NOTE: this is DISTINCT from ``holdspeak.agent_context`` AgentSession, which is a
    live claude/codex *coding* session capture -- a different concept entirely.
    Do not merge the two.
    """

    id: str
    name: str
    avatar: str = ""
    role: str = ""
    system_prompt: str = ""
    user_template: str = ""
    tools: list[str] = field(default_factory=list)
    kb_id: Optional[str] = None
    profile_id: Optional[str] = None   # Phase 24 -- the RuntimeProfile this agent runs on
    # Phase 77 -- the iPad-authored pinned context, first-class on the hub.
    manual_context: str = ""
    use_zone_context: bool = False
    kind: str = ""   # HS-153-01: '' = ordinary recipe, 'mode' = thread mode
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class ModelManifestRecord(Serializable):
    """A model MANIFEST -- capability/synced primitive (HSM-16-08): "this node has
    this model, with these capabilities." Availability only -- the model BINARY
    never syncs and no path/url/bytes field exists here by design (the schema's
    additionalProperties:false makes any such field a validation failure)."""

    id: str                          # "<node>:<file-or-model-id>" -- node-scoped, never collides
    node: str = ""                   # the device holding it ("desktop", "iPad", "iPhone")
    name: str = ""                   # the human/model name ("Qwen3.5-9B-Instruct-Q6_K")
    capabilities: list[str] = field(default_factory=list)   # e.g. ["language"]
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class ProfileRecord(Serializable):
    """A RuntimeProfile -- capability/synced primitive (Phase 24): a named "where
    intelligence runs" target. SHAPE ONLY -- the API key never lives here and never
    syncs; the hub joins its own secret at request time."""

    id: str
    name: str = ""
    kind: str = "onDevice"          # onDevice | openAICompatible | desktop (HSM-15-11: the paired hub; on the hub itself it resolves to the configured default engine) | meshNode (HS-85-02: relay the run to a mesh node's own provider)
    model_file: str = ""
    base_url: str = ""
    model: str = ""
    node: str = ""                  # meshNode: the mesh node whose worker claims the run
    context_limit: int = 16384
    requires_key: bool = False
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class ChainRecord(Serializable):
    """A Chain -- capability/synced primitive (Primitive Framework).

    An ordered run of recipes: ``steps`` is a list of agent ids executed in
    sequence. Synced like meetings/artifacts.
    """

    id: str
    name: str
    steps: list[str] = field(default_factory=list)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class DirectoryRecord(Serializable):
    """A Directory -- organization/synced primitive (Primitive Framework).

    The canonical organization container. The iPad renders a Directory as a
    spatial **zone**; the web/desktop render it as a folder. What syncs is the
    directory's *identity* and *nesting*: ``id, name, parent_id`` (a ``parent_id``
    chain is a nested zone / sub-directory). What does NOT sync is the zone's
    per-device geometry/paint (cx, cy, w, h, color, ...) -- that is layout, kept
    local on each surface and never canonical.

    Membership (which primitive is filed in this directory) is a SEPARATE synced
    map -- see ``DirectoryMembershipRecord`` / ``DirectoryMembershipRepository``.

    Synced like meetings/artifacts: ``last_modified`` is the last-write-wins
    conflict key and ``deleted`` is a tombstone (a deleted directory keeps its row
    so the tombstone propagates to other surfaces).
    """

    id: str
    name: str
    name_normalized: str = ""
    parent_id: Optional[str] = None
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class DirectoryMembershipRecord(Serializable):
    """A filing edge: which primitive is filed in which directory.

    The canonical, synced **membership map** (``primitive_id -> directory_id``). This
    is *organization*, not layout, so it MUST sync -- a meeting/artifact/note/agent
    filed into a directory carries that edge to every surface.

    RELATIONSHIP TO THE LEGACY ``filed`` MAP: the classic desktop home and the iPad
    both kept membership as an in-surface dictionary (``hs.desk.filed`` on the web,
    the iPad's ``filed: [primitive_id: zone_id]``). This record is the canonical
    server-side formalization of that map, and SUPERSEDES it: each ``(primitive_id)``
    keys at most one membership row (a primitive lives in one directory), exactly
    like those single-valued maps. The surfaces' local ``filed`` maps become caches
    that hydrate from / push to these rows over ``/api/sync``.

    Keyed by ``primitive_id`` (one filing per primitive). ``last_modified`` is the
    last-write-wins key; ``deleted`` is a tombstone (an unfiled primitive keeps its
    row, deleted=1, so the unfile propagates). The synced id of this record is the
    ``primitive_id`` (the map key).
    """

    primitive_id: str
    directory_id: str
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    @property
    def id(self) -> str:
        """The membership's synced identity is its map key (the primitive id)."""
        return self.primitive_id
