"""Finish the claimed meeting Stop and persist its existing result."""
from __future__ import annotations

from typing import Any, Optional

from ..logging_config import get_logger
from ..meeting_session import MeetingSession

log = get_logger("web_runtime")


def finish_meeting_stop(
    runtime: Any, session: MeetingSession, *, audio_owner: str,
) -> dict[str, object]:
    # HS-14-07: notify any attached devices that we are about to
    # stop and persist. Captured *before* ``session.stop`` flips
    # the state and clears the device list.
    attached_ids = [d.id for d in session.state.devices] if session.state else []
    # HS-17-05: stop the Recording-tick *before* the
    # `Saving meeting...` broadcast so a stale tick can't land
    # after the user has been told the meeting is saving.
    runtime.recording_ticker.stop()
    # AIPI-4-14: reset per-device cycle indexes so the next meeting
    # starts the double-tap rotation back at view 0.
    runtime.device_stats_cycle.clear()
    if attached_ids:
        runtime.device_status.broadcast(attached_ids, "Saving meeting...", ttl_ms=0)
    runtime._set_runtime_activity(
        "saving",
        source="meeting",
        detail="Stopping and saving meeting.",
        last_event="meeting_saving",
        last_error="",
    )

    final_state = session.stop()
    device_cleanup_error = getattr(session, "device_cleanup_error", None)
    capture_process_exited = bool(getattr(session, "capture_process_exited", False))
    # C10: a child timeout is a warning, but once the child has actually
    # exited it cannot retain the native device. Release the floor only after
    # that exit; the next Record must be able to acquire it.
    if not device_cleanup_error or capture_process_exited:
        runtime.voice_session.release(audio_owner)
    final_state_payload = final_state.to_dict()
    meeting_id = str(final_state_payload.get("id") or "")
    with runtime.state_lock:
        runtime.last_meeting_snapshot = dict(final_state_payload)
    save_error: Optional[str] = None
    save_payload = {
        "database_saved": False,
        "json_saved": False,
        "json_path": None,
        "intel_job_enqueued": False,
        "intent_windows_saved": 0,
        "plugin_runs_saved": 0,
        "mir_save_error": None,
        "artifacts_saved": 0,
        "artifact_synthesis_error": None,
    }
    queue_flush_error: Optional[str] = None
    try:
        queue_flush = runtime._flush_deferred_plugin_runs_to_db()
        queue_flush_error = str(queue_flush.get("error") or "") or None
        save_result = session.save()
        save_payload = {
            "database_saved": bool(save_result.database_saved),
            "json_saved": bool(save_result.json_saved),
            "json_path": str(save_result.json_path) if save_result.json_path else None,
            "intel_job_enqueued": bool(save_result.intel_job_enqueued),
            "intent_windows_saved": 0,
            "plugin_runs_saved": 0,
            "mir_save_error": None,
            "artifacts_saved": 0,
            "artifact_synthesis_error": None,
            "projects_associated": 0,
            "project_association_error": None,
            "deferred_queue_jobs": int(queue_flush.get("queued_jobs") or 0),
            "deferred_queue_error": queue_flush_error,
        }
        if meeting_id:
            mir_history = runtime._persist_pending_mir_history(meeting_id)
            save_payload["intent_windows_saved"] = int(mir_history.get("intent_windows_saved") or 0)
            save_payload["plugin_runs_saved"] = int(mir_history.get("plugin_runs_saved") or 0)
            save_payload["mir_save_error"] = mir_history.get("error")
            artifacts_result = runtime._synthesize_and_persist_artifacts(meeting_id)
            save_payload["artifacts_saved"] = int(artifacts_result.get("artifacts_saved") or 0)
            save_payload["artifact_synthesis_error"] = artifacts_result.get("error")
            project_result = runtime._associate_meeting_with_projects(meeting_id)
            save_payload["projects_associated"] = int(project_result.get("projects_associated") or 0)
            save_payload["project_association_error"] = project_result.get("error")
            # PHILO-17: "Summary after every meeting" is true at Stop.
            # With a ready route, the setting and the owner's consent
            # (meeting_backlog_service.queue_after_save), the summary is
            # queued now and the drainer wakes. With no ready route the
            # meeting is marked, and the backlog runs it once an engine can.
            save_payload["auto_intel_enqueued"] = False
            save_payload["auto_intel_error"] = None
            try:
                from ..db import get_database as _backlog_db
                from ..services.meeting_backlog_service import queue_after_save

                after_save = queue_after_save(_backlog_db(), meeting_id)
                save_payload["auto_intel_enqueued"] = bool(after_save.get("queued"))
                save_payload["summary_deferred_no_engine"] = after_save.get("reason") == "no_engine"
                if after_save.get("queued"):
                    from ..intel_queue_conductor import wake_intel_queue_conductor

                    wake_intel_queue_conductor()
            except Exception as mark_exc:
                save_payload["auto_intel_error"] = str(mark_exc)
                log.warning("summary after Stop not queued for %s: %s", meeting_id, mark_exc)
    except Exception as exc:
        save_error = str(exc)
        log.error(f"Failed to save meeting from web runtime: {exc}")

    with runtime.meeting_lock:
        if runtime.meeting_session is session:
            runtime.meeting_session = None

    with runtime.state_lock:
        runtime.runtime_status["last_error"] = save_error or device_cleanup_error or ""
    if save_error:
        runtime._set_runtime_activity(
            "error",
            source="meeting",
            detail="Meeting save failed.",
            last_event="meeting_save_failed",
            last_error=save_error,
        )
    elif device_cleanup_error:
        runtime._set_runtime_activity(
            "error",
            source="meeting",
            label="Saved",
            detail="Meeting saved. Audio device did not close.",
            last_event="meeting_saved_audio_cleanup_failed",
            last_error=device_cleanup_error,
        )
    else:
        runtime._set_runtime_activity(
            "complete",
            source="meeting",
            label="Saved",
            detail="Meeting saved.",
            last_event="meeting_saved",
            last_error="",
        )

    return {
        "status": "stopped",
        "meeting": final_state_payload,
        "save": save_payload,
        "save_error": save_error,
        "device_cleanup_error": device_cleanup_error,
    }
