"""Transport-neutral settings read and update service (HS-123-03)."""

from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import replace
from typing import Any, Callable
from urllib.parse import urlparse

from holdspeak.config import Config
from holdspeak.db.core import Database
from holdspeak.principals import Principal
from holdspeak.services.errors import ConflictError, ValidationError

SettingsApplied = Callable[[Config], None]
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")
_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
SECRET_PATHS = {
    "web_token": ("meeting", "web_auth_token"),
    "device_psk": ("device", "psk"),
    "telegram_bot_token": ("cadence_telegram", "bot_token"),
    "telegram_pairing_code": ("cadence_telegram", "pairing_code"),
    "failure_webhook_url": ("meeting", "intel_retry_failure_webhook_url"),
    "failure_webhook_credential": (
        "meeting",
        "intel_retry_failure_webhook_header_value",
    ),
    "slack_webhook_url": ("meeting", "slack_webhook_url"),
    "companion_webhook_url": ("meeting", "companion_webhook_url"),
}


# HS-130-07: the settings document's optimistic-concurrency token. It is a
# content hash of the persisted config — a stable, stateless revision that
# needs no new persisted field and no schema migration. A GET carries it as
# `_revision`; a PUT echoes the revision it read. The server rejects a PUT
# whose echoed revision no longer matches the on-disk config (a concurrent
# surface already wrote), so two open surfaces reconcile rather than clobber.
REVISION_KEY = "_revision"


