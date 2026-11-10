"""The Settings hub row facts (HS-170-04), moved out of the route (2026-11-09).

``settings.hub`` (``holdspeak/settings_operations.py``) binds :meth:`SettingsHubService.hub`;
``GET /api/settings/hub`` is produced from it. The read composes the hub's own
model library, inference assignments and cadence services (each may be
absent: its row then makes no claim).
"""
from __future__ import annotations

from typing import Any


def bare_settings_hub(db: Any, observer: Any) -> Any:
    """Off-hub MCP uses the same read, over the usual bare collaborators.

    The hub never uses this builder: its registry holds its composed services.
    """
    from .cadence_service import CadenceService
    from .inference_assignment_service import InferenceAssignmentService
    from .inference_setup_service import InferenceSetupApplicationService
    from .model_library_service import ModelLibraryApplicationService
    from ..config import Config

    setup = InferenceSetupApplicationService(db)
    return SettingsHubService(
        # get_library is a read. Do not start acquisition recovery for a hub
        # summary; no download verb is exposed by this collaborator.
        model_library_service=ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=None),
        inference_assignment_service=InferenceAssignmentService(db),
        cadence_service=CadenceService(db, Config.load().cadence, observer=observer),
    )


def _resolve_meetings_host(config: Any) -> str | None:
    """HS-172-02: resolve the meetings group's assigned model host.

    Returns the HOST the run egresses to, never a profile label:
    - LAN endpoint: its ip/hostname (``192.168.1.43``)
    - This device: ``local``
    - Cloud provider: the provider's API host (``api.openai.com``)
    - Mesh: the node name
    - No assignment: None
    """
    try:
        profile_id = config.meeting.intel_profile_id
        if not profile_id:
            return None
        from ..intel.providers import resolve_meeting_placement
        placement = resolve_meeting_placement(config.meeting)
        if not placement.profile_id:
            return None
        return _placement_host(placement)
    except Exception:
        return None


def _placement_host(placement: Any) -> str:
    """Derive the egress host from a MeetingPlacement.

    Uses ``endpoint_host(base_url)`` for the bare hostname (the same
    source the Concierge's engine_display_name and the Speak resolver
    use), falling back to the boundary for local runs.
    """
    from ..intel.providers import endpoint_host
    if placement.node:
        return str(placement.node)
    host = endpoint_host(placement.base_url)
    return host if host else (placement.boundary or "local")


