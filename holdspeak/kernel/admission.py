"""Generic request parsing; typed payload validation remains in each codec."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ..operation_policy import POLICY_VERSION
from .model import KernelRefused, OperationRequest

_REQUEST_FIELDS = frozenset(
    {
        "request_schema", "request_id", "idempotency_key", "operation",
        "subject_refs", "target", "arguments", "placement", "parent_operation_id",
    }
)
_AUTHORITY_FIELDS = frozenset(
    {"actor", "principal", "authority", "authority_basis", "control_mode", "effect_class", "data_classes", "policy_version"}
)


def parse_request(raw: Any) -> OperationRequest:
    if not isinstance(raw, Mapping):
        raise KernelRefused("request_malformed")
    if set(raw) & _AUTHORITY_FIELDS:
        raise KernelRefused("authority_not_client_settable")
    unknown = set(raw) - _REQUEST_FIELDS
    if unknown:
        raise KernelRefused("request_field_not_allowed", sorted(unknown)[0])
    operation = raw.get("operation")
    target = raw.get("target") or {}
    if raw.get("request_schema") != 1 or not isinstance(operation, Mapping) or not isinstance(target, Mapping):
        raise KernelRefused("request_schema_invalid")
    request_id = str(raw.get("request_id") or "").strip()
    idempotency_key = str(raw.get("idempotency_key") or "").strip()
    name = str(operation.get("name") or "").strip()
    version = operation.get("version")
    arguments = raw.get("arguments")
    if not request_id or not idempotency_key or not name or not isinstance(version, int) or not isinstance(arguments, Mapping):
        raise KernelRefused("request_incomplete")
    refs = raw.get("subject_refs") or []
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        raise KernelRefused("subject_refs_invalid")
    return OperationRequest(
        1, request_id, idempotency_key, name, version,
        str(target.get("ref") or ""), str(raw.get("placement") or ""),
        arguments, tuple(refs), str(raw.get("parent_operation_id") or "").strip(),
    )


def refusal_values(raw: Any, principal: Any, operation_id: str, reason: str) -> dict[str, Any]:
    safe = raw if isinstance(raw, Mapping) else {}
    request_id = str(safe.get("request_id") or operation_id)
    idempotency = str(safe.get("idempotency_key") or operation_id)
    operation = safe.get("operation") if isinstance(safe.get("operation"), Mapping) else {}
    raw_version = operation.get("version")
    version = raw_version if isinstance(raw_version, int) and not isinstance(raw_version, bool) else 0
    digest = json.dumps({"request_id": request_id, "reason": reason}, separators=(",", ":"), sort_keys=True)
    return {
        "operation_id": operation_id, "request_id": request_id, "idempotency_key": idempotency,
        "name": str(operation.get("name") or "unknown"), "version": version,
        "principal_kind": principal.name, "principal_identity": principal.identity,
        "target_ref": "", "placement": "",
        "envelope_sha256": "sha256:" + hashlib.sha256(digest.encode()).hexdigest(),
        "policy_version": POLICY_VERSION, "authority_basis": "refused_at_admission",
        "state": "refused", "native_id": "", "parent_operation_id": "",
        "correlation_id": operation_id,
    }
