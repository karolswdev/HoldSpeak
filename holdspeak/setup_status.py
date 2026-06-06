"""First-run setup-state contract (HS-42-01).

One UI-friendly snapshot of "is this product ready, and if not, what's the single
next thing to do?" — composed as an **adapter** over the existing structured
sources, never a second doctor:

- `collect_doctor_checks(skip_network=True)` → the setup `sections` (1:1, so every
  doctor check — and crucially every `FAIL` — surfaces; the drift test locks this).
- `intel_egress_posture()` + config → the `trust` block (what can leave the machine).
- `detect_presence_platform()` + `desktop_presence_enabled()` → the `presence` block.
- the durable first-success milestone → `first_run`.

It is cheap by construction: `skip_network=True` makes the cloud preflight a neutral
"not run" check, so a page load never blocks on an HTTP timeout, and no check loads a
large model (the runtime checks inspect paths/imports only).
"""
from __future__ import annotations

import re
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("setup_status")

# Severity ordering for picking the single primary action + the overall verdict.
_SEVERITY = {"fail": 3, "warn": 2, "unknown": 1, "pass": 0}


def _slug(name: str) -> str:
    """Stable section id from a doctor check name ("Cloud intel preflight" → ...)."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower())
    return s.strip("-") or "check"


def _section_from_check(check: Any) -> dict[str, Any]:
    status = str(getattr(check, "status", "") or "").strip().lower()
    if status not in ("pass", "warn", "fail"):
        status = "unknown"
    return {
        "id": _slug(getattr(check, "name", "")),
        "label": str(getattr(check, "name", "")),
        "status": status,
        "detail": str(getattr(check, "detail", "") or ""),
        "fix": getattr(check, "fix", None),
    }


def _overall(sections: list[dict[str, Any]]) -> str:
    statuses = {s["status"] for s in sections}
    if "fail" in statuses:
        return "blocked"
    if "warn" in statuses:
        return "needs_attention"
    return "ready"


def _primary_action(
    sections: list[dict[str, Any]], *, first_run: bool, ready: bool
) -> Optional[dict[str, Any]]:
    """The single highest-severity next step (first FAIL, else first WARN).

    When everything passes and the user hasn't dictated yet, the next step is the
    first-dictation test itself — that's the point of the whole surface.
    """
    unmet = [s for s in sections if s["status"] in ("fail", "warn")]
    if unmet:
        unmet.sort(key=lambda s: _SEVERITY[s["status"]], reverse=True)
        top = unmet[0]
        return {
            "id": top["id"],
            "label": top["fix"] or f"Resolve: {top['label']}",
            "route": f"/setup#{top['id']}",
        }
    if ready and first_run:
        return {
            "id": "first_dictation",
            "label": "Try your first dictation",
            "route": "/setup#first-dictation",
        }
    return None


def _trust_block(config: Any, *, web_bind: str = "127.0.0.1") -> dict[str, Any]:
    """What can leave the machine right now, from config (display only)."""
    from .intel import intel_egress_posture

    meeting = config.meeting
    dictation_runtime = config.dictation.runtime

    if not meeting.intel_enabled:
        transcript_egress = "none"
    else:
        provider = str(meeting.intel_provider or "local").strip().lower()
        # local → none; cloud → configured (always off-machine); auto → possible.
        transcript_egress = {
            "local": "none",
            "cloud": "configured",
            "auto": "possible",
        }.get(provider, "possible")

    endpoints: list[str] = []
    if meeting.intel_enabled and str(meeting.intel_provider).lower() != "local":
        base = (meeting.intel_cloud_base_url or "").strip()
        if base:
            endpoints.append(base)
    if str(getattr(dictation_runtime, "backend", "")).lower() == "openai_compatible":
        base = (getattr(dictation_runtime, "openai_compatible_base_url", "") or "").strip()
        if base:
            endpoints.append(base)

    # Static intent description reused from the doctor/web egress source of truth.
    _, egress_description = intel_egress_posture(meeting.intel_provider)

    return {
        "web_bind": web_bind,
        "auth_token_set": bool((getattr(config, "web_auth_token", "") or "").strip()),
        "transcript_egress": transcript_egress,
        "egress_detail": egress_description if meeting.intel_enabled else
        "Disabled — no transcript leaves this machine.",
        "configured_endpoints": endpoints,
        "actuators_enabled": bool(getattr(meeting, "allow_actuators", False)),
        "webhook_allowed_hosts": list(getattr(meeting, "webhook_allowed_hosts", []) or []),
    }


def _presence_block(env: Optional[dict[str, str]] = None) -> dict[str, Any]:
    """Presence availability + the platform tier (no native imports)."""
    from .desktop_presence import desktop_presence_enabled, detect_presence_platform

    platform = detect_presence_platform(env)
    os_name = platform.get("os")
    overlay = bool(platform.get("overlay_capable"))
    if os_name == "macos":
        tier = "hud"
    elif os_name == "linux":
        tier = "hud" if overlay else "notification"
    else:
        tier = "none"
    return {
        "enabled": desktop_presence_enabled(env),
        "available": os_name in ("macos", "linux"),
        "tier": tier,
        "os": os_name,
        "wayland": bool(platform.get("wayland")),
    }


def build_setup_status(
    *,
    database: Any = None,
    config: Any = None,
    env: Optional[dict[str, str]] = None,
    skip_network: bool = True,
) -> dict[str, Any]:
    """Compose the first-run setup-state snapshot.

    `database` supplies the milestone repo (`db.milestones`); when None the
    milestone is treated as unset (so `first_run` is True). `config` defaults to
    `Config.load()`. `skip_network=True` keeps the read cheap (no cloud preflight
    HTTP).
    """
    from .commands.doctor import collect_doctor_checks
    from .config import Config

    if config is None:
        config = Config.load()

    checks = collect_doctor_checks(skip_network=skip_network)
    sections = [_section_from_check(c) for c in checks]

    first_run = True
    if database is not None and getattr(database, "milestones", None) is not None:
        from .db import FIRST_DICTATION_SUCCESS

        try:
            first_run = not database.milestones.is_set(FIRST_DICTATION_SUCCESS)
        except Exception as exc:  # pragma: no cover - never block a page load on the DB
            log.warning(f"setup_status: milestone read failed ({exc}); treating as first run")
            first_run = True

    overall = _overall(sections)
    ready = overall == "ready"
    return {
        "overall": overall,
        "first_run": first_run,
        "primary_action": _primary_action(sections, first_run=first_run, ready=ready),
        "sections": sections,
        "trust": _trust_block(config),
        "presence": _presence_block(env),
    }
