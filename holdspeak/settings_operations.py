"""The Settings window's verbs on the one declared contract (credentials 2026-11-11; the rest 2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``CredentialService`` verb once: its call, its HTTP method and path. The
routes are produced by ``web/routes/system/settings_secrets.py`` through
``OperationRegistry.invoke``.

A credential is a security surface: every row is owner-only and the owner's
own press (``authority="config"``). No row has an MCP tool, so no agent and
no thread reaches a key. The answer is the redacted state of every secret
(``present``, ``destination``), never key material.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

_PRINCIPAL = "derived by the transport (HTTP auth middleware); owner only"
_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
    "NotFound: unknown secret setting",
    "ValidationError: the value is refused (empty, not a URL, not rotatable)",
)
_RESULT = "success and secrets: the redacted state of every secret (present, destination); never key material"
# Declared, not enforced: an enforced admission runs the kernel path, whose
# receipt records the arguments, and the arguments of a replace hold the key.
_ADMISSION = Admission("admitted", "Config: the owner's press writes one credential in the settings file.", enforced=False)


def _replace(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    # The value travels once, as ``value``; the metadata copy never holds it (the
    # observer withholds ``value``, Codex on #2127 finding 3).
    body = {key: value for key, value in args.items() if key not in ("secret_id", "value")}
    return {"success": True, "secrets": service.replace(principal, args.get("secret_id"), args.get("value"), body)}


def _rotate(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"success": True, "secrets": service.rotate(principal, args.get("secret_id"))}


def _delete(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"success": True, "secrets": service.delete(principal, args.get("secret_id"))}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Any, description: str) -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write", result=_RESULT, refusals=_REFUSALS,
        completion="synchronous; GET /api/settings reads the redacted state back",
        exposure=(f"http:{http[0]} {http[1]}",), service="credential_service", method=method,
        owner_only=True, owner_press=True, admission=_ADMISSION,
        call=call, http=http, handler=handler, authority="config",
    )


_S = "/api/settings/secrets/{secret_id}"
CREDENTIAL_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("settings.secret.replace", "replace", ("PUT", _S), "api_replace_secret", _replace,
        "Replace one credential in the settings file (a token, a key, a webhook)."),
    _op("settings.secret.rotate", "rotate", ("POST", _S + "/rotate"), "api_rotate_secret", _rotate,
        "Rotate one rotatable credential (the web token, the device key, the Telegram pairing code)."),
    _op("settings.secret.delete", "delete", ("DELETE", _S), "api_delete_secret", _delete,
        "Remove one credential from the settings file."),
)


# ── the rest of Settings (2026-11-09): one row per route ─────────────────
# ``web/routes/system/settings.py``, ``authority.py`` and ``briefing.py``
# produce these routes, ``mcp/families/declared.py`` the tools. The settings
# file, the heartbeat and Reach have tools (the hand-written settings and
# heartbeat MCP families are parked); the posture (authority) and Telegram's
# pairing and token are owner only, HTTP only: no agent changes how HoldSpeak
# is allowed to act or where it reaches him.

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (HTTP auth middleware; MCP auth resolver); owner only"
_ANY_OBJECT: dict[str, Any] = {"type": "object", "additionalProperties": True}


def _row(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Any, description: str, *,
         result: str, write: bool = False, owner_only: bool = False, owner_press: bool = False, tool: Any = None,
         web_call: Any = None, authority: str = "work", status: int = 200, held: tuple[str, ...] = (),
         blocking_io: bool = False, refusals: tuple[str, ...] = (), completion: str = "synchronous") -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"},
        principal=_OWNER if owner_only else _ANY, effect="write" if write else "read", result=result,
        refusals=_CONTRACT_REFUSALS + (("owner_required",) if owner_only else ()) + refusals, completion=completion,
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool is not None else ()), service=service,
        method=method, owner_only=owner_only, owner_press=owner_press, blocking_io=blocking_io, held=held,
        call=call, web_call=web_call, http=http, http_status=status, handler=handler, tool_schema=tool,
        authority=authority, thread=("effect_proposal" if write else "evidence_read") if tool is not None else None,
    )


def _settings_read(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.plugins.dictation.runtime_counters import get_counters, get_session_status

    payload = service.get_settings(principal)
    # Runtime fields are read-only enrichment of the HTTP answer, never persisted state.
    payload["_runtime_status"] = {"counters": get_counters(), "session": get_session_status()}
    return payload


def _calendar_sources_snapshot() -> dict[str, str]:
    """{source id: url} of the calendar sources on disk right now."""
    try:
        from holdspeak.config import Config

        return {source.id: str(source.url or "") for source in Config.load().calendar.sources}
    except Exception:
        return {}


def remove_generated_ics_for_removed_sources(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """HS-175 counsel C4 (the Remove half): a calendar source removed by a settings
    write whose URL is an ICS the Snapshot verb generated takes its file with it.
    Only files inside the snapshot directory are deleted. Returns the paths deleted."""
    from holdspeak.services.calendar_snapshot_service import delete_generated_ics

    return [url for source_id, url in before.items() if source_id not in after and delete_generated_ics(url)]


def _settings_write(service: Any, principal: Any, patch: Any) -> Any:
    if not isinstance(patch, dict):
        from holdspeak.services.errors import ValidationError

        raise ValidationError("patch must be an object")
    touches_sources = isinstance(patch.get("calendar"), dict) and "sources" in patch["calendar"]
    before = _calendar_sources_snapshot() if touches_sources else {}
    result = service.update_settings(principal, patch)
    if touches_sources and isinstance(result, dict) and result.get("success", True):
        try:
            remove_generated_ics_for_removed_sources(before, _calendar_sources_snapshot())
        except Exception as exc:  # the write stands; the file cleanup is logged
            from holdspeak.logging_config import get_logger

            get_logger("settings_operations").warning("snapshot ICS cleanup after settings write failed: %s", exc)
    return result


class _LiveHeartbeat:
    """The bound target: a HeartbeatService over the process database, with the
    watch evaluator and the follow-through sender, built at each call (as the
    hand-written route and MCP family built theirs)."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.db import get_database, get_observer
        from holdspeak.delivery.follow_through import default_follow_through
        from holdspeak.runtime.composition import db_or, observer_or
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.services.watch_service import WatchService

        db, observer = db_or(get_database), observer_or(get_observer)
        service = HeartbeatService(db, observer=observer, watch_service=WatchService(db, observer=observer),
                                   follow_through=default_follow_through(db))
        return getattr(service, name)


