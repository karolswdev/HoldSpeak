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
    on_update_action_item: Optional[Callable[[str, str], Any]] = None
    on_update_action_item_review: Optional[Callable[[str, str], Any]] = None
    on_edit_action_item: Optional[Callable[..., Any]] = None
    on_update_meeting: Optional[Callable[..., Any]] = None
    on_set_title: Optional[Callable[[str], None]] = None
    on_set_tags: Optional[Callable[[list[str]], None]] = None

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
    on_wake_type: Optional[Callable[[str], Optional[str]]] = None
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

    # HSM-15-10: whether this server requires a token to talk to it (i.e. it is
    # bound off-loopback). Surfaced UNauthenticated via `GET /api/mesh/info` so a
    # freshly-discovered companion knows whether pairing needs a token. A bool,
    # not a callable — the server fixes it once at bind time.
    mesh_requires_token: bool = False
