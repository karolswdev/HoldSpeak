"""Packaged, read-only inference preset catalogue for Capability Truth.

The catalogue is code/data shipped with HoldSpeak.  Reading it performs no
network access and no row/config mutation.  Local candidates deliberately do
not appear here until their immutable source and runtime qualification exist.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable

from .mesh_authority import ed25519


_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,95}$")
_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXPERIENCES = frozenset({"quick", "balanced", "deep"})


PACKAGED_CATALOG_SCHEMA_VERSION = 1
PACKAGED_CATALOG_MIN_REVISION = 1
_PACKAGED_CATALOG_KEY_ID = "holdspeak_catalog_2026_01"
_PACKAGED_CATALOG_TRUST_ROOTS = {
    _PACKAGED_CATALOG_KEY_ID: bytes.fromhex(
        "6ee091fd280a9b68554fa73c588125d47d3425c68a26ba236b4dad90f90a8f92"
    )
}
_PACKAGED_PRESETS_SOURCE: tuple[dict[str, Any], ...] = (
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen3_8b",
        "experience": "quick",
        "label": "OpenRouter · Quick Qwen",
        "provider_adapter": "openai_compatible",
        "model_id": "qwen/qwen3-8b",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 16_384},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_qwen3_8b",
            "name": "OpenRouter · Quick Qwen",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3-8b",
            "context_limit": 131_072,
            "requires_key": True,
        },
    },
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen35_35b_a3b",
        "experience": "balanced",
        "label": "OpenRouter · Balanced Qwen",
        "provider_adapter": "openai_compatible",
        "model_id": "qwen/qwen3.5-35b-a3b",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 32_768},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_qwen35_35b_a3b",
            "name": "OpenRouter · Balanced Qwen",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3.5-35b-a3b",
            "context_limit": 262_144,
            "requires_key": True,
        },
    },
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen38_27b",
        "experience": "deep",
        "label": "OpenRouter · Deep Qwen",
        "provider_adapter": "openai_compatible",
        "model_id": "qwen/qwen3.8-27b",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 32_768},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_qwen38_27b",
            "name": "OpenRouter · Deep Qwen",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3.8-27b",
            "context_limit": 262_144,
            "requires_key": True,
        },
    },
)


def _exact(value: dict[str, Any], keys: set[str], where: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{where} has invalid fields")


def _safe_text(value: Any, where: str, *, limit: int = 160) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{where} is invalid")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{where} contains control characters")
    return value


def validate_catalog(entries: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Validate the recursively closed union and return isolated copies."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ordinal, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ValueError(f"preset[{ordinal}] must be an object")
        kind = raw.get("kind")
        if kind == "hosted_profile_preset":
            _exact(raw, {"kind", "id", "experience", "label", "provider_adapter", "model_id", "boundary", "secret_requirement", "context", "applicability", "existing_profile"}, f"preset[{ordinal}]")
            if raw["provider_adapter"] != "openai_compatible" or raw["boundary"] != "external_service" or raw["secret_requirement"] != "profile_key":
                raise ValueError(f"preset[{ordinal}] has unsupported hosted authority")
            if not isinstance(raw["model_id"], str) or not _MODEL_ID.fullmatch(raw["model_id"]):
                raise ValueError(f"preset[{ordinal}].model_id is invalid")
            _exact(raw["existing_profile"], {"target_id", "name", "kind", "base_url", "model", "context_limit", "requires_key"}, f"preset[{ordinal}].existing_profile")
            profile = raw["existing_profile"]
            if profile["target_id"] != raw["id"] or profile["model"] != raw["model_id"] or profile["kind"] != "openAICompatible" or profile["base_url"] != "https://openrouter.ai/api/v1" or profile["requires_key"] is not True:
                raise ValueError(f"preset[{ordinal}] hosted profile is inconsistent")
            if type(profile["context_limit"]) is not int or not 1 <= profile["context_limit"] <= 1_000_000:
                raise ValueError(f"preset[{ordinal}] context limit is invalid")
            _safe_text(profile["name"], f"preset[{ordinal}].existing_profile.name")
        elif kind == "local_artifact_preset":
            _exact(raw, {"kind", "id", "experience", "label", "runtime_id", "format", "boundary", "source", "platforms", "applicability"}, f"preset[{ordinal}]")
            if raw["format"] not in {"gguf", "mlx_safetensors"} or raw["boundary"] != "same_device":
                raise ValueError(f"preset[{ordinal}] has invalid local format/boundary")
            _safe_text(raw["runtime_id"], f"preset[{ordinal}].runtime_id", limit=96)
            if not isinstance(raw["platforms"], list) or not raw["platforms"] or any(not isinstance(item, str) or not _ID.fullmatch(item) for item in raw["platforms"]):
                raise ValueError(f"preset[{ordinal}].platforms is invalid")
            _exact(raw["source"], {"repository", "revision", "manifest_sha256", "download_bytes", "license"}, f"preset[{ordinal}].source")
            source = raw["source"]
            if not isinstance(source["repository"], str) or not _MODEL_ID.fullmatch(source["repository"]):
                raise ValueError(f"preset[{ordinal}].source.repository is invalid")
            if not isinstance(source["revision"], str) or not re.fullmatch(r"[0-9a-f]{40,64}", source["revision"]):
                raise ValueError(f"preset[{ordinal}].source.revision is mutable")
            if not isinstance(source["manifest_sha256"], str) or not _SHA256.fullmatch(source["manifest_sha256"]):
                raise ValueError(f"preset[{ordinal}].source.manifest is invalid")
            if type(source["download_bytes"]) is not int or source["download_bytes"] <= 0:
                raise ValueError(f"preset[{ordinal}].source.download_bytes is invalid")
            _safe_text(source["license"], f"preset[{ordinal}].source.license", limit=64)
        else:
            raise ValueError(f"preset[{ordinal}].kind is invalid")

        preset_id = raw.get("id")
        if not isinstance(preset_id, str) or not _ID.fullmatch(preset_id) or preset_id in seen:
            raise ValueError(f"preset[{ordinal}].id is invalid or duplicated")
        seen.add(preset_id)
        if raw.get("experience") not in _EXPERIENCES:
            raise ValueError(f"preset[{ordinal}].experience is invalid")
        _safe_text(raw.get("label"), f"preset[{ordinal}].label")
        _exact(raw["context"], {"support", "working_ceiling_tokens"}, f"preset[{ordinal}].context") if kind == "hosted_profile_preset" else None
        if kind == "hosted_profile_preset" and (raw["context"]["support"] != "bounded" or type(raw["context"]["working_ceiling_tokens"]) is not int or not 1 <= raw["context"]["working_ceiling_tokens"] <= raw["existing_profile"]["context_limit"]):
            raise ValueError(f"preset[{ordinal}].context is invalid")
        _exact(raw["applicability"], {"state", "reason"}, f"preset[{ordinal}].applicability")
        if raw["applicability"]["state"] not in {"applicable", "unavailable"} or not (raw["applicability"]["reason"] is None or isinstance(raw["applicability"]["reason"], str)):
            raise ValueError(f"preset[{ordinal}].applicability is invalid")
        result.append(copy.deepcopy(raw))
    return tuple(result)


_PACKAGED_CATALOG_BODY = {
    "schema_version": 1,
    "catalog_revision": 1,
    "generated_at": "2026-08-01T00:00:00Z",
    "expires_at": "2036-08-01T00:00:00Z",
    "signing_key_id": _PACKAGED_CATALOG_KEY_ID,
    "entries": _PACKAGED_PRESETS_SOURCE,
}
_PACKAGED_CATALOG_SIGNATURE = "c9dea494693c3d637deea2993a9b98555fd58d27c9d1c4898b4e667068dcafd082dddfdb7a9948295dac5e882ca0e8552cbd0797c0295b050278e514a7b0eb01"
_PACKAGED_CATALOG_JSON = json.dumps(
    {**_PACKAGED_CATALOG_BODY, "signature": _PACKAGED_CATALOG_SIGNATURE},
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
)
PACKAGED_CATALOG_SHA256 = "sha256:" + hashlib.sha256(_PACKAGED_CATALOG_JSON.encode("utf-8")).hexdigest()
del _PACKAGED_PRESETS_SOURCE
del _PACKAGED_CATALOG_BODY


def verify_catalog_envelope(
    envelope_json: str,
    *,
    now: datetime,
    trust_roots: dict[str, bytes] | None = None,
    minimum_revision: int = PACKAGED_CATALOG_MIN_REVISION,
) -> dict[str, Any]:
    """Verify one canonical signed catalogue before any entry is projected."""
    raw = json.loads(envelope_json)
    _exact(raw, {"schema_version", "catalog_revision", "generated_at", "expires_at", "signing_key_id", "entries", "signature"}, "catalog")
    if raw["schema_version"] != PACKAGED_CATALOG_SCHEMA_VERSION:
        raise ValueError("catalog schema is unsupported")
    if type(raw["catalog_revision"]) is not int or raw["catalog_revision"] < minimum_revision:
        raise ValueError("catalog revision is rolled back")
    roots = _PACKAGED_CATALOG_TRUST_ROOTS if trust_roots is None else trust_roots
    public = roots.get(raw["signing_key_id"])
    if public is None:
        raise ValueError("catalog signing key is unknown")
    try:
        signature = bytes.fromhex(raw["signature"])
    except (TypeError, ValueError) as exc:
        raise ValueError("catalog signature is invalid") from exc
    body = {key: value for key, value in raw.items() if key != "signature"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if not ed25519.verify(public, canonical, signature):
        raise ValueError("catalog signature is invalid")
    try:
        generated = datetime.fromisoformat(raw["generated_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(raw["expires_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("catalog time bounds are invalid") from exc
    observed = now.astimezone(timezone.utc)
    if generated > observed or expires <= observed or expires <= generated:
        raise ValueError("catalog is not within its validity period")
    entries = validate_catalog(raw["entries"])
    return {
        "schema_version": raw["schema_version"],
        "catalog_revision": raw["catalog_revision"],
        "generated_at": raw["generated_at"],
        "expires_at": raw["expires_at"],
        "signing_key_id": raw["signing_key_id"],
        "sha256": "sha256:" + hashlib.sha256(envelope_json.encode("utf-8")).hexdigest(),
        "entries": entries,
    }


def packaged_catalog(*, now: datetime) -> dict[str, Any]:
    return verify_catalog_envelope(_PACKAGED_CATALOG_JSON, now=now)


def packaged_catalog_envelope_json() -> str:
    """Return the immutable packaged envelope for verification fixtures."""
    return _PACKAGED_CATALOG_JSON


def packaged_presets(*, now: datetime | None = None) -> tuple[dict[str, Any], ...]:
    observed = now or datetime.now(timezone.utc)
    return packaged_catalog(now=observed)["entries"]


def applicable_presets(*, platform_id: str, runtime_ids: set[str], entries: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return only packaged entries whose declared prerequisites are proven."""
    result: list[dict[str, Any]] = []
    for row in validate_catalog(packaged_presets() if entries is None else entries):
        if row["applicability"]["state"] != "applicable":
            continue
        if row["kind"] == "local_artifact_preset":
            if platform_id not in row["platforms"] or row["runtime_id"] not in runtime_ids:
                continue
        result.append(row)
    return result