class _LiveReach:
    """The bound target: the process's one ReachService, read at each call."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.services.reach_service import default_reach_service

        return getattr(default_reach_service(), name)


class _LiveTelegram:
    """The bound target: the process's one Telegram reach, read at each call."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.services.telegram_reach import default_telegram_reach

        return getattr(default_telegram_reach(), name)


LIVE_HEARTBEAT_SERVICE = _LiveHeartbeat()
LIVE_REACH_SERVICE = _LiveReach()
LIVE_TELEGRAM_SERVICE = _LiveTelegram()

_HEARTBEAT_PATCH = {
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean", "description": "Run the heartbeat sweep."},
        "interval_minutes": {"type": "integer", "minimum": 1, "description": "Minutes between sweeps."},
        "quiet_hours": {"type": "object", "description": "Quiet hours window: {start, end} in local hours."},
        "notify": {"type": "string", "enum": ["off", "edge", "every_sweep"], "description": "Notification mode."},
        "muted_projects": {"type": "array", "items": {"type": "string"},
                           "description": "Project IDs to exclude from notification aggregates."},
        "report_merged_prs": {"type": "boolean", "description": "Read each Room repository's merged PRs on every "
                                                                 "sweep, so the weekly update reports every merge."},
    },
    "additionalProperties": False,
}
_NO_ARGS: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}
_R = "/api/reach"

