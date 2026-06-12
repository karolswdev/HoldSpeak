"""FastAPI request models for the HoldSpeak web runtime.

Keeping these DTOs out of ``web_server.py`` makes route wiring easier to
review and prevents request-schema drift from hiding inside the large server
module.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class _BookmarkRequest(BaseModel):
    label: str = ""


class _StopRequest(BaseModel):
    reason: Optional[str] = None


class _ActionItemUpdateRequest(BaseModel):
    status: str  # "done", "pending", or "dismissed"


class _ActionItemReviewRequest(BaseModel):
    review_state: str  # "pending" or "accepted"


class _ProposalDecisionRequest(BaseModel):
    # HS-37-03: a human approve/reject of an actuator proposal. Approving
    # only flips DB state — execution is HS-37-04. `decided_by` records the actor.
    decision: str  # "approved" or "rejected"
    decided_by: Optional[str] = None


class _ActionItemEditRequest(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class _AftercareFileIssueRequest(BaseModel):
    # HS-49-03: turn an accepted action item into a GitHub-issue actuator
    # *proposal* (proposed state) through the existing propose -> approve ->
    # execute flow. `repo` is the target "owner/name"; nothing is sent until the
    # proposal is separately approved and actuators are enabled.
    action_item_id: str
    repo: str


class _SlackExportRequest(BaseModel):
    # HS-61-01: export one aftercare artifact to Slack as an actuator
    # *proposal* (proposed state). `what` picks the artifact: "digest" or
    # "followup". Nothing is sent until the proposal is separately approved.
    what: str = ""


class _UpdateMeetingRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None


class _IntentProfileRequest(BaseModel):
    profile: str


class _IntentOverrideRequest(BaseModel):
    intents: Optional[list[str]] = None


class _IntentPreviewRequest(BaseModel):
    profile: Optional[str] = None
    threshold: Optional[float] = None
    intent_scores: Optional[dict[str, float]] = None
    override_intents: Optional[list[str]] = None
    previous_intents: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    transcript: Optional[str] = None


class _MeetingStartRequest(BaseModel):
    """Optional body for ``POST /api/meeting/start`` (HS-14-06).

    ``devices`` is an optional list of currently-registered
    AIPI-Lite-class device ids that should contribute audio to the
    meeting. Default empty means legacy local-mic + system-audio only.
    """

    devices: Optional[list[str]] = None


class _GlobalActionItemUpdateRequest(BaseModel):
    status: str


class _GlobalActionItemReviewRequest(BaseModel):
    review_state: str


class _GlobalActionItemEditRequest(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class _SpeakerUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None


class _IntelProcessRequest(BaseModel):
    max_jobs: Optional[int] = None
    mode: Optional[str] = None


class _PluginJobProcessRequest(BaseModel):
    max_jobs: Optional[int] = None
    mode: Optional[str] = None


class _ActivitySettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    retention_days: Optional[int] = None


class _ActivityDomainRuleRequest(BaseModel):
    domain: str
    action: str = "exclude"


class _ActivityProjectRuleRequest(BaseModel):
    project_id: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None
    entity_type: Optional[str] = None


class _ActivityMeetingCandidateRequest(BaseModel):
    source_connector_id: Optional[str] = None
    source_activity_record_id: Optional[int] = None
    title: Optional[str] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    meeting_url: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None


class _ActivityMeetingCandidateStatusRequest(BaseModel):
    status: str


class _ActivityEnrichmentConnectorRequest(BaseModel):
    enabled: Optional[bool] = None
    settings: Optional[dict[str, Any]] = None


class _ActivityExtensionEventsRequest(BaseModel):
    events: list[dict[str, Any]]


class _ActivityCliEnrichmentRunRequest(BaseModel):
    limit: Optional[int] = None
    timeout_seconds: Optional[float] = None
    max_bytes: Optional[int] = None