def settings_revision(config: Config) -> str:
    """A deterministic short hash of the persisted config."""
    canonical = json.dumps(config.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# HS-132-10: the read-only provenance block. The settings document is where a
# person SETS meetings placement, so the document states which dial actually
# decided and what that decision loaded. It is derived, never persisted: the
# writer strips it back off on the way in (see `_update`).
PLACEMENT_KEY = "_placement"
CALENDAR_SUBSCRIPTION_KEY = "_calendar_subscription"


def meeting_placement_summary(config: Config) -> dict[str, Any]:
    """Describe the ONE meetings placement decision for the surface that sets it.

    Reuses the placement authority (``resolve_meeting_placement``) and the
    deployment describer (``configured_meeting_deployment``) — this shapes their
    answer for the wire, it never re-decides. ``provider_honored`` is false
    exactly when an adopted destination decided, which is the state the web
    Provider dial used to hide (a silent no-op, issue #450 defect 4).
    """
    from holdspeak.intel.providers import (
        PLACEMENT_DESTINATION,
        configured_meeting_deployment,
        resolve_meeting_placement,
    )

    meeting = getattr(config, "meeting", None)
    try:
        placement = resolve_meeting_placement(meeting)
        deployment = configured_meeting_deployment(meeting=meeting)
    except Exception as exc:  # never let a describer break the settings read
        return {
            "placement_source": "",
            "placement_reason": f"placement unavailable ({exc.__class__.__name__})",
            "provider_intent": str(getattr(meeting, "intel_provider", "") or ""),
            "provider_honored": True,
            "boundary": "",
            "target_id": "",
            "target_name": "",
            "engine": "",
            "model": "",
            "node": "",
            "runnable": False,
            "runnable_reason": f"placement unavailable ({exc.__class__.__name__})",
        }
    return {
        "placement_source": str(placement.source or ""),
        "placement_reason": str(placement.reason or ""),
        "provider_intent": str(getattr(meeting, "intel_provider", "") or ""),
        "provider_honored": placement.source != PLACEMENT_DESTINATION,
        "boundary": str(placement.boundary or ""),
        "target_id": str(placement.profile_id or ""),
        "target_name": str(placement.profile_name or ""),
        "engine": str(deployment.engine or ""),
        "model": str(deployment.model or ""),
        "node": str(deployment.node or ""),
        "runnable": bool(deployment.runnable),
        "runnable_reason": str(deployment.reason or ""),
    }


def redacted_settings(
    config: Config, *, include_meeting_placement: bool = True
) -> dict[str, Any]:
    """Return settings safe for transport.

    ``include_meeting_placement`` is intentionally decided by the settings
    service's per-family migration marker.  Once Meeting routes are assigned,
    recalculating this legacy placement projection would be a fresh mutable
    selector hidden inside a harmless-looking GET.
    """
    from holdspeak.config import (
        LEGACY_ENDPOINT_FIELDS,
        calendar_subscription_summary,
    )

    payload = deepcopy(config.to_dict())
    payload[REVISION_KEY] = settings_revision(config)
    payload[CALENDAR_SUBSCRIPTION_KEY] = calendar_subscription_summary(
        config.calendar.subscription
    )
    if include_meeting_placement:
        # The provenance rides both the read and the write's echo, so a surface
        # that changes the dial sees the new placement without a reload.
        payload[PLACEMENT_KEY] = {"meeting": meeting_placement_summary(config)}
    for path, fields in LEGACY_ENDPOINT_FIELDS.items():
        node: Any = payload
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            for field in fields:
                node.pop(field, None)
    states = {}
    for secret_id, (section, field) in SECRET_PATHS.items():
        section_data = payload.get(section)
        if not isinstance(section_data, dict):
            continue
        value = str(section_data.pop(field, "") or "")
        state = {"configured": bool(value)}
        if secret_id in {
            "failure_webhook_url",
            "slack_webhook_url",
            "companion_webhook_url",
        }:
            host = urlparse(value).hostname
            if host:
                state["destination"] = host.lower()
        states[secret_id] = state
    payload["_secrets"] = states
    return payload


def strip_secret_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(payload)
    clean.pop("_secrets", None)
    for section, field in SECRET_PATHS.values():
        if isinstance(clean.get(section), dict):
            clean[section].pop(field, None)
    if isinstance(clean.get("meeting"), dict):
        clean["meeting"].pop("intel_retry_failure_webhook_header_name", None)
    return clean


def _strip_legacy_endpoint_fields(payload: dict[str, Any]) -> dict[str, Any]:
    from holdspeak.config import LEGACY_ENDPOINT_FIELDS

    for path, fields in LEGACY_ENDPOINT_FIELDS.items():
        node: Any = payload
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            for field in fields:
                node.pop(field, None)
    return payload


def _merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _merge_dict(dst[key], value)
        else:
            dst[key] = value
    return dst


@observe_service
class SettingsService:
    def __init__(
        self, db: Database, on_settings_applied: SettingsApplied | None = None
    , *, observer: PipelineObserver | None = None) -> None:
        self._db, self._on_settings_applied = db, on_settings_applied
        self._observer = observer or NullObserver()

    def get_settings(self, principal: Principal) -> dict[str, Any]:
        return self.get_redacted(principal)

    def get_redacted(self, principal: Principal) -> dict[str, Any]:
        thought_routes = self._assignment_migration_active(
            "thoughts-writing-route-assignments"
        )
        meeting_routes = self._assignment_migration_active("meeting-route-assignments")
        rails_routes = self._assignment_migration_active(
            "rails-observer-route-assignments"
        )
        result = redacted_settings(
            Config.load(), include_meeting_placement=not meeting_routes
        )
        if thought_routes:
            result.get("thoughts", {}).pop("inference_target_id", None)
            result.get("dictation", {}).get("runtime", {}).pop("profile_id", None)
        if meeting_routes:
            meeting = result.get("meeting", {})
            if isinstance(meeting, dict):
                # These retained Config bytes are migration evidence only.  A
                # post-marker Settings response must not expose a second Meeting
                # selection surface or recalculate its old placement.
                meeting.pop("intel_profile_id", None)
                meeting.pop("intel_provider", None)
        if rails_routes:
            rails = result.get("rails_observer", {})
            if isinstance(rails, dict):
                rails.pop("profile_id", None)
        return result

    def _assignment_migration_active(self, family: str) -> bool:
        with self._db._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM inference_assignment_migrations WHERE family=?", (family,)
            ).fetchone() is not None

    def _routed_assignments_active(self) -> bool:
        """Compatibility name for the pre-existing Thought/writing gate."""
        return self._assignment_migration_active("thoughts-writing-route-assignments")

    def update_settings(
        self, principal: Principal, patch: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(patch, dict):
            raise ValidationError("Settings patch must be an object")
        if self._routed_assignments_active() and (
            "inference_target_id" in dict(patch.get("thoughts") or {})
            or "profile_id" in dict(dict(patch.get("dictation") or {}).get("runtime") or {})
        ):
            raise ValidationError(
                "Legacy inference selectors are unavailable after assignment migration.",
                code="inference_legacy_selector_retired",
            )
        meeting_patch = dict(patch.get("meeting") or {})
        if self._assignment_migration_active("meeting-route-assignments") and (
            {"intel_profile_id", "intel_provider"} & set(meeting_patch)
        ):
            raise ValidationError(
                "Legacy Meeting routing selectors are unavailable after assignment migration.",
                code="meeting_legacy_selector_retired",
            )
        rails_patch = dict(patch.get("rails_observer") or {})
        if self._assignment_migration_active("rails-observer-route-assignments") and (
            "profile_id" in rails_patch
        ):
            raise ValidationError(
                "The Rails observer profile selector is unavailable after assignment migration.",
                code="rails_observer_legacy_selector_retired",
            )
        # HS-130-07: optimistic concurrency. A client that read a revision must
        # echo it; if the on-disk config has moved since, the partial-tree write
        # would silently clobber the concurrent surface's edit, so we reject it
        # with a reconcilable conflict carrying the current revision. A patch
        # that omits the token (a legacy caller) is applied last-writer-wins as
        # before — the guard is opt-in per writer.
        patch = dict(patch)
        expected = patch.pop(REVISION_KEY, None)
        if expected is not None:
            current_revision = settings_revision(Config.load())
            if str(expected) != current_revision:
                raise ConflictError(
                    "Settings changed in another surface since you loaded them. "
                    "Reload and reapply your edit.",
                    code="settings_stale",
                    context={"revision": current_revision},
                )
        result = self._update(patch)
        if result.get("success") is False:
            raise ValidationError(str(result["error"]))
        return result

    def _update(self, patch: dict[str, Any]) -> dict[str, Any]:
        from holdspeak.config import (
            Config,
            CalendarConfig,
            DeviceConfig,
            DictationConfig,
            DictationConfigError,
            DictationPipelineConfig,
            HotkeyConfig,
            KEY_DISPLAY,
            KEY_MAP,
            LLMRuntimeConfig,
            MacrosConfig,
            MeetingConfig,
            ModelConfig,
            PresenceConfig,
            RailsObserverConfig,
            ThoughtsConfig,
            UIConfig,
            VoiceMacroError,
            WakeWordConfig,
            validate_calendar_subscription,
        )

        current = Config.load()
        merged = deepcopy(current.to_dict())
        _merge_dict(
            merged,
            _strip_legacy_endpoint_fields(strip_secret_mutations(patch)),
        )

        hotkey_data = merged.get("hotkey", {})
        model_data = merged.get("model", {})
        ui_data = merged.get("ui", {})
        meeting_data = merged.get("meeting", {})
        device_data = merged.get("device", {})
        presence_data = merged.get("presence", {})

        hotkey_key = str(hotkey_data.get("key", current.hotkey.key))
        if hotkey_key not in KEY_MAP:
            return {"success": False, "error": f"Invalid hotkey key: {hotkey_key}"}
        hotkey_data["key"] = hotkey_key
        hotkey_data["display"] = KEY_DISPLAY.get(hotkey_key, hotkey_key)

        # HS-139-02: strip defaulted keys — these dials are removed from
        # the settings surface and the service-writable set. A stale
        # client echoing them back gets the value silently dropped so
        # the pinned default governs.
        _DEFAULTED_MODEL = {"name", "warm_on_start"}
        _DEFAULTED_MEETING = {
            "mic_label", "remote_label", "cross_meeting_recognition",
            "web_auto_open", "intel_enabled", "intel_deferred_enabled",
            "mir_enabled",
        }
        for _dk in _DEFAULTED_MODEL:
            model_data.pop(_dk, None)
        for _dk in _DEFAULTED_MEETING:
            meeting_data.pop(_dk, None)
        # HS-59: validate the transcription language at the boundary so a
        # typo fails the settings write, not a dictation later. Store the
        # normalized code ("auto" for detection).
        from holdspeak.languages import normalize_language

        raw_language = model_data.get("language", current.model.language)
        try:
            normalized = normalize_language(raw_language)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        model_data["language"] = normalized or "auto"

        # --- HS-60: wake-word validation (strict at the boundary) ---
        wake_data = merged.get("wake_word", {}) or {}
        current_wake = getattr(current, "wake_word", WakeWordConfig())
        wake_action = str(wake_data.get("action", current_wake.action)).strip().lower()
        if wake_action not in ("preview", "type"):
            return {
                "success": False,
                "error": f"wake_word.action must be 'preview' or 'type', got {wake_action!r}",
            }
        wake_data["action"] = wake_action
        try:
            wake_threshold = float(wake_data.get("threshold", current_wake.threshold))
        except (TypeError, ValueError):
            return {"success": False, "error": "wake_word.threshold must be a number"}
        if not (0.0 <= wake_threshold <= 1.0):
            return {
                "success": False,
                "error": "wake_word.threshold must be between 0 and 1",
            }
        wake_data["threshold"] = wake_threshold
        try:
            wake_window = float(
                wake_data.get("armed_window_seconds", current_wake.armed_window_seconds)
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "wake_word.armed_window_seconds must be a number",
            }
        if not (2.0 <= wake_window <= 30.0):
            return {
                "success": False,
                "error": "wake_word.armed_window_seconds must be between 2 and 30",
            }
        wake_data["armed_window_seconds"] = wake_window
        wake_model = str(wake_data.get("model", current_wake.model)).strip()
        if not wake_model:
            return {"success": False, "error": "wake_word.model must not be empty"}
        wake_data["model"] = wake_model
        wake_data["enabled"] = bool(wake_data.get("enabled", current_wake.enabled))

        # --- UIConfig validation (HS-139-01: theme/history_lines/show_audio_meter
        # deleted — dead settings with no runtime consumer) ---
        # Strip any legacy keys a stale client might echo back.
        for _dead_ui in ("theme", "history_lines", "show_audio_meter"):
            ui_data.pop(_dead_ui, None)
        ui_data["desk_sounds"] = bool(
            ui_data.get("desk_sounds", current.ui.desk_sounds)
        )

        # --- Optional string / bool fields in MeetingConfig ---
        meeting_data["mic_device"] = (
            str(meeting_data.get("mic_device") or "").strip() or None
        )
        meeting_data["system_audio_device"] = (
            str(meeting_data.get("system_audio_device") or "").strip() or None
        )
        meeting_data["auto_export"] = bool(
            meeting_data.get("auto_export", current.meeting.auto_export)
        )
        meeting_data["intel_summary_model"] = (
            str(meeting_data.get("intel_summary_model") or "").strip() or None
        )
        meeting_data["intel_cloud_reasoning_effort"] = (
            str(meeting_data.get("intel_cloud_reasoning_effort") or "").strip() or None
        )

        export_format = str(
            meeting_data.get("export_format", current.meeting.export_format)
        )
        if export_format not in {"txt", "markdown", "json", "srt"}:
            return {
                "success": False,
                "error": f"Invalid export format: {export_format}",
            }
        meeting_data["export_format"] = export_format

        intel_provider = str(
            meeting_data.get("intel_provider", current.meeting.intel_provider)
        ).lower()
        if intel_provider not in {"local", "cloud", "auto"}:
            return {
                "success": False,
                "error": f"Invalid intel provider: {intel_provider}",
            }
        meeting_data["intel_provider"] = intel_provider

        from holdspeak.plugins.router import available_profiles

        # HS-139-02: mir_enabled stripped above (pinned true).
        # HS-130-05 / HS-134-08: the ONE routing profile. Accept
        # `routing_profile`; tolerate a stale `mir_profile` key from an
        # older client (drop after reading).
        routing_profile = (
            str(
                meeting_data.get(
                    "routing_profile",
                    meeting_data.get(
                        "mir_profile", current.meeting.effective_routing_profile()
                    ),
                )
            )
            .strip()
            .lower()
        )
        if routing_profile not in set(available_profiles()):
            return {"success": False, "error": f"Invalid routing profile: {routing_profile}"}
        meeting_data["routing_profile"] = routing_profile
        meeting_data.pop("mir_profile", None)

        # HS-139-01: intel_queue_poll_seconds deleted (dead — never threaded
        # to IntelQueue). Strip a stale client echo.
        meeting_data.pop("intel_queue_poll_seconds", None)

        retry_base_seconds = int(
            meeting_data.get(
                "intel_retry_base_seconds", current.meeting.intel_retry_base_seconds
            )
        )
        if retry_base_seconds < 1:
            return {
                "success": False,
                "error": "intel_retry_base_seconds must be at least 1",
            }
        meeting_data["intel_retry_base_seconds"] = retry_base_seconds

        retry_max_seconds = int(
            meeting_data.get(
                "intel_retry_max_seconds", current.meeting.intel_retry_max_seconds
            )
        )
        if retry_max_seconds < retry_base_seconds:
            return {
                "success": False,
                "error": "intel_retry_max_seconds must be >= intel_retry_base_seconds",
            }
        meeting_data["intel_retry_max_seconds"] = retry_max_seconds

        retry_max_attempts = int(
            meeting_data.get(
                "intel_retry_max_attempts", current.meeting.intel_retry_max_attempts
            )
        )
        if retry_max_attempts < 1:
            return {
                "success": False,
                "error": "intel_retry_max_attempts must be at least 1",
            }
        meeting_data["intel_retry_max_attempts"] = retry_max_attempts

        # HS-139-01: intel_retry_failure_alert_percent and
        # intel_retry_failure_hysteresis_minutes deleted (dead — never
        # threaded to IntelQueue). Strip stale client echoes.
        meeting_data.pop("intel_retry_failure_alert_percent", None)
        meeting_data.pop("intel_retry_failure_hysteresis_minutes", None)

        webhook_url = str(
            meeting_data.get(
                "intel_retry_failure_webhook_url",
                current.meeting.intel_retry_failure_webhook_url or "",
            )
            or ""
        ).strip()
        if webhook_url:
            parsed_webhook = urlparse(webhook_url)
            if (
                parsed_webhook.scheme not in {"http", "https"}
                or not parsed_webhook.netloc
            ):
                return {
                    "success": False,
                    "error": "intel_retry_failure_webhook_url must be a valid http(s) URL",
                }
        meeting_data["intel_retry_failure_webhook_url"] = webhook_url or None
        webhook_header_name = str(
            meeting_data.get(
                "intel_retry_failure_webhook_header_name",
                current.meeting.intel_retry_failure_webhook_header_name or "",
            )
            or ""
        ).strip()
        webhook_header_value = str(
            meeting_data.get(
                "intel_retry_failure_webhook_header_value",
                current.meeting.intel_retry_failure_webhook_header_value or "",
            )
            or ""
        ).strip()
        if bool(webhook_header_name) != bool(webhook_header_value):
            return {
                "success": False,
                "error": "intel_retry_failure_webhook_header_name and intel_retry_failure_webhook_header_value must both be set or both be empty",
            }
        if webhook_header_name and not _HTTP_HEADER_NAME_RE.match(webhook_header_name):
            return {
                "success": False,
                "error": "intel_retry_failure_webhook_header_name must contain only letters, digits, and hyphens",
            }
        meeting_data["intel_retry_failure_webhook_header_name"] = (
            webhook_header_name or None
        )
        meeting_data["intel_retry_failure_webhook_header_value"] = (
            webhook_header_value or None
        )

        # HS-61-01: the Send-to-Slack incoming-webhook URL. Empty = the
        # feature is off; anything else must pass THE shared rule (https
        # with a host; plain http for loopback only). The URL's host is
        # exactly what the Slack connector may POST to.
        slack_url = str(
            meeting_data.get(
                "slack_webhook_url", current.meeting.slack_webhook_url or ""
            )
            or ""
        ).strip()
        if slack_url:
            from holdspeak.slack_export import slack_webhook_host

            try:
                slack_webhook_host(slack_url)
            except ValueError as exc:
                return {"success": False, "error": f"slack_webhook_url: {exc}"}
        meeting_data["slack_webhook_url"] = slack_url

        # HSM-14: the iPad desk's Webhook connector URL. Same consent posture
        # as Slack — empty = the connector is off; anything else must pass THE
        # shared rule (https with a host; plain http for loopback only). The
        # URL's host is exactly what the Webhook connector may POST to, and the
        # URL is a credential: it stays on the host and never rides a payload.
        companion_webhook_url = str(
            meeting_data.get(
                "companion_webhook_url",
                current.meeting.companion_webhook_url or "",
            )
            or ""
        ).strip()
        if companion_webhook_url:
            from holdspeak.slack_export import slack_webhook_host

            try:
                slack_webhook_host(companion_webhook_url)
            except ValueError as exc:
                return {"success": False, "error": f"companion_webhook_url: {exc}"}
        meeting_data["companion_webhook_url"] = companion_webhook_url

        # HSM-14: the iPad desk's GitHub connector default repo (owner/name).
        # Auth is the host's already-authenticated local `gh` — no token is
        # stored or crosses the wire. Empty = the connector is off; otherwise
        # it must be a plain `owner/name` slug.
        companion_github_repo = str(
            meeting_data.get(
                "companion_github_repo",
                current.meeting.companion_github_repo or "",
            )
            or ""
        ).strip()
        if companion_github_repo and not _GITHUB_REPO_RE.match(companion_github_repo):
            return {
                "success": False,
                "error": "companion_github_repo must be of the form owner/name",
            }
        meeting_data["companion_github_repo"] = companion_github_repo

        similarity = float(
            meeting_data.get(
                "similarity_threshold", current.meeting.similarity_threshold
            )
        )
        if not (0.0 <= similarity <= 1.0):
            return {
                "success": False,
                "error": "similarity_threshold must be between 0.0 and 1.0",
            }
        meeting_data["similarity_threshold"] = similarity

        # HS-112-01: the assigned InferenceTarget (empty ⇒ hub default).
        # Stored as-is; a dangling id degrades honestly at resolution
        # time, so saving never blocks on it.
        meeting_data["intel_profile_id"] = (
            str(
                meeting_data.get(
                    "intel_profile_id", current.meeting.intel_profile_id or ""
                )
                or ""
            ).strip()
            or None
        )

        # WFS-CFG-004: validate the dictation slice (preserves
        # current values when payload omits them; merged already
        # carries `current.to_dict()["dictation"]` as the base).
        # Drops the read-only `_runtime_status` / `_placement` enrichment if
        # the client echoed it back (both are derived, never persisted).
        merged.pop("_runtime_status", None)
        merged.pop(PLACEMENT_KEY, None)
        merged.pop(CALENDAR_SUBSCRIPTION_KEY, None)
        dictation_data = merged.get("dictation", {}) or {}
        pipeline_data = dictation_data.get("pipeline", {}) or {}
        runtime_data = dictation_data.get("runtime", {}) or {}

        # HS-139-02: strip defaulted pipeline keys — pinned, not writable.
        for _dpk in ("enabled", "corrections_enabled", "journal_enabled", "journal_retention"):
            pipeline_data.pop(_dpk, None)
        raw_stages = pipeline_data.get("stages", current.dictation.pipeline.stages)
        if not isinstance(raw_stages, list) or not all(
            isinstance(stage, str) for stage in raw_stages
        ):
            return {
                "success": False,
                "error": "dictation.pipeline.stages must be a list of strings",
            }
        pipeline_data["stages"] = list(raw_stages)
        try:
            max_lat = int(
                pipeline_data.get(
                    "max_total_latency_ms",
                    current.dictation.pipeline.max_total_latency_ms,
                )
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "dictation.pipeline.max_total_latency_ms must be an integer",
            }
        if max_lat <= 0:
            return {
                "success": False,
                "error": "dictation.pipeline.max_total_latency_ms must be > 0",
            }
        pipeline_data["max_total_latency_ms"] = max_lat
        target_override = (
            str(
                pipeline_data.get(
                    "target_profile_override",
                    current.dictation.pipeline.target_profile_override,
                )
            )
            .strip()
            .lower()
            or "auto"
        )
        allowed_target_overrides = {
            "auto",
            "claude_code",
            "codex_cli",
            "terminal_shell",
            "browser",
            "editor",
            "chat",
        }
        if target_override not in allowed_target_overrides:
            return {
                "success": False,
                "error": (
                    "dictation.pipeline.target_profile_override must be one of: "
                    + ", ".join(sorted(allowed_target_overrides))
                ),
            }
        pipeline_data["target_profile_override"] = target_override

        # HS-40-01: the four Phase-39 depth knobs. They already flow
        # through via the merge + `DictationPipelineConfig(**pipeline_data)`
        # construction below (and `__post_init__` is the single source of
        # truth for the 1–5 / 0–1 bounds), but coerce the numeric/bool
        # types explicitly here so a non-numeric payload returns a clean
        # 4xx instead of a raw "'<=' not supported" TypeError. Defaults
        # come from `current` so an omitted knob is preserved, never reset.
        try:
            rewrite_passes = int(
                pipeline_data.get(
                    "rewrite_passes", current.dictation.pipeline.rewrite_passes
                )
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "dictation.pipeline.rewrite_passes must be an integer",
            }
        pipeline_data["rewrite_passes"] = rewrite_passes
        try:
            target_detect_below = float(
                pipeline_data.get(
                    "target_detect_llm_below",
                    current.dictation.pipeline.target_detect_llm_below,
                )
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "dictation.pipeline.target_detect_llm_below must be a number",
            }
        pipeline_data["target_detect_llm_below"] = target_detect_below
        # HS-139-02: corrections_enabled stripped above (pinned true).
        pipeline_data["target_detect_llm_enabled"] = bool(
            pipeline_data.get(
                "target_detect_llm_enabled",
                current.dictation.pipeline.target_detect_llm_enabled,
            )
        )

        backend = (
            str(runtime_data.get("backend", current.dictation.runtime.backend))
            .strip()
            .lower()
        )
        if backend not in {"auto", "mlx", "llama_cpp", "openai_compatible"}:
            return {
                "success": False,
                "error": f"Invalid dictation backend: {backend!r}",
            }
        runtime_data["backend"] = backend
        runtime_data["mlx_model"] = (
            str(
                runtime_data.get("mlx_model", current.dictation.runtime.mlx_model)
            ).strip()
            or current.dictation.runtime.mlx_model
        )
        runtime_data["llama_cpp_model_path"] = (
            str(
                runtime_data.get(
                    "llama_cpp_model_path",
                    current.dictation.runtime.llama_cpp_model_path,
                )
            ).strip()
            or current.dictation.runtime.llama_cpp_model_path
        )
        # HS-112-01: the assigned InferenceTarget (empty ⇒ hub default).
        # Stored as-is; a dangling id degrades honestly at resolution
        # time, so saving never blocks on it.
        runtime_data["profile_id"] = (
            str(
                runtime_data.get(
                    "profile_id", current.dictation.runtime.profile_id or ""
                )
                or ""
            ).strip()
            or None
        )
        try:
            timeout_seconds = float(
                runtime_data.get(
                    "openai_compatible_timeout_seconds",
                    current.dictation.runtime.openai_compatible_timeout_seconds,
                )
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "dictation.runtime.openai_compatible_timeout_seconds must be a number",
            }
        if timeout_seconds <= 0:
            return {
                "success": False,
                "error": "dictation.runtime.openai_compatible_timeout_seconds must be > 0",
            }
        runtime_data["openai_compatible_timeout_seconds"] = timeout_seconds
        runtime_data["warm_on_start"] = bool(
            runtime_data.get("warm_on_start", current.dictation.runtime.warm_on_start)
        )

        # HS-52-02: voice command macros. Validate the section so a malformed
        # macro returns a clean 4xx with a clear message, never a 500 and never a
        # silently-dropped command. `merged` already carries `current`'s macros as
        # the base, so omitting the section preserves it.
        macros_data = dictation_data.get("macros", {}) or {}
        macros_enabled = bool(
            macros_data.get("enabled", current.dictation.macros.enabled)
        )
        raw_macros = macros_data.get("items", [])
        if not isinstance(raw_macros, list):
            return {"success": False, "error": "dictation.macros.items must be a list"}
        try:
            macros_cfg = MacrosConfig(enabled=macros_enabled, items=raw_macros)
        except VoiceMacroError as exc:
            return {"success": False, "error": f"Invalid voice macro: {exc}"}

        try:
            dictation_cfg = DictationConfig(
                pipeline=DictationPipelineConfig(**pipeline_data),
                runtime=LLMRuntimeConfig(**runtime_data),
                macros=macros_cfg,
                spoken_symbols=dictation_data.get("spoken_symbols", []) or [],
                # HS-75-03: the preview-before-type knob rides the same
                # boundary (a plain bool; absent falls back to current).
                preview_before_type=bool(
                    dictation_data.get(
                        "preview_before_type",
                        current.dictation.preview_before_type,
                    )
                ),
            )
        except DictationConfigError as exc:
            return {"success": False, "error": str(exc)}
        except TypeError as exc:
            return {"success": False, "error": f"Invalid dictation field: {exc}"}

        # HS-112-01: the rails observer's pointer is settable from the
        # models module's RAILS row; same boundary discipline.
        rails_data = merged.get("rails_observer", {}) or {}
        rails_data["enabled"] = bool(
            rails_data.get("enabled", current.rails_observer.enabled)
        )
        rails_data["profile_id"] = (
            str(
                rails_data.get("profile_id", current.rails_observer.profile_id or "")
                or ""
            ).strip()
            or None
        )
        try:
            rails_data["poll_seconds"] = int(
                rails_data.get("poll_seconds", current.rails_observer.poll_seconds)
            )
            rails_data["tail"] = int(
                rails_data.get("tail", current.rails_observer.tail)
            )
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "rails_observer.poll_seconds and rails_observer.tail must be integers",
            }
        if rails_data["poll_seconds"] < 5 or rails_data["tail"] < 1:
            return {
                "success": False,
                "error": "rails_observer.poll_seconds must be >= 5 and rails_observer.tail >= 1",
            }

        thoughts_data = merged.get("thoughts", {}) or {}
        thoughts_data["inference_target_id"] = (
            str(
                thoughts_data.get(
                    "inference_target_id", current.thoughts.inference_target_id or ""
                )
                or ""
            ).strip()
            or None
        )

        calendar_data = merged.get("calendar", {}) or {}
        if not isinstance(calendar_data, dict):
            return {"success": False, "error": "calendar must be an object"}
        try:
            calendar_cfg = CalendarConfig(
                subscription=validate_calendar_subscription(
                    calendar_data.get("subscription", current.calendar.subscription)
                )
            )
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        updated = replace(
            current,
            hotkey=HotkeyConfig(**hotkey_data),
            model=ModelConfig(**model_data),
            ui=UIConfig(**ui_data),
            meeting=MeetingConfig(**meeting_data),
            dictation=dictation_cfg,
            device=DeviceConfig(**device_data),
            presence=PresenceConfig(**presence_data),
            wake_word=WakeWordConfig(**wake_data),
            rails_observer=RailsObserverConfig(**rails_data),
            thoughts=ThoughtsConfig(**thoughts_data),
            calendar=calendar_cfg,
        )
        updated.save()

        # Destination and policy configuration are part of authority. A
        # settings mutation conservatively invalidates reusable grants;
        # per-action approvals retain their own exact snapshots.
        authority_before = (
            current.meeting.slack_webhook_url,
            current.meeting.companion_webhook_url,
            current.meeting.companion_github_repo,
        )
        authority_after = (
            updated.meeting.slack_webhook_url,
            updated.meeting.companion_webhook_url,
            updated.meeting.companion_github_repo,
        )
        if authority_before != authority_after:
            self._db.actuators.revoke_active_grants(
                reason="destination_configuration_changed"
            )

        if self._on_settings_applied is not None:
            try:
                self._on_settings_applied(updated)
            except Exception as exc:
                # Existing behavior intentionally persists the accepted setting even
                # when live reconfiguration fails; the failure is logged and the
                # route still returns the accepted, redacted configuration.
                import logging

                logging.getLogger(__name__).error("on_settings_applied failed: %s", exc)

        return {"success": True, "settings": redacted_settings(updated)}
