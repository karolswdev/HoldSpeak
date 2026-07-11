"""Material authority bound to one actuator approval.

Approval is a capability for one exact effect, not merely permission for a
proposal id.  This dependency-light module is shared by persistence (where the
binding is captured) and the executor (where it is verified before egress).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional


PREVIEW_RENDERER_VERSION = "actuator-preview/v1"
POLICY_VERSION = "actuator-policy/v1"

_DESTINATION_KEYS = (
    "destination",
    "url",
    "webhook_url",
    "repo",
    "repository",
    "channel",
    "project",
    "room",
    "recipient",
)


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def payload_hash(payload: Optional[Mapping[str, Any]]) -> str:
    """Return the stable identity of the exact machine payload."""
    return _canonical_hash(dict(payload or {}))


def normalize_destination(target: str, payload: Optional[Mapping[str, Any]]) -> str:
    """Return a secret-safe identity for the effect's material destination.

    Destination-shaped payload fields are normalized for whitespace/case and
    hashed so webhook paths, recipients, and similar credentials never become
    new plaintext persistence. The target remains readable for audit routing.
    """
    clean_target = str(target or "").strip().lower()
    material = {
        key: str((payload or {}).get(key) or "").strip().lower()
        for key in _DESTINATION_KEYS
        if str((payload or {}).get(key) or "").strip()
    }
    if not material:
        return f"{clean_target}:default"
    return f"{clean_target}:sha256:{_canonical_hash(material)}"


def effect_class(target: str, action: str) -> str:
    """Normalize the externally meaningful class of effect."""
    return "/".join(
        part.strip().lower().replace(" ", "_")
        for part in (str(target or ""), str(action or ""))
    )


@dataclass(frozen=True)
class AuthorityBinding:
    payload_hash: str
    normalized_destination: str
    preview_hash: str
    preview_renderer_version: str
    effect_class: str
    policy_version: str


def authority_binding(
    *, target: str, action: str, preview: str, payload: Optional[Mapping[str, Any]]
) -> AuthorityBinding:
    """Build the complete authority tuple captured and checked by HoldSpeak."""
    return AuthorityBinding(
        payload_hash=payload_hash(payload),
        normalized_destination=normalize_destination(target, payload),
        preview_hash=_canonical_hash(str(preview or "")),
        preview_renderer_version=PREVIEW_RENDERER_VERSION,
        effect_class=effect_class(target, action),
        policy_version=POLICY_VERSION,
    )


__all__ = [
    "AuthorityBinding",
    "POLICY_VERSION",
    "PREVIEW_RENDERER_VERSION",
    "authority_binding",
    "effect_class",
    "normalize_destination",
    "payload_hash",
]
