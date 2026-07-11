"""Data models for the HoldSpeak persistence layer.

Extracted verbatim from db.py in Phase 31 (HS-31-01) so repositories and the
Database container share them without import cycles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

# Validation constants shared across the persistence layer.
VALID_ACTION_ITEM_STATUSES = frozenset({"pending", "done", "dismissed"})
VALID_ACTION_ITEM_REVIEW_STATES = frozenset({"pending", "accepted"})
VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES = frozenset(
    {"candidate", "armed", "dismissed", "started"}
)
# Phase 37 (HS-37-02): the actuator-proposal lifecycle.
VALID_ACTUATOR_PROPOSAL_STATUSES = frozenset(
    {"proposed", "approved", "executed", "rejected", "failed"}
)
VALID_CAPABILITY_INVOCATION_STATES = frozenset(
    {"running", "succeeded", "failed", "cancelled", "unavailable", "empty"}
)
VALID_CAPABILITY_ATTEMPT_STATES = frozenset(
    {"running", "succeeded", "failed", "cancelled", "empty"}
)


@dataclass
class MeetingSummary:
    """Lightweight meeting summary for list views."""
    id: str
    started_at: datetime
    ended_at: Optional[datetime]
    title: Optional[str]
    duration_seconds: float
    segment_count: int
    action_item_count: int
    tags: list[str]
    intel_status: str = "disabled"
    intel_status_detail: Optional[str] = None
    capture_status: str = "finalized"
    capture_failure: Optional[str] = None
    capture_checkpoint_seconds: float = 0.0
    provenance: str = "desktop"


@dataclass
class IntelJob:
    """Deferred intelligence job metadata."""

    meeting_id: str
    status: str
    transcript_hash: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]
    meeting_title: Optional[str] = None
    started_at: Optional[datetime] = None
    intel_status_detail: Optional[str] = None


@dataclass
class IntelQueueSummary:
    """Aggregated deferred-intel queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class IntelJobAttempt:
    """Deferred-intel attempt event for one meeting."""

    meeting_id: str
    attempt: int
    outcome: str
    error: Optional[str]
    retry_at: Optional[datetime]
    created_at: datetime


@dataclass
class ActionItemSummary:
    """Action item with meeting context."""
    id: str
    task: str
    owner: Optional[str]
    due: Optional[str]
    status: str
    review_state: str
    meeting_id: str
    meeting_title: Optional[str]
    meeting_date: datetime
    source_timestamp: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    reviewed_at: Optional[datetime]


@dataclass
class IntentWindowSummary:
    """Persisted MIR intent window with confidence scores."""

    meeting_id: str
    window_id: str
    start_seconds: float
    end_seconds: float
    transcript_hash: str
    transcript_excerpt: str
    profile: str
    threshold: float
    active_intents: list[str]
    intent_scores: dict[str, float]
    override_intents: list[str]
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunSummary:
    """Persisted MIR plugin-run record."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    status: str
    idempotency_key: Optional[str]
    duration_ms: float
    output: Optional[dict[str, Any]]
    error: Optional[str]
    deduped: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunJob:
    """Deferred MIR plugin-run queue item."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    transcript_hash: str
    idempotency_key: str
    context: dict[str, Any]
    status: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]


