"""The meeting lifecycle glue (HS-63-04).

Start/stop, the segment/intel/broadcast handlers, bookmarks, meeting
updates, and the action-item passthroughs — verbatim moves out of
WebRuntime.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

import numpy as np

from ..device_status import (
    push_intel_to_devices,
    push_segment_to_devices,
)
from ..logging_config import get_logger
from ..meeting_session import MeetingSession
from ..web.runtime_support import _UnknownDeviceError

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class MeetingGlueMixin:
    def _active_meeting_session(self) -> Optional[MeetingSession]:
        with self.meeting_lock:
            session = self.meeting_session
        if session is None or not session.is_active:
            return None
        return session

    def _normalize_tags(self, tags: Optional[list[str]]) -> list[str]:
        if not isinstance(tags, list):
            return []
        return [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    def _meeting_summary_from_state(self, state: dict[str, object]) -> Optional[dict[str, object]]:
        if not bool(state.get("meeting_active")):
            return None
        meeting_id = state.get("id")
        if not isinstance(meeting_id, str) or not meeting_id:
            return None
        return {
            "id": meeting_id,
            "title": state.get("title"),
            "tags": state.get("tags") if isinstance(state.get("tags"), list) else [],
            "started_at": state.get("started_at"),
            "ended_at": state.get("ended_at"),
            "duration": state.get("duration"),
            "formatted_duration": state.get("formatted_duration"),
        }

    def _broadcast_intel_status(self) -> None:
        if self.server is None:
            return
        state = self._get_state()
        intel_status = state.get("intel_status")
        if intel_status is not None:
            self.server.broadcast("intel_status", intel_status)

    def _on_meeting_segment(self, segment) -> None:
        try:
            speaker = str(getattr(segment, "speaker", "") or "Speaker")
            text = str(getattr(segment, "text", "") or "").strip()
            detail = f"{speaker}: {text}" if text else "Transcript segment captured."
            self._set_runtime_activity(
                "meeting_live",
                source="meeting",
                label="Segment captured",
                detail=detail[:220],
                last_event="meeting_segment",
                last_error="",
            )
        except Exception as exc:
            log.debug(f"Failed to map meeting segment activity: {exc}")
        if self.server is not None:
            try:
                self.server.broadcast("segment", segment.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast segment: {exc}")
        # HS-17-08: push each finalized segment to attached AIPI-Lite
        # devices as a 3s flash so the LCD reflects what's being
        # transcribed in real time. No-op when no devices attached.
        try:
            active = self._active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_segment_to_devices(self.device_status, attached_ids, segment)
        except Exception as exc:
            log.debug(f"Failed to push segment to device LCD: {exc}")

    def _on_meeting_intel(self, intel) -> None:
        self._set_runtime_activity(
            "complete",
            source="meeting",
            label="Intel ready",
            detail="Meeting intelligence finished.",
            last_event="meeting_intel_complete",
            last_error="",
        )
        if self.server is not None:
            try:
                self.server.broadcast("intel_complete", intel.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast intel_complete: {exc}")
        self._broadcast_intel_status()
        # HS-17-07: push the intel summary to attached AIPI-Lite LCDs
        # so the user gets visible feedback when intel finishes (topics,
        # actions, summary — all landed in the middle slot).
        try:
            active = self._active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_intel_to_devices(self.device_status, attached_ids, intel)
        except Exception as exc:
            log.debug(f"Failed to push intel to device LCD: {exc}")

    # Events the meeting session emits that have a *dedicated* runtime path
    # already (`_on_meeting_segment` / `_on_meeting_intel` broadcast these,
    # and also drive the device LCDs). Forwarding them again from the generic
    # `on_broadcast` seam would double-broadcast, so they are filtered out.
    _BROADCAST_VIA_DEDICATED_HANDLER = frozenset({"segment", "intel_complete", "intel_status"})

    def _on_meeting_broadcast(self, message_type: str, data: object) -> None:
        """Observe live events `MeetingSession` emits (HS-32-02 inversion).

        The session no longer reaches into a web server; it emits, and the
        runtime forwards to its broadcast channel. ``segment`` /
        ``intel_complete`` / ``intel_status`` already flow via the dedicated
        ``on_segment`` / ``on_intel`` handlers, so only ``intel_token`` and
        ``meeting_updated`` — previously delivered solely to the now-removed
        embedded per-meeting server, and dead in the flagship runtime — are
        forwarded here.
        """
        if message_type in self._BROADCAST_VIA_DEDICATED_HANDLER:
            return
        self._map_meeting_broadcast_activity(message_type, data)
        if self.server is None:
            return
        try:
            self.server.broadcast(message_type, data)
        except Exception as exc:
            log.debug(f"Failed to forward meeting broadcast {message_type!r}: {exc}")

    def _map_meeting_broadcast_activity(self, message_type: str, data: object) -> None:
        if message_type == "intel_token":
            self._set_runtime_activity(
                "processing",
                source="meeting",
                label="Intel streaming",
                detail="Meeting intelligence is streaming.",
                last_event="meeting_intel_streaming",
                last_error="",
            )
            return
        if message_type == "actuator_proposed":
            label = "Action proposed"
            detail = "An actuator proposed an external action."
            if isinstance(data, dict):
                title = str(data.get("title") or data.get("preview") or "").strip()
                target = str(data.get("target") or "").strip()
                if title and target:
                    detail = f"{target}: {title}"
                elif title:
                    detail = title
            self._set_runtime_activity(
                "complete",
                source="meeting",
                label=label,
                detail=detail[:220],
                last_event="actuator_proposed",
                last_error="",
            )

    def _start_meeting(self, *, devices: Optional[list[str]] = None) -> dict[str, object]:
        if self._active_meeting_session() is not None:
            raise RuntimeError("Meeting already active")

        # Validate every requested device id is currently registered
        # *before* spinning up a session — surfaces 404 to the caller
        # without leaving an empty meeting on disk.
        device_pairs: list[tuple[object, object]] = []  # (descriptor, source)
        if devices:
            for device_id in devices:
                descriptor = self.device_registry.get(device_id)
                if descriptor is None:
                    raise _UnknownDeviceError(device_id)
                source = self.device_registry.recorder_for(device_id)
                if source is None:
                    raise _UnknownDeviceError(device_id)
                device_pairs.append((descriptor, source))

        if self.transcriber is None or getattr(self.transcriber, "model_name", None) != self.config.model.name:
            self.transcriber = self._ensure_transcriber_loaded()

        # HS-32-03: claim the shared audio floor before opening any recorder, so
        # a hotkey/device voice-typing session can't already hold the mic (and so
        # one can't grab it while the meeting runs). Released in
        # `_stop_active_meeting` / shutdown; released here if start-up fails
        # before the meeting is registered.
        if not self.voice_session.acquire(_MEETING_AUDIO_OWNER):
            raise RuntimeError(
                f"Cannot start meeting: audio floor held by {self.voice_session.active_owner!r}"
            )
        # HS-36-05: build the LLM-assisted per-segment intent probe only when the
        # config knob is on. Defensive: any failure to construct it (missing optional
        # deps, unconfigured endpoint) leaves it None and routing falls back to the
        # lexical path — meeting start must never break on this.
        segment_probe = None
        if getattr(self.config.meeting, "intent_segment_probe_enabled", False):
            try:
                from ..plugins.segment_probe import build_segment_probe

                segment_probe = build_segment_probe()
            except Exception:
                log.warning("segment intent probe unavailable; using lexical scoring", exc_info=True)
                segment_probe = None

        try:
            session = MeetingSession(
                transcriber=self.transcriber,
                mic_label=self.config.meeting.mic_label,
                remote_label=self.config.meeting.remote_label,
                mic_device=self.config.meeting.mic_device,
                system_device=self.config.meeting.system_audio_device,
                on_segment=self._on_meeting_segment,
                on_mic_level=lambda _level: None,
                on_system_level=lambda _level: None,
                on_intel=self._on_meeting_intel,
                on_settings_applied=self._apply_updated_config,
                on_broadcast=self._on_meeting_broadcast,
                intel_enabled=self.config.meeting.intel_enabled,
                intel_model_path=self.config.meeting.intel_realtime_model,
                intel_provider=self.config.meeting.intel_provider,
                intel_cloud_model=self.config.meeting.intel_cloud_model,
                intel_cloud_api_key_env=self.config.meeting.intel_cloud_api_key_env,
                intel_cloud_base_url=self.config.meeting.intel_cloud_base_url,
                intel_cloud_reasoning_effort=self.config.meeting.intel_cloud_reasoning_effort,
                intel_cloud_store=self.config.meeting.intel_cloud_store,
                intel_deferred_enabled=self.config.meeting.intel_deferred_enabled,
                diarization_enabled=self.config.meeting.diarization_enabled,
                diarize_mic=self.config.meeting.diarize_mic,
                cross_meeting_recognition=self.config.meeting.cross_meeting_recognition,
                mir_disabled_plugins=list(
                    getattr(self.config.meeting, "disabled_plugins", []) or []
                ),
                mir_segment_probe=segment_probe,
            )
            state = session.start()
            with self.state_lock:
                title_override = self.pending_title
                tags_override = list(self.pending_tags) if self.pending_tags is not None else None
                self.pending_title = None
                self.pending_tags = None
            if title_override is not None:
                session.set_title(title_override)
                state = session.state or state
            if tags_override is not None:
                session.set_tags(tags_override)
                state = session.state or state
            if self.runtime_url:
                state.web_url = self.runtime_url

            attached_ids: list[str] = []
            for descriptor, source in device_pairs:
                try:
                    session.attach_device(descriptor, source)  # type: ignore[arg-type]
                    attached_ids.append(getattr(descriptor, "id", ""))
                except Exception as exc:
                    log.error(f"Failed to attach device {getattr(descriptor, 'id', '?')}: {exc}")
                    # Best effort: continue with whatever attached successfully.
                    # The descriptors that *did* attach remain on state.devices.
                    continue

            with self.meeting_lock:
                self.meeting_session = session
        except Exception:
            # Roll back the floor claim if the meeting never came up.
            self.voice_session.release(_MEETING_AUDIO_OWNER)
            self._set_runtime_activity(
                "error",
                source="meeting",
                detail="Meeting start failed.",
                last_event="meeting_start_failed",
                last_error="Meeting start failed",
            )
            raise

        if attached_ids:
            attached_for_status = [d for d in attached_ids if d]
            self.device_status.broadcast(
                attached_for_status,
                "Recording 00:00",
                ttl_ms=0,
            )
            # HS-17-05: schedule the periodic Recording-tick. The 0:00
            # paint above is done synchronously; subsequent ticks fire
            # every 5 s on a daemon thread that exits cleanly on
            # `_stop_active_meeting`.
            self.recording_ticker.start(
                started_at_monotonic=time.monotonic(),
                device_ids=attached_for_status,
            )
        with self.state_lock:
            self.pending_intent_windows.clear()
            self.pending_plugin_runs.clear()
            self.preview_window_seq = 0
        with self.state_lock:
            self.runtime_status["last_error"] = ""
        self._set_runtime_activity(
            "meeting_live",
            source="meeting",
            detail="Meeting recording is live.",
            last_event="meeting_started",
            last_error="",
        )

        self._broadcast_intel_status()
        return state.to_dict()

    def _stop_active_meeting(self, *, allow_runtime_fallback: bool) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is None:
            if allow_runtime_fallback:
                self.runtime_stop_event.set()
                return {"status": "stopping_runtime"}
            raise RuntimeError("No active meeting")

        # HS-14-07: notify any attached devices that we are about to
        # stop and persist. Captured *before* ``session.stop`` flips
        # the state and clears the device list.
        attached_ids = [d.id for d in session.state.devices] if session.state else []
        # HS-17-05: stop the Recording-tick *before* the
        # `Saving meeting...` broadcast so a stale tick can't land
        # after the user has been told the meeting is saving.
        self.recording_ticker.stop()
        # AIPI-4-14: reset per-device cycle indexes so the next meeting
        # starts the double-tap rotation back at view 0.
        self.device_stats_cycle.clear()
        if attached_ids:
            self.device_status.broadcast(attached_ids, "Saving meeting...", ttl_ms=0)
        self._set_runtime_activity(
            "saving",
            source="meeting",
            detail="Stopping and saving meeting.",
            last_event="meeting_saving",
            last_error="",
        )

        final_state = session.stop()
        # HS-32-03: the meeting's recorder is now closed — release the shared
        # audio floor immediately (before the slower save/intel work, none of
        # which touches the mic) so hotkey/device voice typing can resume.
        self.voice_session.release(_MEETING_AUDIO_OWNER)
        final_state_payload = final_state.to_dict()
        meeting_id = str(final_state_payload.get("id") or "")
        with self.state_lock:
            self.last_meeting_snapshot = dict(final_state_payload)
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
            queue_flush = self._flush_deferred_plugin_runs_to_db()
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
                mir_history = self._persist_pending_mir_history(meeting_id)
                save_payload["intent_windows_saved"] = int(mir_history.get("intent_windows_saved") or 0)
                save_payload["plugin_runs_saved"] = int(mir_history.get("plugin_runs_saved") or 0)
                save_payload["mir_save_error"] = mir_history.get("error")
                artifacts_result = self._synthesize_and_persist_artifacts(meeting_id)
                save_payload["artifacts_saved"] = int(artifacts_result.get("artifacts_saved") or 0)
                save_payload["artifact_synthesis_error"] = artifacts_result.get("error")
                project_result = self._associate_meeting_with_projects(meeting_id)
                save_payload["projects_associated"] = int(project_result.get("projects_associated") or 0)
                save_payload["project_association_error"] = project_result.get("error")
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to save meeting from web runtime: {exc}")

        with self.meeting_lock:
            if self.meeting_session is session:
                self.meeting_session = None

        with self.state_lock:
            self.runtime_status["last_error"] = save_error or ""
        if save_error:
            self._set_runtime_activity(
                "error",
                source="meeting",
                detail="Meeting save failed.",
                last_event="meeting_save_failed",
                last_error=save_error,
            )
        else:
            self._set_runtime_activity(
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
        }

    def _on_bookmark(self, label: str) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is not None:
            bookmark = session.add_bookmark(label=label, auto_label=not bool(label))
            if bookmark is not None:
                attached_ids = [d.id for d in session.state.devices] if session.state else []
                if attached_ids:
                    self.device_status.broadcast(
                        attached_ids,
                        f"Bookmark @ {bookmark.timestamp:.0f}s",
                        ttl_ms=2500,
                    )
                return bookmark.to_dict()
            raise RuntimeError("No active meeting")

        entry = {
            "timestamp": max(0.0, (datetime.now() - self.runtime_started_at).total_seconds()),
            "label": label or "",
        }
        with self.state_lock:
            self.bookmarks.append(entry)
        return entry

    def _on_stop(self) -> dict[str, object]:
        return self._stop_active_meeting(allow_runtime_fallback=True)

    def _on_meeting_stop(self) -> dict[str, object]:
        return self._stop_active_meeting(allow_runtime_fallback=False)

    def _on_update_meeting(self, *, title: Optional[str], tags: Optional[list[str]]) -> dict[str, object]:
        session = self._active_meeting_session()
        clean_tags = self._normalize_tags(tags) if tags is not None else None

        if session is not None:
            if title is not None:
                session.set_title(title)
            if clean_tags is not None:
                session.set_tags(clean_tags)
            state = session.state
            return state.to_dict() if state is not None else self._runtime_idle_state()

        with self.state_lock:
            if title is not None:
                self.pending_title = str(title).strip()
            if clean_tags is not None:
                self.pending_tags = clean_tags
        return self._runtime_idle_state()

    def _on_update_action_item(self, item_id: str, status: str):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.update_action_item(item_id, status)

    def _on_update_action_item_review(self, item_id: str, review_state: str):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.update_action_item_review(item_id, review_state)

    def _on_edit_action_item(self, item_id: str, *, task: str, owner: Optional[str], due: Optional[str]):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.edit_action_item(item_id, task=task, owner=owner, due=due)
