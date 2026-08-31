"""Shared accessor object the web route modules read from (HS-26-01).

As routes migrate out of `MeetingWebServer._create_app` (where they currently
close over `self`), they instead take a `WebContext` carrying just the accessors
they need. This grows one field per migrated concern; HS-26-06 collapses the
server's 40+ constructor callbacks into this object.

Keep it a plain data holder: route modules import `WebContext`; `WebContext`
imports no route module (so there is no import cycle).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class WebContext:
    """Accessors needed by the migrated route modules.

    Fields are added as each domain's routes move over. HS-26-01 (pilot:
    `/health`, `/api/state`) needs only the meeting-state getter; HS-26-02
    adds the meeting / speaker / intel cluster's accessors. Every field beyond
    `get_state` defaults to ``None`` so partially-wired contexts (e.g. the pilot
    test) stay valid; the server populates the full set in `_create_app`.
    """

    get_state: Callable[[], dict[str, Any]]

    # HS-26-02: meeting-lifecycle + action-item callbacks the meeting routes
    # invoke. The DB-backed read routes (meetings/speakers/intel listings) close
    # over no server state, so they need nothing here.
    broadcast: Optional[Callable[[str, Any], None]] = None
    on_bookmark: Optional[Callable[[str], Any]] = None
    on_start: Optional[Callable[..., Any]] = None
    on_stop: Optional[Callable[[], Any]] = None
    on_meeting_stop: Optional[Callable[[], Any]] = None
    # HS-132-02: the live meeting's action-item triage. Read by the action-item
    # routes, which bind them into `MeetingService.bind_live_triage` so the three
    # PATCH verbs ask the running session before the archive.
    on_update_action_item: Optional[Callable[[str, str], Any]] = None
    on_update_action_item_review: Optional[Callable[[str, str], Any]] = None
    on_edit_action_item: Optional[Callable[..., Any]] = None
    on_update_meeting: Optional[Callable[..., Any]] = None
    on_set_title: Optional[Callable[[str], None]] = None
    on_set_tags: Optional[Callable[[list[str]], None]] = None
    # HS-122-04: transport-neutral meeting archive and lifecycle boundary.
    # The runtime-owned callbacks above remain bound into this service at app
    # composition, keeping the service itself independent of the web layer.
    meeting_service: Optional[Any] = None
    # A composition-owned factory permits isolated test databases to supply the
    # current service without routes importing database accessors.
    meeting_service_factory: Optional[Callable[[], Any]] = None
    # HS-123-06: focused meeting collaborators composed at the application edge.
    meeting_intel_service: Optional[Any] = None
    meeting_intel_service_factory: Optional[Callable[[], Any]] = None
    meeting_aftercare_service: Optional[Any] = None
    meeting_aftercare_service_factory: Optional[Callable[[], Any]] = None

    # HS-123-05: durable project and projection domain boundaries, composed once
    # by the server so their routes stay transport-only adapters.
    project_service: Optional[Any] = None
    projection_service: Optional[Any] = None

    # HS-123-02: authority and credential lifecycle services are composed once
    # by the server so their routes remain transport-only adapters.
    authority_service: Optional[Any] = None
    credential_service: Optional[Any] = None
    # HS-123-08: cadence, sync, and desk-actuator application boundaries.
    cadence_service: Optional[Any] = None
    follow_through_service: Optional[Any] = None
    door_service: Optional[Any] = None
    # Phase 135: encrypted People sidecar service.  It is intentionally not a
    # normal database repository and carries no sync/export/memory collaborator.
    people_service: Optional[Any] = None
    sync_service: Optional[Any] = None
    actuator_service: Optional[Any] = None

    # HS-123-08: remaining operational services are composed by the server;
    # their route adapters own only HTTP parsing and serialization.
    gate_service: Optional[Any] = None
    setup_service: Optional[Any] = None
    # HS-142-01: pure, owner-only Capability Truth projection.
    inference_setup_service: Optional[Any] = None
    # HS-142-02: durable model acquisition/activation saga.
    inference_acquisition_service: Optional[Any] = None
    # HS-143-12: owner-only aggregate availability/projection boundary. It has
    # no assignment write authority and composes the two services above.
    model_library_service: Optional[Any] = None
    # HS-143-13: the canonical sparse assignment authority is composed once;
    # its HTTP route only adapts closed owner commands and projections.
    inference_assignment_service: Optional[Any] = None
    # Phase 143: process-composed, owner-only registry projection.  It owns no
    # profile/binding/assignment persistence and never resolves a model route.
    inference_capability_service: Optional[Any] = None
    # HS-123-12: delivery persistence/composition boundary for the delivery
    # route family. Individual delivery collaborators remain injectable seams.
    delivery_service: Optional[Any] = None
    mesh_service: Optional[Any] = None
    memory_service: Optional[Any] = None
    mission_control_service: Optional[Any] = None
    # Reactions are the application-level projection from typed service events
    # into Workbenches.  The web surface receives the composed service rather
    # than opening a separate persistence seam.
    reaction_service: Optional[Any] = None
    # HS-159-02: the universal Watch facade over the graduated
    # connector_watches table. Routes come in P3; construction only here.
    watch_service: Optional[Any] = None
    # HS-159-03: the durable setup interview service. Composes
    # ProjectService + WatchService; routes come in P4.
    project_setup_service: Optional[Any] = None
    # HS-141-04: the single application-owned one-question task lifecycle.
    # Route factories must never create their own threads or event loops.
    refinement_coordinator: Optional[Any] = None
    refinement_service: Optional[Any] = None

    # HS-26-03: intent-control + dictation-pipeline callbacks for the dictation
    # routes. The dictation handlers' many private helpers (project detection,
    # block-config IO, dry-run) close over no server state — they need nothing
    # here beyond `on_dictation_config_changed`.
    on_get_intent_controls: Optional[Callable[[], Any]] = None
    on_set_intent_profile: Optional[Callable[[str], Any]] = None
    on_set_intent_override: Optional[Callable[[Optional[list[str]]], Any]] = None
    on_route_preview: Optional[Callable[..., Any]] = None
    on_dictation_config_changed: Optional[Callable[[], None]] = None

    # HSM-13-01: deliver a remote-dictation answer (already run through the rich
    # pipeline) into the desktop's dictation target / AI PI delivery path. The host
    # injects the actual delivery; the route is deliver-on-command only (the client
    # user pressed send) and never autonomous. Absent hook = process-and-return only.
    # The hook accepts the processed text and an optional ``target`` keyword
    # ("agent" | "focused", HSM-15-01a). The default-mode call site passes the
    # text positionally only, so a plain ``Callable[[str], Any]`` hook still works.
    on_remote_dictation: Optional[Callable[..., Any]] = None
    # HS-93-05: optional durable request-identity ledger for paired dictation.
    # Tests may inject an isolated repository; the production route resolves
    # the database repository lazily when this field is absent.
    dictation_deliveries: Optional[Any] = None
    # HS-123-12: the remaining coder/dictation route handlers use these
    # composed application services rather than importing database accessors.
    coder_service: Optional[Any] = None
    dictation_service: Optional[Any] = None

    # HS-26-04: deferred plugin-job queue processing for the activity routes.
    # The activity-intelligence reads close over no server state; the meeting-
    # candidate-start route reuses on_start / on_update_meeting (HS-26-02).
    on_process_plugin_jobs: Optional[Callable[..., Any]] = None

    # HS-26-05: the residual system / page / project surface. These expose the
    # last few server internals the seam needs — the device registry, the
    # project detector, the WebSocket manager, the runtime-status + settings
    # callbacks, and the duration formatter (a server method).
    device_registry: Optional[Any] = None
    project_detector: Optional[Any] = None
    ws: Optional[Any] = None
    on_get_status: Optional[Callable[[], Any]] = None
    on_settings_applied: Optional[Callable[[Any], None]] = None
    # HS-123-03: settings policy and persistence are composed once here; routes
    # receive the already-bound application service.
    settings_service: Optional[Any] = None
    # Write-only, local custody for destination keys. Profile CRUD remains
    # secret-free; only this explicit owner operation may touch a key value.
    profile_key_service: Optional[Any] = None
    on_wake_type: Optional[Callable[[str], Optional[str]]] = None
    on_preview_type: Optional[Callable[[str], Optional[str]]] = None
    on_preview_discard: Optional[Callable[[str], bool]] = None
    on_transcribe: Optional[Callable[..., str]] = None
    # HS-131-09: the ADMITTED speak-to-fill seam — same transcription, but the
    # utterance's authority is handed back so the browser pipeline's model calls
    # are children of it. The pipeline path uses this; the raw path does not.
    on_transcribe_admitted: Optional[Callable[..., Any]] = None
    current_formatted_duration: Optional[Callable[[], Optional[str]]] = None

    # HS-39-02: session dictation correction store (a `CorrectionStore`). The
    # dictation routes record + read corrections through it; the live runtime
    # shares the same instance via `server.dictation_corrections`.
    corrections: Optional[Any] = None

    # HS-39-05: session dictation telemetry store (a `DictationTelemetryStore`),
    # fed via the pipeline `on_run` hook; readiness reads per-stage quantiles.
    telemetry: Optional[Any] = None

    # HS-45-01: session dictation journal recorder (a `DictationJournalRecorder`),
    # fed at the same post-run seam; the dry-run path records a row through it,
    # the live runtime shares the instance via `server.dictation_journal`.
    journal: Optional[Any] = None

    # HS-112-06: the one audio-floor arbiter (a `VoiceTypingSession`), shared
    # with the runtime that owns the hotkey / meeting / wake capture paths. The
    # floor routes read and claim through it so the browser's open mic is an
    # owner on the SAME model instead of a second, invisible one. `None` in a
    # partial context — the routes then answer `arbitrated: false`.
    voice_session: Optional[Any] = None

    # HSM-15-10: whether this server requires a token to talk to it (i.e. it is
    # bound off-loopback). Surfaced UNauthenticated via `GET /api/mesh/info` so a
    # freshly-discovered companion knows whether pairing needs a token. A bool,
    # not a callable — the server fixes it once at bind time.
    mesh_requires_token: bool = False

    # HS-92-02: the general runtime WebSocket follows the same bind policy as
    # HTTP. These values are fixed by MeetingWebServer and checked before the
    # socket is accepted or added to the broadcast manager.
    web_host: str = "127.0.0.1"
    web_auth_token: str = ""