@dataclass
class PluginRunJobQueueSummary:
    """Aggregated deferred plugin-run queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class ProjectSummary:
    """User-defined project knowledge base."""

    id: str
    name: str
    description: str
    keywords: list[str]
    team_members: list[str]
    context: dict[str, Any]
    detection_threshold: float
    is_archived: bool
    meeting_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class ArtifactSummary:
    """Persisted synthesized artifact with lineage sources."""

    id: str
    meeting_id: str
    artifact_type: str
    title: str
    body_markdown: str
    structured_json: dict[str, Any]
    confidence: float
    status: str
    plugin_id: str
    plugin_version: str
    sources: list[dict[str, str]]
    created_at: datetime
    updated_at: datetime
    # 'meeting' | 'run' (v6, Phase 74). Run-born rows have no meeting anchor:
    # meeting_id stores NULL and reads back "" here.
    origin: str = "meeting"


@dataclass
class ActivityRecord:
    """Normalized local activity record from browser history metadata."""

    id: int
    source_browser: str
    source_profile: str
    source_path_hash: str
    url: str
    normalized_url: str
    title: Optional[str]
    domain: str
    visit_count: int
    first_seen_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    last_visit_raw: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityImportCheckpoint:
    """Per browser/profile import checkpoint for local activity readers."""

    source_browser: str
    source_profile: str
    source_path_hash: str
    last_visit_raw: Optional[str]
    last_imported_at: Optional[datetime]
    last_error: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityProjectRule:
    """User-defined rule for assigning local activity to a project."""

    id: str
    project_id: str
    project_name: Optional[str]
    name: str
    enabled: bool
    priority: int
    match_type: str
    pattern: str
    entity_type: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityEnrichmentConnectorState:
    """Persisted state for an optional activity enrichment connector."""

    id: str
    enabled: bool
    settings: dict[str, Any]
    last_run_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ConnectorRun:
    """One persisted invocation of a connector pack.

    HS-13-05. Each run row captures the start/finish timestamps,
    the success / error flag, the byte count and per-capability
    counters (annotations / candidates / commands). Rows are
    deleted alongside the connector's other output when the
    operator clicks "Clear annotations" / "Clear candidates" —
    run history is part of the pack's output, not a global log.
    """

    id: int
    connector_id: str
    started_at: datetime
    finished_at: datetime
    succeeded: bool
    error: Optional[str]
    output_bytes: int
    annotation_count: int
    candidate_count: int
    command_count: int

    def duration_ms(self) -> int:
        delta = self.finished_at - self.started_at
        return max(0, int(delta.total_seconds() * 1000))

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "succeeded": self.succeeded,
            "error": self.error,
            "output_bytes": self.output_bytes,
            "annotation_count": self.annotation_count,
            "candidate_count": self.candidate_count,
            "command_count": self.command_count,
            "duration_ms": self.duration_ms(),
        }


@dataclass
class ActivityAnnotation:
    """Local enrichment annotation attached to an activity record or entity."""

    id: str
    activity_record_id: Optional[int]
    source_connector_id: str
    annotation_type: str
    title: str
    value: dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityMeetingCandidate:
    """Local candidate for a meeting action derived from activity metadata."""

    id: str
    source_connector_id: str
    source_activity_record_id: Optional[int]
    dedupe_key: str
    title: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    meeting_url: Optional[str]
    started_meeting_id: Optional[str]
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ActuatorProposalRecord:
    """A proposed external side effect awaiting human approval (Phase 37).

    `payload` is the exact machine representation of the side effect — the
    parity source-of-truth the guarded executor (HS-37-04) checks before
    acting. Timestamps are ISO strings. `status` is one of
    `VALID_ACTUATOR_PROPOSAL_STATUSES`.
    """

    id: str
    meeting_id: Optional[str]   # None for origin='desk' (v5 — no sentinel meeting)
    origin: str                 # 'meeting' | 'desk' (v5, Phase 72)
    window_id: str
    plugin_id: str
    plugin_version: str
    idempotency_key: str
    status: str
    target: str
    action: str
    preview: str
    payload: dict[str, Any]
    reversible: bool
    required_capabilities: list[str]
    decided_by: Optional[str]
    approved_payload_hash: Optional[str]
    approved_destination: Optional[str]
    approved_preview_hash: Optional[str]
    preview_renderer_version: Optional[str]
    effect_class: Optional[str]
    policy_version: Optional[str]
    result: Optional[dict[str, Any]]
    error: Optional[str]
    created_at: str
    decided_at: Optional[str]
    executed_at: Optional[str]
    updated_at: str


@dataclass
class ActuatorProposalAuditEntry:
    """One recorded status transition of an actuator proposal (Phase 37)."""

    id: int
    proposal_id: str
    actor: str
    from_status: Optional[str]
    to_status: str
    detail: Optional[str]
    created_at: str


@dataclass
class DictationCorrectionRecord:
    """A persisted dictation correction (Phase 40, HS-40-02).

    The durable form of `plugins.dictation.corrections.Correction`: `kind` is
    `"intent"`/`"target"`, `gist` is the bounded context gist the correction
    applies to, `value` is the corrected block id / target profile. Gist-only +
    secret-rejected at write time (the `CorrectionStore` enforces this before
    persisting), so a stored row never carries a secret.
    """

    id: int
    kind: str
    gist: str
    value: str
    created_at: str


@dataclass
class NoteRecord:
    """A first-class desk Note — content/synced primitive (Primitive Framework).

    The desk's freeform markdown note, authorable on any surface (desktop / iPad /
    web) and synced to the desktop hub. Mirrors the meeting/artifact sync shape:
    `last_modified` drives last-write conflict resolution and `deleted` is a
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "body_markdown": self.body_markdown,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class KBRecord:
    """A desk Knowledge Base — organization/synced primitive (Primitive Framework).

    The desk's knowledge container: a named bag of member primitive ids. NOTE:
    this is DISTINCT from the existing `project.yaml` kb-map and the `.hs/` /
    `.holdspeak/` context files — those are project-scoped dictation context. This
    KB is the desk's user-authored organizational grouping, synced like meetings.
    """

    id: str
    name: str
    member_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "member_ids": list(self.member_ids),
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class RecipeRecord:
    """A first-class Agent persona — capability/synced primitive (Primitive Framework).

    The iPad's Tailored-Agents persona promoted to a canonical server object: a
    named, reusable prompt template (system + user) with an avatar, a role, an
    optional tool list and an optional owning KB. Runnable on the hub via the
    intel/LLM engine.

    NOTE: this is DISTINCT from `holdspeak.agent_context` AgentSession, which is a
    live claude/codex *coding* session capture — a different concept entirely.
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
    profile_id: Optional[str] = None   # Phase 24 — the RuntimeProfile this agent runs on
    # Phase 77 — the iPad-authored pinned context, first-class on the hub.
    manual_context: str = ""
    use_zone_context: bool = False
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "avatar": self.avatar,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "user_template": self.user_template,
            "tools": list(self.tools),
            "kb_id": self.kb_id,
            "profile_id": self.profile_id,
            "manual_context": self.manual_context,
            "use_zone_context": self.use_zone_context,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class ModelManifestRecord:
    """A model MANIFEST — capability/synced primitive (HSM-16-08): "this node has
    this model, with these capabilities." Availability only — the model BINARY
    never syncs and no path/url/bytes field exists here by design (the schema's
    additionalProperties:false makes any such field a validation failure)."""

    id: str                          # "<node>:<file-or-model-id>" — node-scoped, never collides
    node: str = ""                   # the device holding it ("desktop", "iPad", "iPhone")
    name: str = ""                   # the human/model name ("Qwen3.5-9B-Instruct-Q6_K")
    capabilities: list[str] = field(default_factory=list)   # e.g. ["language"]
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node": self.node,
            "name": self.name,
            "capabilities": list(self.capabilities),
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class ProfileRecord:
    """A RuntimeProfile — capability/synced primitive (Phase 24): a named "where
    intelligence runs" target. SHAPE ONLY — the API key never lives here and never
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "model_file": self.model_file,
            "base_url": self.base_url,
            "model": self.model,
            "node": self.node,
            "context_limit": self.context_limit,
            "requires_key": self.requires_key,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class ChainRecord:
    """A Chain — capability/synced primitive (Primitive Framework).

    An ordered run of recipes: `steps` is a list of agent ids executed in
    sequence. Synced like meetings/artifacts.
    """

    id: str
    name: str
    steps: list[str] = field(default_factory=list)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "steps": list(self.steps),
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class DirectoryRecord:
    """A Directory — organization/synced primitive (Primitive Framework).

    The canonical organization container. The iPad renders a Directory as a
    spatial **zone**; the web/desktop render it as a folder. What syncs is the
    directory's *identity* and *nesting*: `id, name, parent_id` (a `parent_id`
    chain is a nested zone / sub-directory). What does NOT sync is the zone's
    per-device geometry/paint (cx, cy, w, h, color, …) — that is layout, kept
    local on each surface and never canonical.

    Membership (which primitive is filed in this directory) is a SEPARATE synced
    map — see `DirectoryMembershipRecord` / `DirectoryMembershipRepository`.

    Synced like meetings/artifacts: `last_modified` is the last-write-wins
    conflict key and `deleted` is a tombstone (a deleted directory keeps its row
    so the tombstone propagates to other surfaces).
    """

    id: str
    name: str
    parent_id: Optional[str] = None
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class DirectoryMembershipRecord:
    """A filing edge: which primitive is filed in which directory.

    The canonical, synced **membership map** (`primitive_id → directory_id`). This
    is *organization*, not layout, so it MUST sync — a meeting/artifact/note/agent
    filed into a directory carries that edge to every surface.

    RELATIONSHIP TO THE LEGACY `filed` MAP: the classic desktop home and the iPad
    both kept membership as an in-surface dictionary (`hs.desk.filed` on the web,
    the iPad's `filed: [primitive_id: zone_id]`). This record is the canonical
    server-side formalization of that map, and SUPERSEDES it: each `(primitive_id)`
    keys at most one membership row (a primitive lives in one directory), exactly
    like those single-valued maps. The surfaces' local `filed` maps become caches
    that hydrate from / push to these rows over `/api/sync`.

    Keyed by `primitive_id` (one filing per primitive). `last_modified` is the
    last-write-wins key; `deleted` is a tombstone (an unfiled primitive keeps its
    row, deleted=1, so the unfile propagates). The synced id of this record is the
    `primitive_id` (the map key).
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "directory_id": self.directory_id,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class WorkflowRecord:
    """A Workflow — capability/synced primitive (Primitive Framework).

    A saved Workbench workflow: either a freeform `prompt` or a node-graph
    `graph_json` (the Blueprints visual program). Synced like meetings/artifacts.
    """

    id: str
    name: str
    prompt: str = ""
    graph_json: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    last_modified: str = ""
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "graph_json": self.graph_json,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "deleted": self.deleted,
        }


@dataclass
class CapabilityAttemptRecord:
    """One execution attempt inside a durable capability invocation."""

    id: str
    invocation_id: str
    attempt_index: int
    destination: str
    provider: Optional[str]
    state: str
    error: Optional[str]
    result_ref: Optional[str]
    started_at: str
    completed_at: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "invocation_id": self.invocation_id,
            "attempt_index": self.attempt_index,
            "destination": self.destination,
            "provider": self.provider,
            "state": self.state,
            "error": self.error,
            "result_ref": self.result_ref,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class CapabilityInvocationRecord:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "definition_ref": self.definition_ref,
            "initiator": self.initiator,
            "grounding_refs": list(self.grounding_refs),
            "requested_placement": self.requested_placement,
            "input_snapshot": dict(self.input_snapshot),
            "state": self.state,
            "result_ref": self.result_ref,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass
class DictationJournalRecord:
    """One persisted dictation-journal entry (Phase 45, HS-45-01).

    The durable afterlife of a single dictation/dry-run pipeline run: what was
    said (`transcript`), how it routed (`intent`/`block_id`/`confidence`), where
    it was headed (`target_profile`), what got typed (`final_text`), and how long
    each stage took (`stage_ms`/`total_ms`/`rewrite_pass_ms`). `source` is
    `"dictation"` (a real spoken run) or `"dry_run"` (the no-mic web path).
    `corrected`/`correction_id` are unset here and set by HS-45-03 when the user
    fixes the entry in the moment. Transcript + final text are secret-filtered
    before persistence, so a stored row never carries a secret.
    """

    id: int
    created_at: str
    source: str
    transcript: str
    final_text: str
    project_root: Optional[str] = None
    intent: Optional[str] = None
    block_id: Optional[str] = None
    target_profile: Optional[str] = None
    stage_ms: dict[str, float] = field(default_factory=dict)
    total_ms: float = 0.0
    rewrite_pass_ms: list[float] = field(default_factory=list)
    confidence: Optional[float] = None
    warnings: list[str] = field(default_factory=list)
    corrected: bool = False
    correction_id: Optional[int] = None



@dataclass
class MeshRelayJob:
    """A mesh-edge relay run (HS-85-01): work addressed to ONE node, claimed by
    that node's worker, executed on ITS OWN provider, result posted back.
    Hub-local rows — never a synced kind; prompts move only hub ⇄ the
    executing node."""

    id: str
    node: str
    task_kind: str = "llm"
    system_prompt: str = ""
    user_prompt: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_hint: str = ""
    status: str = "queued"  # queued | running | completed | failed
    result: Optional[str] = None
    error: Optional[str] = None
    deadline_at: str = ""
    created_at: str = ""
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node": self.node,
            "task_kind": self.task_kind,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model_hint": self.model_hint,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "deadline_at": self.deadline_at,
            "created_at": self.created_at,
            "claimed_at": self.claimed_at,
            "completed_at": self.completed_at,
        }
