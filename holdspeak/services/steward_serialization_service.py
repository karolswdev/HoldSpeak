"""Steward wire serializers shared by HTTP, MCP, and project services."""
from __future__ import annotations

import json
from typing import Any


def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
    """Serialize a steward run row for the public wire shape."""
    summary = {}
    if run.get("summary_json"):
        try:
            summary = json.loads(run["summary_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": run["id"],
        "project_id": run["project_id"],
        "policy_id": run.get("policy_id"),
        "state": run["state"],
        "phase": run["phase"],
        "requested_by": run.get("requested_by", ""),
        "watermark": run.get("watermark", ""),
        "summary": summary,
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "started_at": run.get("started_at"),
        "completed_at": run.get("completed_at"),
        "stop_requested_at": run.get("stop_requested_at"),
    }


def _serialize_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_serialize_run(run) for run in runs]


def _serialize_step(step: dict[str, Any]) -> dict[str, Any]:
    """Serialize a steward step row for the public wire shape."""
    expected = {}
    if step.get("expected_state_json"):
        try:
            expected = json.loads(step["expected_state_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    observed = {}
    if step.get("observed_state_json"):
        try:
            observed = json.loads(step["observed_state_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    receipt = {}
    if step.get("receipt_json"):
        try:
            receipt = json.loads(step["receipt_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    error = None
    if step.get("error_json"):
        try:
            error = json.loads(step["error_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": step["id"],
        "phase": step["phase"],
        "seq": step["seq"],
        "state": step["state"],
        "effect_kind": step["effect_kind"],
        "idempotency_key": step["idempotency_key"],
        "expected": expected,
        "observed": observed,
        "receipt": receipt,
        "error": error,
    }


def _serialize_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_serialize_step(step) for step in steps]


def _serialize_policy(policy: dict[str, Any] | None) -> dict[str, Any] | None:
    if policy is None:
        return None
    eligible = []
    if policy.get("eligible_effect_kinds_json"):
        try:
            eligible = json.loads(policy["eligible_effect_kinds_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    bounds = {}
    if policy.get("bounds_json"):
        try:
            bounds = json.loads(policy["bounds_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    yolo = {}
    if policy.get("yolo_flags_json"):
        try:
            yolo = json.loads(policy["yolo_flags_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": policy["id"],
        "project_id": policy["project_id"],
        "eligible_effect_kinds": eligible,
        "yolo_flags": yolo,
        "max_retries": policy["max_retries"],
        "max_actions_per_run": policy["max_actions_per_run"],
        "cooldown_seconds": policy["cooldown_seconds"],
        "bounds": bounds,
        "enabled": bool(policy["enabled"]),
        "unattended_enabled": bool(policy.get("unattended_enabled", 0)),
        "created_at": policy.get("created_at"),
        "updated_at": policy.get("updated_at"),
    }
