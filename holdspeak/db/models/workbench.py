"""Workbench-domain data models."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Any

from .mixins import Serializable

VALID_WORKBENCH_ITEM_STATUSES = frozenset({"pending", "claimed", "done", "failed", "dismissed"})
VALID_SKILL_STATUSES = frozenset({"draft", "active", "archived"})
VALID_SKILL_SOURCES = frozenset({"agent-proposed", "owner-authored"})
VALID_CAPABILITY_INVOCATION_STATES = frozenset(
    {"running", "succeeded", "failed", "cancelled", "unavailable", "empty", "unknown"}
)
VALID_CAPABILITY_ATTEMPT_STATES = frozenset(
    {"running", "succeeded", "failed", "cancelled", "empty", "unknown"}
)


@dataclass
class WorkflowRecord(Serializable):
    """A Workflow -- capability/synced primitive (Primitive Framework).

    A saved Workbench workflow: either a freeform ``prompt`` or a node-graph
    ``graph_json`` (the Blueprints visual program). Synced like meetings/artifacts.
    """

    id: str
    name: str
    prompt: str = ""
    graph_json: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False


@dataclass
class CapabilityAttemptRecord(Serializable):
    """One execution attempt inside a durable capability invocation."""

    id: str
    invocation_id: str
    attempt_index: int
    destination: str
    actual_placement: dict[str, Any]
    provider: Optional[str]
    state: str
    error: Optional[str]
    result_ref: Optional[str]
    started_at: str
    completed_at: Optional[str]


@dataclass
class CapabilityInvocationRecord(Serializable):
    """The additive run envelope shared by Persona, Sequence, and Workflow."""

    id: str
    correlation_id: str
    definition_ref: str
    initiator: str
    grounding_refs: list[str]
    requested_placement: str
    input_snapshot: dict[str, Any]
    state: str
    result_ref: Optional[str]
    error: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    attempts: list[CapabilityAttemptRecord] = field(default_factory=list)


@dataclass
class SkillRecord(Serializable):
    """A reusable procedural skill an agent learns and applies.

    Skills are agent-proposed (owner approves) or owner-authored.
    Attached to recipes, injected into the prompt stack between the
    recipe's system prompt and the item grounding.
    """

    id: str
    title: str = ""
    body: str = ""
    source: str = "owner-authored"
    status: str = "active"
    recipe_ids_json: str = "[]"
    created_by: str = ""
    version: int = 1
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "source": self.source,
            "status": self.status,
            "recipe_ids": json.loads(self.recipe_ids_json) if self.recipe_ids_json else [],
            "created_by": self.created_by,
            "version": self.version,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class WorkbenchRecord(Serializable):
    """A Workbench -- an agent-operated surface that works through items.

    One agent (recipe_id), one inference target (profile_id), one schedule.
    The Workbench is a DeskPrimitive (Article II). The Delivery Workbench
    integration is one instance of this primitive backed by the PMO rails.
    """

    id: str
    name: str
    recipe_id: Optional[str] = None
    profile_id: Optional[str] = None
    schedule: Optional[str] = None
    schedule_enabled: bool = False
    item_order_json: str = "[]"
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "recipe_id": self.recipe_id,
            "profile_id": self.profile_id,
            "schedule": self.schedule,
            "schedule_enabled": self.schedule_enabled,
            "item_order": json.loads(self.item_order_json) if self.item_order_json else [],
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class WorkbenchItemRecord(Serializable):
    """An item on a Workbench -- work for the agent to process.

    Items are conversational (body + grounding), prioritizable, and carry
    the agent's result and placement receipt after processing.
    """

    id: str
    workbench_id: str
    title: str = ""
    body: str = ""
    priority: int = 3
    status: str = "pending"
    grounding_json: str = "{}"
    context_json: str = "{}"
    result: Optional[str] = None
    result_egress_json: Optional[str] = None
    result_artifact_id: Optional[str] = None
    mint_attempted: bool = False
    tokens_consumed: int = 0
    created_at: str = ""
    last_modified: str = ""
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workbench_id": self.workbench_id,
            "title": self.title,
            "body": self.body,
            "priority": self.priority,
            "status": self.status,
            "grounding": json.loads(self.grounding_json) if self.grounding_json else {},
            "context": json.loads(self.context_json) if self.context_json else {},
            "result": self.result,
            "result_egress": json.loads(self.result_egress_json) if self.result_egress_json else None,
            "tokens_consumed": self.tokens_consumed,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "claimed_at": self.claimed_at,
            "completed_at": self.completed_at,
        }


@dataclass
class WorkbenchRunRecord(Serializable):
    """A receipt for one scheduled or manual Workbench run."""

    id: str
    workbench_id: str
    started_at: str = ""
    completed_at: Optional[str] = None
    items_attempted: int = 0
    items_completed: int = 0
    items_failed: int = 0
    total_tokens: int = 0
    egress_boundary: str = ""
    model: str = ""
    constitutional_context_revision: int = 0
    constitutional_context_hash: str = ""
    skills_injected_json: str = "[]"
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workbench_id": self.workbench_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "items_attempted": self.items_attempted,
            "items_completed": self.items_completed,
            "items_failed": self.items_failed,
            "total_tokens": self.total_tokens,
            "egress_boundary": self.egress_boundary,
            "model": self.model,
            "constitutional_context_revision": self.constitutional_context_revision,
            "constitutional_context_hash": self.constitutional_context_hash,
            "skills_injected": json.loads(self.skills_injected_json) if self.skills_injected_json else [],
            "status": self.status,
        }
