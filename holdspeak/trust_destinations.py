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
        "slack": _configured(meeting.slack_webhook_url),
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
        "slack": "Configured Slack workspace" if enabled["slack"] else "Not configured",
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
    return rows


__all__ = ["REGISTRY_PATH", "destination_inventory", "destination_registry"]