SETTINGS_ROUTE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _row("settings.get", "settings_service", "get_settings", ("GET", "/api/settings"), "api_get_settings",
         lambda s, p, a: s.get_settings(p),
         "Read the current HoldSpeak settings. Secrets are redacted; _revision enables optimistic concurrency.",
         web_call=_settings_read, result="the settings tree with _revision (the HTTP answer adds _runtime_status)",
         tool=_NO_ARGS),
    _row("settings.update", "settings_service", "update_settings", ("PUT", "/api/settings"), "api_update_settings",
         lambda s, p, a: _settings_write(s, p, a.get("patch")),
         "Update HoldSpeak settings with a partial patch. EGRESS: an HTTPS calendar.sources is a list of "
         "{id, label, url, enabled} ICS sources, each fetched by the hub without credentials or headers; "
         "intel_provider and intel_profile_id are retired routing controls; _placement inference assignments and "
         "secrets cannot be written through this tool. Echo _revision from settings.get for optimistic concurrency; "
         "omit it for last-writer-wins. Settings are persisted immediately; the hub applies them at once, and a "
         "process off the hub sends no live-reload signal. Owner only: the settings are his, and no agent "
         "writes a credential (Codex on #2127).",
         write=True, owner_only=True, authority="config",
         result="{success, settings, _revision}", refusals=("ValidationError", "ConflictError: a stale _revision",
                                                            "credential_in_settings_patch"),
         completion="synchronous; settings.get reads the new values",
         tool={"type": "object", "properties": {"patch": {"type": "object", "description":
               "Partial settings object. Only supplied keys are changed."}}, "required": ["patch"],
               "additionalProperties": False}),
    _row("settings.hub", "settings_hub_service", "hub", ("GET", "/api/settings/hub"), "api_settings_hub",
         lambda s, p, a: s.hub(p),
         "Read the Settings hub row facts: each section's state (engines, connections, voice, meetings, rhythm).",
         result="{models, connections, voice, meetings, answers, rhythm, sounds, agents, system, posture, writtenAt}",
         blocking_io=True, tool=_NO_ARGS),
    _row("heartbeat.status", "heartbeat_service", "get_settings", ("GET", "/api/settings/heartbeat"),
         "api_heartbeat_get", lambda s, p, a: {**s.get_settings(), "held": s.in_quiet_hours()},
         "Read the heartbeat sweep settings, and whether quiet hours hold it now.",
         web_call=lambda s, p, a: s.get_settings(), result="{enabled, interval_minutes, quiet_hours, notify, "
         "muted_projects, report_merged_prs} (the tool adds held)", tool=_NO_ARGS),
    _row("heartbeat.set", "heartbeat_service", "update_settings", ("PUT", "/api/settings/heartbeat"),
         "api_heartbeat_put", lambda s, p, a: s.update_settings(dict(a)),
         "Change the heartbeat sweep settings: interval, quiet hours, notifications, muted projects.",
         write=True, authority="config", result="the new heartbeat settings", refusals=("ValidationError",),
         tool=_HEARTBEAT_PATCH),
    _row("heartbeat.run_now", "heartbeat_service", "run_sweep", ("POST", "/api/settings/heartbeat/run-now"),
         "api_heartbeat_run_now", lambda s, p, a: s.run_sweep(p, owner_hand=True),
         "Run one heartbeat sweep now: every due watch, even inside quiet hours.",
         write=True, blocking_io=True, result="the sweep receipt", tool=_NO_ARGS),
    # MCP only: the face has no test-notification press.
    OperationDescriptor(
        name="heartbeat.notify_test", version=1,
        description="Fire one test desktop notification (owner-only). Returns {fired: boolean}.",
        args_schema={"type": "object"}, principal=_OWNER, effect="write", result="{fired, reason?}",
        refusals=_CONTRACT_REFUSALS + ("owner_required",), completion="synchronous",
        exposure=("mcp:heartbeat.notify_test",), service="heartbeat_service", method="notify_test",
        owner_only=True, call=lambda s, p, a: s.notify_test(), tool_schema=_NO_ARGS, thread="effect_proposal",
    ),
    _row("authority.policy", "authority_service", "get_policy", ("GET", "/api/authority/policy"),
         "api_authority_policy", lambda s, p, a: s.get_policy(p),
         "Read the control mode (Secure, Normal, YOLO) and the authority policy it applies.", owner_only=True,
         result="{version, control_mode, control_mode_label, precedence, hard_invariants, supported_families}"),
    _row("authority.control_mode.set", "authority_service", "set_control_mode", ("PUT", "/api/authority/control-mode"),
         "api_set_control_mode", lambda s, p, a: s.set_control_mode(p, str(a.get("control_mode") or "")),
         "Set the control mode: Secure, Normal or YOLO. A change revokes every active scoped grant.",
         write=True, owner_only=True, owner_press=True, authority="authority",
         result="{control_mode, previous_control_mode, revoked_grants, revoked_coder_grants}",
         refusals=("ValidationError: Control mode must be Secure, Normal, or YOLO.",)),
    _row("reach.status", "reach_service", "status", ("GET", _R), "api_reach", lambda s, p, a: s.status(p),
         "Read how HoldSpeak reaches the owner: the channels, the ladder, quiet hours, the digest, Later and the "
         "open pages. Never a token.", owner_only=True, result="{channels, ladder, quiet, digest, later_means, "
         "packages}", refusals=("owner_only",), tool=_NO_ARGS),
    _row("reach.save", "reach_service", "save_settings", ("PUT", _R), "api_reach_put",
         lambda s, p, a: (s.save_settings(p, dict(a.get("patch") or {})), s.status(p))[1],
         "Change how HoldSpeak reaches the owner: Telegram's rung, what Later means, the digest time, the phone app.",
         web_call=lambda s, p, a: (s.save_settings(p, dict(a)), s.status(p))[1], write=True, owner_only=True,
         authority="config", result="the reach status after the change", refusals=("owner_only", "reach_invalid"),
         tool={"type": "object", "properties": {"patch": {"type": "object", "description":
               "{telegram?, later_means?, digest?, phone_app?}"}}, "required": ["patch"],
               "additionalProperties": False}),
    _row("reach.later", "reach_service", "later", ("POST", _R + "/later"), "api_reach_later",
         lambda s, p, a: s.later(p, a.get("ref"), a.get("later"), via="desk"),
         "Hold one held item for later (words like 'tomorrow 9'); it comes back then. Decides nothing.",
         write=True, owner_only=True, authority="config", result="{until, words, parked}", refusals=("owner_only",),
         tool={"type": "object", "properties": {"ref": {"type": "string", "description": "The held item's ref."},
               "later": {"type": "string", "description": "When: words like 'tomorrow 9'."}},
               "required": ["ref"], "additionalProperties": False}),
    _row("reach.digest.send", "reach_service", "send_digest_now", ("POST", _R + "/digest"), "api_reach_digest",
         lambda s, p, a: s.send_digest_now(p),
         "Send the digest to the owner's Telegram chat now.", write=True, owner_only=True, owner_press=True,
         blocking_io=True, authority="egress", result="{sent, lines}", refusals=("owner_only", "telegram_unpaired"),
         tool=_NO_ARGS),
    _row("reach.telegram.pair", "telegram_service", "start_pairing", ("POST", _R + "/telegram/pair"),
         "api_reach_telegram_pair", lambda s, p, a: s.start_pairing(p),
         "Start pairing the owner's Telegram chat: a one-time code he sends to the bot.", write=True,
         owner_only=True, owner_press=True, authority="config", status=201, blocking_io=True,
         result="{code, words, expires_at}", refusals=("owner_only", "telegram_no_token", "telegram_paired")),
    _row("reach.telegram.unpair", "telegram_service", "unpair", ("DELETE", _R + "/telegram/pair"),
         "api_reach_telegram_unpair", lambda s, p, a: s.unpair(p),
         "Unpair the owner's Telegram chat.", write=True, owner_only=True, owner_press=True, authority="config",
         result="{paired: false}", refusals=("owner_only",)),
    _row("reach.telegram.token", "telegram_service", "save_token", ("PUT", _R + "/telegram/token"),
         "api_reach_telegram_token", lambda s, p, a: s.save_token(p, a.get("token")),
         "Save the Telegram bot token in the keychain. The token is held by the transport, never an argument.",
         write=True, owner_only=True, owner_press=True, authority="config", held=("token",),
         result="{token: keystore | missing}", refusals=("owner_only", "telegram_token_invalid")),
)

