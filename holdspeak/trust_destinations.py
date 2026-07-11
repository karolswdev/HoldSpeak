"""Canonical trust-destination registry and config-derived inventory."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

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


def destination_inventory(config: Any, *, database: Any = None) -> list[dict[str, Any]]:
    """Join disclosure language to current state without exposing credentials."""
    meeting = config.meeting
    runtime = config.dictation.runtime
    pipeline = config.dictation.pipeline
    provider = str(meeting.intel_provider or "local").strip().lower()
    backend = str(getattr(runtime, "backend", "local") or "local").strip().lower()
    from .intel.providers import effective_dictation_llm, effective_intel_cloud

    meeting_runtime = effective_intel_cloud(meeting)
    dictation_runtime = effective_dictation_llm(runtime)
    enabled = {
        "meeting_intel": bool(meeting.intel_enabled and provider != "local"),
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
    names = {
        "meeting_intel": (
            meeting_runtime.profile_name or "Configured meeting runtime"
            if enabled["meeting_intel"] else "This machine"
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
        for registry_id, target in {
            "slack": "slack", "companion_webhook": "webhook", "github": "github"
        }.items():
            receipts[registry_id] = actuators.last_execution_receipt(target)
    return [
        {
            **row, "enabled": enabled[row["id"]], "destination": names[row["id"]],
            "last_receipt": receipts.get(row["id"]),
        }
        for row in destination_registry()
    ]


__all__ = ["REGISTRY_PATH", "destination_inventory", "destination_registry"]