class SettingsHubService:
    """One read over the services the Settings hub rows summarize."""

    def __init__(self, *, model_library_service: Any = None, inference_assignment_service: Any = None,
                 cadence_service: Any = None) -> None:
        self._model_library = model_library_service
        self._assignments = inference_assignment_service
        self._cadence = cadence_service

    def _database(self) -> Any:
        from ..db import get_database
        from ..runtime.composition import db_or

        for target in (self._assignments, self._model_library, self._cadence):
            if (db := getattr(target, "_db", None)) is not None:
                return db
        return db_or(get_database)

    def hub(self, principal: Any) -> dict[str, Any]:
        """HS-170-04: the Settings hub row facts.

        One read returning the module rows' state tokens from existing services.
        Counts are integers; the face applies the zero law.
        """
        from ..config import Config

        config = Config.load()
        p = principal

        # Models: engines from the model library summary, groups from
        # the assignments summary.
        engines = 0
        groups_set = 0
        default_set = False
        # Inventory 2026-10-03 (UX-CANON A.10): the hub rows said
        # "Voice LIVE" and "SUMMARY SET ON" with no engine assigned. A
        # switch is not a working path; each row also carries whether its
        # work has an engine. A missing key means unknown.
        group_engine: dict[str, bool] = {}
        answers_fact: dict[str, Any] = {"engineSet": None, "engine": None}
        if self._model_library is not None:
            try:
                lib = self._model_library.get_library(p)
                summary = lib.get("summary", {})
                engines = summary.get("ready_count", 0)
            except Exception:
                pass
        if self._assignments is not None:
            try:
                asn = self._assignments.assignment_summary(p)
                rows = asn.get("rows", [])
                for row in rows:
                    if row.get("id") == "global":
                        default_set = row.get("status") == "assigned"
                    elif row.get("status") == "assigned":
                        groups_set += 1
            except Exception:
                pass
            # The engine fact is the EFFECTIVE assignment for the capability
            # the work runs on, as the runner resolves it (capability, then
            # its group, then the default). A group row misses a selection
            # made for one capability (the summary selection writes
            # `capability:meeting.deferred_analysis`), and said NO ENGINE
            # after a successful selection (review of #789).
            for wire_key, capability_id in (
                ("voice", "speech.rewrite"),
            ):
                try:
                    resolved = self._assignments.resolve_effective(
                        p, capability_id=capability_id)
                    group_engine[wire_key] = resolved.get("status") == "assigned"
                except Exception:
                    pass  # unknown: the face makes no engine claim
            # PHILO-17 U35: the headline names the engine that answers an
            # Ask. The assignment route decides only after the route
            # migration (AskService._routed_assignments_active); before it
            # the answer is unknown and the face names no engine.
            try:
                routed = self._assignments.routed("ask.answer")
                if routed:
                    resolved = self._assignments.resolve_effective(
                        p, capability_id="ask.answer")
                    answers_fact["engineSet"] = resolved.get("status") in {
                        "assigned", "no_compatible_assignment",
                    }
                    entries = ((resolved.get("assignment") or {}).get("entries") or [])
                    if answers_fact["engineSet"] and entries:
                        answers_fact["engine"] = str(
                            entries[0].get("label") or entries[0].get("profile_id") or ""
                        ) or None
            except Exception:
                pass  # unknown: the face makes no engine claim

        # PHILO-15 B33: the summary engine is the ROUTE the queue takes
        # (exact, group, global default; OFF first), the same answer
        # doctor's "Meeting summary: profile …" line reads. It was the
        # exact-capability resolution plus the legacy config pointer, so
        # five faces said "no model" while summaries ran on the LAN box.
        summary_fact: dict[str, Any] = {"engine_set": None, "off": False, "host": None}
        try:
            from ..services.meeting_route_projection import summary_engine_fact

            summary_fact = summary_engine_fact(self._database())
        except Exception:
            pass
        if summary_fact.get("engine_set") is not None:
            group_engine["meetings"] = bool(summary_fact["engine_set"])

        # Connections: count provider connections.
        connected = 0
        try:
            conns = self._database().automations.list_provider_connections()
            connected = len(conns)
        except Exception:
            pass

        # Voice: pipeline live + target.
        voice_live = config.dictation.pipeline.enabled
        voice_target = config.dictation.pipeline.target_profile_override or "auto"
        # Betterment ST0: the Voice fact reads whether speech works, the
        # same speech-model read Setup and doctor make (disk only). A
        # switch is not a working path. None: unknown.
        speech_ready: bool | None = None
        try:
            from ..whisper_models import configured_speech_readiness

            speech_ready = bool(configured_speech_readiness(config=config).get("ready"))
        except Exception:
            pass

        # Meetings: intelligence enabled.
        intel_on = config.meeting.intel_enabled

        # Rhythm: count active cadence loops + heartbeat sweep state.
        loops = 0
        if self._cadence is not None:
            try:
                loop_list = self._cadence.list_loops(p)
                loops = len(loop_list.get("loops", []))
            except Exception:
                pass

        # HS-171-02: heartbeat sweep rhythm mirror.
        heartbeat_rhythm: dict[str, Any] = {"loops": loops}
        try:
            from ..services.heartbeat_service import HeartbeatService
            hb = HeartbeatService(self._database())
            heartbeat_rhythm = hb.hub_rhythm()
        except Exception:
            heartbeat_rhythm["sweepEveryMinutes"] = 15
            heartbeat_rhythm["nextSweepAt"] = None
            heartbeat_rhythm["lastSweepAt"] = None
            heartbeat_rhythm["quiet"] = {"start": 22, "end": 8, "held": False}

        # Sounds.
        sounds_on = config.ui.desk_sounds

        # System.
        mesh_on = bool(getattr(config.mesh, "device_name", ""))
        remote_on = bool(config.remote.streamable_http_enabled)

        # Posture.
        posture = config.control_mode

        # writtenAt: the settings file's last write.
        written_at = None
        try:
            from ..config import CONFIG_FILE
            import os
            if CONFIG_FILE.exists():
                written_at = os.path.getmtime(CONFIG_FILE)
        except Exception:
            pass

        # HS-172-02: most recent completed intel run for the receipt.
        last_run_at: str | None = None
        last_run_s: int | None = None
        try:
            with self._database()._connection() as _conn:
                _row = _conn.execute(
                    "SELECT intel_completed_at, intel_requested_at "
                    "FROM meetings "
                    "WHERE intel_status = 'complete' AND intel_completed_at IS NOT NULL "
                    "ORDER BY intel_completed_at DESC LIMIT 1"
                ).fetchone()
                if _row and _row["intel_completed_at"]:
                    last_run_at = _row["intel_completed_at"]
                    if _row["intel_requested_at"]:
                        from datetime import datetime as _dt
                        _req = _dt.fromisoformat(_row["intel_requested_at"])
                        _comp = _dt.fromisoformat(_row["intel_completed_at"])
                        last_run_s = max(0, int((_comp - _req).total_seconds()))
        except Exception:
            pass

        return {
            "models": {
                "engines": engines,
                "groupsSet": groups_set,
                "defaultSet": default_set,
            },
            "connections": {"connected": connected},
            "voice": {
                "live": voice_live,
                "target": voice_target,
                "engineSet": group_engine.get("voice"),
                "speechReady": speech_ready,
            },
            "meetings": {
                "intelligence": intel_on,
                "engineSet": group_engine.get("meetings"),
                "engine": summary_fact.get("profile"),
                "summariesOff": bool(summary_fact.get("off")),
                "auto": config.meeting.intelligence_auto,
                "auto_record": config.meeting.auto_record,
                "host": summary_fact.get("host") or _resolve_meetings_host(config),
                "lastRunAt": last_run_at,
                "lastRunS": last_run_s,
            },
            "answers": answers_fact,
            "rhythm": heartbeat_rhythm,
            "sounds": {"on": sounds_on},
            # Betterment AG5: how many agents work at once.
            "agents": {"workingAtOnce": config.agents.working_at_once},
            "system": {
                "host": "THIS DEVICE",
                "mesh": mesh_on,
                "remote": remote_on,
            },
            "posture": posture,
            "writtenAt": written_at,
        }