SETTINGS_OPERATIONS: tuple[OperationDescriptor, ...] = CREDENTIAL_OPERATIONS + SETTINGS_ROUTE_OPERATIONS


def bare_builders(db: Any, observer: Any) -> dict[str, Any]:
    """The Settings family's services in a bare (non-hub) composition: the MCP
    dispatch off the hub (``mcp.tools.runtime_registry``) binds its tools over these."""

    def setup() -> Any:
        from holdspeak.services.setup_service import SetupService

        return SetupService(db, observer=observer)

    def settings() -> Any:
        from holdspeak.services.settings_service import SettingsService

        return SettingsService(db=db, on_settings_applied=None, observer=observer)

    def onboarding() -> Any:
        from holdspeak.services.onboarding_service import OnboardingService

        return OnboardingService()

    def settings_hub() -> Any:
        from holdspeak.services.settings_hub_service import bare_settings_hub

        return bare_settings_hub(db, observer)

    return {"setup_service": setup, "settings_service": settings, "settings_hub_service": settings_hub,
            "onboarding_service": onboarding,
            "heartbeat_service": lambda: LIVE_HEARTBEAT_SERVICE, "reach_service": lambda: LIVE_REACH_SERVICE}


__all__ = ["CREDENTIAL_OPERATIONS", "LIVE_HEARTBEAT_SERVICE", "LIVE_REACH_SERVICE", "LIVE_TELEGRAM_SERVICE", "SETTINGS_OPERATIONS",
           "SETTINGS_ROUTE_OPERATIONS", "bare_builders",
           "remove_generated_ics_for_removed_sources"]
