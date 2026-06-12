"""The MIR / routing glue (HS-63-04).

Intent controls, the route preview, preview-history persistence, MIR
history + artifact persistence, and project association — verbatim moves
out of WebRuntime.
"""

from __future__ import annotations

import hashlib
from typing import Optional

import numpy as np

from ..logging_config import get_logger
from ..plugins.router import (
    DEFAULT_INTENT_THRESHOLD,
    SUPPORTED_INTENTS,
    available_profiles,
    normalize_override_intents,
    normalize_profile,
    preview_route,
)
from ..plugins.host import build_idempotency_key
from ..plugins.signals import extract_intent_signals

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class RoutingGlueMixin:
    def _mir_controls_payload(self) -> dict[str, object]:
        with self.state_lock:
            return {
                "enabled": bool(self.mir_enabled),
                "profile": str(self.mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(self.mir_override_intents),
                "last_preview": dict(self.last_route_preview) if isinstance(self.last_route_preview, dict) else None,
                "threshold": float(DEFAULT_INTENT_THRESHOLD),
            }

    def _infer_intent_scores(self, *, transcript: Optional[str], tags: Optional[list[str]]) -> dict[str, float]:
        return extract_intent_signals(transcript, tags=tags)

    def _derive_preview_transcript_hash(
        self,
        *,
        transcript: Optional[str],
        intent_scores: Optional[dict[str, object]],
    ) -> tuple[str, str]:
        transcript_text = str(transcript or "").strip()
        if transcript_text:
            return hashlib.sha256(transcript_text.encode("utf-8")).hexdigest(), transcript_text[:400]
        score_blob = str(intent_scores if isinstance(intent_scores, dict) else {})
        return hashlib.sha256(score_blob.encode("utf-8")).hexdigest(), ""

    def _build_active_preview_window_context(
        self,
        *,
        transcript: Optional[str],
        route_payload: dict[str, object],
    ) -> Optional[dict[str, object]]:
        session = self._active_meeting_session()
        if session is None:
            return None

        state = session.state
        if state is None:
            return None

        meeting_id = str(state.id or "").strip()
        if not meeting_id:
            return None

        self.preview_window_seq += 1
        transcript_hash, transcript_excerpt = self._derive_preview_transcript_hash(
            transcript=transcript,
            intent_scores=route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else None,
        )
        state_payload = state.to_dict()
        end_seconds = float(state_payload.get("duration") or 0.0)
        start_seconds = max(0.0, end_seconds - 90.0)
        return {
            "meeting_id": meeting_id,
            "window_id": f"{meeting_id}:preview-{self.preview_window_seq:04d}",
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "transcript_hash": transcript_hash,
            "transcript_excerpt": transcript_excerpt,
        }

    def _record_route_preview_history(
        self,
        *,
        route_payload: dict[str, object],
        tags: Optional[list[str]],
        window_context: dict[str, object],
        plugin_runs: list[dict[str, object]],
    ) -> None:
        meeting_id = str(window_context.get("meeting_id") or "").strip()
        window_id = str(window_context.get("window_id") or "").strip()
        transcript_hash = str(window_context.get("transcript_hash") or "").strip()
        if not meeting_id or not window_id:
            return

        active_intents = route_payload.get("active_intents") if isinstance(route_payload.get("active_intents"), list) else []
        override_intents = route_payload.get("override_intents") if isinstance(route_payload.get("override_intents"), list) else []
        intent_scores = route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else {}
        clean_tags = [str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()]

        with self.state_lock:
            self.pending_intent_windows.append(
                {
                    "meeting_id": meeting_id,
                    "window_id": window_id,
                    "start_seconds": float(window_context.get("start_seconds") or 0.0),
                    "end_seconds": float(window_context.get("end_seconds") or 0.0),
                    "transcript_hash": transcript_hash,
                    "transcript_excerpt": str(window_context.get("transcript_excerpt") or ""),
                    "profile": str(route_payload.get("profile") or "balanced"),
                    "threshold": float(route_payload.get("threshold") or DEFAULT_INTENT_THRESHOLD),
                    "active_intents": [str(intent).strip().lower() for intent in active_intents if str(intent).strip()],
                    "intent_scores": {
                        str(intent).strip().lower(): float(score)
                        for intent, score in intent_scores.items()
                        if str(intent).strip()
                    },
                    "override_intents": [str(intent).strip().lower() for intent in override_intents if str(intent).strip()],
                    "tags": clean_tags,
                    "metadata": {
                        "source": "route_preview",
                        "hysteresis_applied": bool(route_payload.get("hysteresis_applied")),
                    },
                }
            )

            for run in plugin_runs:
                plugin_id = str(run.get("plugin_id") or "").strip()
                if not plugin_id:
                    continue
                run_transcript_hash = str(run.get("transcript_hash") or transcript_hash)
                self.pending_plugin_runs.append(
                    {
                        "meeting_id": meeting_id,
                        "window_id": window_id,
                        "plugin_id": plugin_id,
                        "plugin_version": str(run.get("plugin_version") or "unknown"),
                        "status": str(run.get("status") or "unknown"),
                        "idempotency_key": str(run.get("idempotency_key") or "").strip()
                        or build_idempotency_key(
                            meeting_id=meeting_id,
                            window_id=window_id,
                            plugin_id=plugin_id,
                            transcript_hash=run_transcript_hash,
                        ),
                        "duration_ms": float(run.get("duration_ms") or 0.0),
                        "output": run.get("output") if isinstance(run.get("output"), dict) else None,
                        "error": str(run.get("error")) if run.get("error") else None,
                        "deduped": bool(run.get("deduped")),
                    }
                )

    def _persist_pending_mir_history(self, meeting_id: str) -> dict[str, object]:
        with self.state_lock:
            windows_to_save = [dict(item) for item in self.pending_intent_windows if str(item.get("meeting_id")) == meeting_id]
            runs_to_save = [dict(item) for item in self.pending_plugin_runs if str(item.get("meeting_id")) == meeting_id]
            self.pending_intent_windows[:] = [
                item for item in self.pending_intent_windows if str(item.get("meeting_id")) != meeting_id
            ]
            self.pending_plugin_runs[:] = [
                item for item in self.pending_plugin_runs if str(item.get("meeting_id")) != meeting_id
            ]

        saved_windows = 0
        saved_runs = 0
        save_error: Optional[str] = None
        if not windows_to_save and not runs_to_save:
            return {
                "intent_windows_saved": 0,
                "plugin_runs_saved": 0,
                "error": None,
            }

        try:
            from ..db import get_database

            db = get_database()
            for record in windows_to_save:
                db.plugins.record_intent_window(**record)
                saved_windows += 1
            for record in runs_to_save:
                db.plugins.record_plugin_run(**record)
                saved_runs += 1
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to persist MIR history for meeting {meeting_id}: {exc}")

        return {
            "intent_windows_saved": saved_windows,
            "plugin_runs_saved": saved_runs,
            "error": save_error,
        }

    def _synthesize_and_persist_artifacts(self, meeting_id: str) -> dict[str, object]:
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"artifacts_saved": 0, "error": None}

        try:
            from ..db import get_database
            from ..plugins.synthesis import synthesize_meeting_artifacts

            db = get_database()
            runs = db.plugins.list_plugin_runs(clean_meeting_id, limit=5000)
            artifacts = synthesize_meeting_artifacts(
                meeting_id=clean_meeting_id,
                plugin_runs=runs,
                max_artifacts=500,
            )
            for artifact in artifacts:
                db.plugins.record_artifact(
                    artifact_id=artifact.artifact_id,
                    meeting_id=artifact.meeting_id,
                    artifact_type=artifact.artifact_type,
                    title=artifact.title,
                    body_markdown=artifact.body_markdown,
                    structured_json=artifact.structured_json,
                    confidence=artifact.confidence,
                    status=artifact.status,
                    plugin_id=artifact.plugin_id,
                    plugin_version=artifact.plugin_version,
                    sources=[source.to_dict() for source in artifact.sources],
                )
            return {"artifacts_saved": len(artifacts), "error": None}
        except Exception as exc:
            message = str(exc)
            log.error(f"Failed to synthesize artifacts for meeting {clean_meeting_id}: {message}")
            return {"artifacts_saved": 0, "error": message}

    def _associate_meeting_with_projects(self, meeting_id: str) -> dict[str, object]:
        """Auto-associate a meeting with projects based on project_detector plugin runs."""
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"projects_associated": 0, "error": None}

        try:
            from ..db import get_database
            db = get_database()
            runs = db.plugins.list_plugin_runs(clean_meeting_id, limit=5000)

            # Filter to successful project_detector runs
            detector_runs = [
                r for r in runs
                if r.plugin_id == "project_detector" and r.status in ("success", "deduped")
                and r.output
            ]

            if not detector_runs:
                return {"projects_associated": 0, "error": None}

            # Aggregate max score per project across all windows
            project_max_scores: dict[str, dict[str, object]] = {}
            for run in detector_runs:
                matched = run.output.get("matched_projects") or []
                for match in matched:
                    pid = str(match.get("project_id") or "").strip()
                    if not pid:
                        continue
                    score = float(match.get("score") or 0)
                    threshold = float(match.get("detection_threshold") or 0.4)
                    existing = project_max_scores.get(pid)
                    if existing is None or score > float(existing["max_score"]):
                        project_max_scores[pid] = {
                            "max_score": score,
                            "threshold": threshold,
                        }
                    # Log each window detection
                    db.projects.log_project_detection(
                        meeting_id=clean_meeting_id,
                        project_id=pid,
                        window_id=run.window_id,
                        score=score,
                        keyword_hits=match.get("keyword_hits"),
                        member_hits=match.get("member_hits"),
                    )

            # Associate meeting with projects that exceed their threshold
            associated = 0
            for pid, data in project_max_scores.items():
                max_score = float(data["max_score"])
                threshold = float(data["threshold"])
                if max_score >= threshold:
                    db.projects.associate_meeting_project(
                        meeting_id=clean_meeting_id,
                        project_id=pid,
                        source="auto",
                        confidence=max_score,
                    )
                    associated += 1

            return {"projects_associated": associated, "error": None}
        except Exception as exc:
            message = str(exc)
            log.error(f"Failed to associate meeting {clean_meeting_id} with projects: {message}")
            return {"projects_associated": 0, "error": message}

    def _on_get_intent_controls(self) -> dict[str, object]:
        return self._mir_controls_payload()

    def _on_set_intent_profile(self, profile: str) -> dict[str, object]:
        with self.state_lock:
            self.mir_profile = normalize_profile(profile)
        return self._mir_controls_payload()

    def _on_set_intent_override(self, intents: Optional[list[str]]) -> dict[str, object]:
        with self.state_lock:
            self.mir_override_intents = normalize_override_intents(intents)
        return self._mir_controls_payload()

    def _on_route_preview(
        self,
        *,
        profile: Optional[str] = None,
        threshold: Optional[float] = None,
        intent_scores: Optional[dict[str, float]] = None,
        override_intents: Optional[list[str]] = None,
        previous_intents: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        transcript: Optional[str] = None,
    ) -> dict[str, object]:
        controls = self._mir_controls_payload()
        profile_value = normalize_profile(profile or str(controls.get("profile") or ""))
        threshold_value = DEFAULT_INTENT_THRESHOLD if threshold is None else float(threshold)

        inferred_scores = self._infer_intent_scores(transcript=transcript, tags=tags)
        provided_scores = intent_scores if isinstance(intent_scores, dict) else {}
        effective_scores = dict(inferred_scores)
        effective_scores.update(provided_scores)

        if isinstance(override_intents, list):
            effective_override = normalize_override_intents(override_intents)
        else:
            effective_override = normalize_override_intents(controls.get("override_intents"))  # type: ignore[arg-type]

        route = preview_route(
            profile=profile_value,
            intent_scores=effective_scores,
            threshold=threshold_value,
            previous_intents=previous_intents,
            override_intents=effective_override,
        )
        route_payload = route.to_dict()
        route_payload["mir_enabled"] = bool(controls.get("enabled"))
        window_context = self._build_active_preview_window_context(
            transcript=transcript,
            route_payload=route_payload,
        )
        transcript_hash, _ = self._derive_preview_transcript_hash(
            transcript=transcript,
            intent_scores=route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else None,
        )

        execution_meeting_id = (
            str(window_context.get("meeting_id"))
            if isinstance(window_context, dict) and window_context.get("meeting_id")
            else "web-runtime-preview"
        )
        execution_window_id = (
            str(window_context.get("window_id"))
            if isinstance(window_context, dict) and window_context.get("window_id")
            else f"{execution_meeting_id}:preview"
        )
        execution_context = {
            "transcript": str(transcript or ""),
            "tags": [str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()],
            "active_intents": list(route_payload.get("active_intents") or []),
            "intent_scores": dict(route_payload.get("intent_scores") or {}),
            "profile": route_payload.get("profile"),
            "threshold": route_payload.get("threshold"),
        }
        run_results = self.plugin_host.execute_chain(
            list(route_payload.get("plugin_chain") or []),
            context=execution_context,
            meeting_id=execution_meeting_id,
            window_id=execution_window_id,
            transcript_hash=transcript_hash,
        )
        route_payload["plugin_runs"] = [result.to_dict() for result in run_results]
        queue_flush = self._flush_deferred_plugin_runs_to_db()
        route_payload["deferred_queue_jobs"] = int(queue_flush.get("queued_jobs") or 0)
        if queue_flush.get("error"):
            route_payload["deferred_queue_error"] = str(queue_flush["error"])

        if isinstance(window_context, dict):
            self._record_route_preview_history(
                route_payload=route_payload,
                tags=tags,
                window_context=window_context,
                plugin_runs=route_payload["plugin_runs"],  # type: ignore[arg-type]
            )

        with self.state_lock:
            self.last_route_preview = dict(route_payload)

        return route_payload
