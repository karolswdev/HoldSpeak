"""Canonical trust-destination registry and config-derived inventory."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

def _registry_path() -> Path:
    source = Path(__file__).resolve().parents[1] / "docs" / "trust-destinations.json"
    if source.exists():
        return source
    packaged = Path(__file__).resolve().parent / "data" / "trust-destinations.json"
    if packaged.exists():
        return packaged
    raise ValueError("trust destination registry is not available")


REGISTRY_PATH = _registry_path()
_REQUIRED = {"id", "name", "operation", "boundary", "data_class", "authority_basis", "background_ability", "revoke_action"}


@lru_cache(maxsize=1)
def destination_registry() -> tuple[dict[str, str], ...]:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1 or not isinstance(raw.get("destinations"), list):
        raise ValueError("unsupported trust destination registry")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in raw["destinations"]:
        if not isinstance(value, dict) or not _REQUIRED <= value.keys():
            raise ValueError("incomplete trust destination registry entry")
        row = {key: str(value[key]).strip() for key in _REQUIRED}
        if not all(row.values()) or row["id"] in seen:
            raise ValueError("blank or duplicate trust destination registry entry")
        seen.add(row["id"])
        rows.append(row)
    return tuple(rows)


def _configured(value: Any) -> bool:
    return bool(str(value or "").strip())


def destination_inventory(
    config: Any,
    *,
    database: Any = None,
    summary_route: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Join disclosure language to current state without exposing credentials."""
    if summary_route is None and database is not None:
        from .services.meeting_route_projection import summary_route_display

        try:
            summary_route = summary_route_display(database)
        except Exception:
            summary_route = None
    meeting = config.meeting
    runtime = config.dictation.runtime
    pipeline = config.dictation.pipeline
    backend = str(getattr(runtime, "backend", "local") or "local").strip().lower()
    from .intel.providers import effective_dictation_llm

    dictation_runtime = effective_dictation_llm(runtime)
    enabled = {
        "meeting_intel": False,
        "dictation_runtime": bool(
            pipeline.enabled and (dictation_runtime.profile_id or backend == "openai_compatible")
        ),
        # Slack credentials now live in channel destinations. The retained
        # Config field is intentionally ignored by trust inventory.
        "slack": False,
        "companion_webhook": _configured(meeting.companion_webhook_url),
        "github": _configured(meeting.companion_github_repo),
        "telegram": bool(
            getattr(config.cadence_telegram, "enabled", False)
            and _configured(getattr(config.cadence_telegram, "bot_token", ""))
        ),
        "failure_webhook": _configured(meeting.intel_retry_failure_webhook_url),
    }
    summary_ready = bool(summary_route and summary_route.get("status") == "ready")
    summary_legs = list(summary_route.get("legs") or ()) if summary_ready else []
    summary_hosts = [
        "This device"
        if str(leg.get("boundary") or "") == "local"
        else str(leg.get("host") or "").strip()
        for leg in summary_legs
        if str(leg.get("host") or "").strip()
    ]
    summary_boundaries = [
        str(leg.get("boundary") or "").strip()
        for leg in summary_legs
        if str(leg.get("boundary") or "").strip()
    ]
    names = {
        "meeting_intel": (
            " -> ".join(summary_hosts)
            if summary_ready and summary_hosts
            else "Summary route unavailable"
        ),
        "dictation_runtime": (
            dictation_runtime.profile_name or "Configured dictation runtime"
            if enabled["dictation_runtime"] else "This machine"
        ),
        "slack": "Slack channel destinations",
        "companion_webhook": (
            "Configured custom endpoint" if enabled["companion_webhook"] else "Not configured"
        ),
        "github": str(meeting.companion_github_repo or "Not configured"),
        "telegram": "Paired Telegram bot" if enabled["telegram"] else "Not configured",
        "failure_webhook": (
            "Configured alert endpoint" if enabled["failure_webhook"] else "Not configured"
        ),
    }
    receipts: dict[str, Any] = {}
    actuators = getattr(database, "actuators", None)
    if actuators is not None:
        from .kernel.journal import JournalStore

        journal = JournalStore(database._connection)
        for registry_id, target in {
            "slack": "slack", "companion_webhook": "webhook", "github": "github"
        }.items():
            receipts[registry_id] = (
                journal.last_receipt_for_ref(f"egress:{target}")
                or actuators.last_execution_receipt(target)
            )
    rows: list[dict[str, Any]] = []
    for row in destination_registry():
        registry_id = row["id"]
        value = {
            **row,
            "enabled": (
                summary_ready
                and any(str(leg.get("boundary") or "") != "local" for leg in summary_legs)
                if registry_id == "meeting_intel"
                else enabled[registry_id]
            ),
            "destination": names[registry_id],
            "last_receipt": receipts.get(registry_id),
        }
        if registry_id == "meeting_intel":
            value.update(
                name="Meeting summary",
                operation="Generate meeting summary",
                boundary=(" -> ".join(summary_boundaries) if summary_ready else "unavailable"),
                data_class="Meeting transcript",
                authority_basis="Assigned summary route",
                background_ability="Only runs for an explicit summary request",
                revoke_action="Change the summary assignment",
            )
        rows.append(value)
    rows.extend(_saved_send_destinations(database))
    return rows


def _short_target(target: Mapping[str, Any]) -> str:
    """A saved destination's target in plain words (a home folder reads as ~)."""
    for key in ("folder", "repo", "repository", "space", "project", "to", "address"):
        text = str(target.get(key) or "").strip()
        if not text:
            continue
        if key == "folder":
            home = str(Path.home())
            for prefix in (home, str(Path(home).resolve())):
                if text == prefix or text.startswith(prefix + "/"):
                    return "~" + text[len(prefix):]
        return text
    return "Saved destination"


def _shown(target: Any) -> dict[str, Any]:
    """The target as the face reads it (the built-in folder resolved now)."""
    if not isinstance(target, dict):
        return {}
    from .services.channel_contract import shown_target

    return shown_target(target)


def _saved_send_destinations(database: Any) -> list[dict[str, Any]]:
    """The owner's saved Send destinations (Settings, Connections).

    Inventory 2026-10-03 (UX-CANON A.10): Trust said "Enabled destinations
    None" with a saved destination. Each active saved destination is a row.
    ``enabled`` keeps its one meaning (data can leave this device): a folder
    on this device is ``saved`` and not ``enabled``.
    """
    channels = getattr(database, "channel_destinations", None)
    if channels is None:
        return []
    try:
        saved = channels.list()
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for row in saved:
        channel = str(row.get("channel") or "")
        try:
            target = json.loads(row.get("target_json") or "{}")
        except (TypeError, ValueError):
            target = {}
        # The built-in HoldSpeak folder: iCloud Drive's sync is read now.
        synced = bool(row.get("synced")) or bool(_shown(target).get("cloud"))
        local = channel == "file" and not synced
        rows.append({
            "id": f"channel:{row['id']}",
            "name": str(row.get("name") or "Saved destination"),
            "operation": "Send a document",
            "boundary": "This device" if local else "Outside this device",
            "data_class": "The document you send",
            "authority_basis": "You press Send",
            "background_ability": "No. Each send needs your press",
            "revoke_action": "Park the destination in Settings, Connections",
            "enabled": not local,
            "saved": True,
            "destination": _short_target(_shown(target)),
            "last_receipt": None,
        })
    return rows


__all__ = ["REGISTRY_PATH", "destination_inventory", "destination_registry"]
