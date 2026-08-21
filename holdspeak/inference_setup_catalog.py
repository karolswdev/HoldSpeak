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
PACKAGED_CATALOG_MIN_REVISION = 4
_PACKAGED_CATALOG_KEY_ID = "holdspeak_catalog_2026_08_02"
_PACKAGED_CATALOG_TRUST_ROOTS = {
    _PACKAGED_CATALOG_KEY_ID: bytes.fromhex(
        "dc6956be38eb49dc0c0f4c1e993bfc911ccea50632f8e742231e5cade38d809c"
    )
}
_PACKAGED_PRESETS_SOURCE: tuple[dict[str, Any], ...] = (
    {
        "kind": "local_artifact_preset",
        "id": "preset_local_qwen35_4b_gguf_q4km",
        "experience": "quick",
        "label": "Quick local Qwen",
        "summary": "Fast local Thought interviews and everyday writing.",
        "runtime_id": "llama_cpp_prompt_v1",
        "runtime_min_revision": "0.3.34",
        "format": "gguf",
        "boundary": "same_device",
        "activation": "download",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {
            "repository": "unsloth/Qwen3.5-4B-GGUF",
            "revision": "e87f176479d0855a907a41277aca2f8ee7a09523",
            "filename": "Qwen3.5-4B-Q4_K_M.gguf",
            "file_sha256": "sha256:1d203c2196991da08bc5b191ab4727516f476f3167e3276f75a0c5257493aadb",
            "manifest_sha256": "sha256:8eeea91e273c731f889a47405d49651dc4dcb90bc98b9a08af8135d1af44a4a8",
            "download_bytes": 2_740_937_888,
            "installed_bytes": 2_740_937_888,
            "peak_free_bytes": 5_750_000_000,
            "license": "Apache-2.0",
        },
        "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
        "applicability": {"state": "applicable", "reason": None},
    },
    {
        "kind": "local_artifact_preset",
        "id": "preset_local_qwen35_08b_gguf_q4km",
        "experience": "quick",
        "label": "Tiny local Qwen",
        "summary": "A 0.8B local model for intent, routing, and lightweight work.",
        "runtime_id": "llama_cpp_prompt_v1",
        "runtime_min_revision": "0.3.34",
        "format": "gguf",
        "boundary": "same_device",
        "activation": "download",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
        "source": {
            "repository": "unsloth/Qwen3.5-0.8B-GGUF",
            "revision": "6ab461498e2023f6e3c1baea90a8f0fe38ab64d0",
            "filename": "Qwen3.5-0.8B-Q4_K_M.gguf",
            "file_sha256": "sha256:bd258782e35f7f458f8aced1adc053e6e92e89bc735ba3be89d38a06121dc517",
            "manifest_sha256": "sha256:ec6d18c20bccb7db96fd368b275ce3017d84046e8573b1ebc7854bed83ce348b",
            "download_bytes": 532_517_120,
            "installed_bytes": 532_517_120,
            "peak_free_bytes": 1_200_000_000,
            "license": "Apache-2.0",
        },
        "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
        "applicability": {"state": "applicable", "reason": None},
    },
    {
        "kind": "local_artifact_preset",
        "id": "candidate_local_hammer21_15b_gguf_q4km",
        "experience": "quick",
        "label": "Hammer 2.1 · 1.5B",
        "summary": "A small on-device specialist for structured tool calls.",
        "runtime_id": "llama_cpp_prompt_v1",
        "runtime_min_revision": "0.3.34",
        "format": "gguf",
        "boundary": "same_device",
        "activation": "evaluation_only",
        "context": {"recommended_tokens": 8192, "ceiling_tokens": 32768},
        "source": {
            "repository": "mradermacher/Hammer2.1-1.5b-GGUF",
            "revision": "d3414318e22ced45ca3c43862269a75db5b5f2ed",
            "filename": "Hammer2.1-1.5b.Q4_K_M.gguf",
            "file_sha256": "sha256:567555510e0c72d69a5fe17a6d3a391456f4471eac97ecaf840e701161703555",
            "manifest_sha256": "sha256:e29a4d1676c4d9ca8f28132d850d0fb61eabeaf73a67e78a71a8f045382e2840",
            "download_bytes": 985_701_504,
            "installed_bytes": 985_701_504,
            "peak_free_bytes": 2_100_000_000,
            "license": "CC-BY-NC-4.0",
        },
        "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
        "applicability": {"state": "applicable", "reason": None},
    },
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen3_8b",
        "experience": "quick",
        "label": "OpenRouter · Quick Qwen",
        "summary": "A small, fast Qwen for short Notes and everyday work.",
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
        "summary": "Strong general reasoning without using a giant model.",
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
        "summary": "Deeper cloud reasoning for harder synthesis.",
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
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen37_flash",
        "experience": "quick",
        "label": "OpenRouter · Qwen Flash",
        "summary": "The quickest economical Qwen choice for everyday work.",
        "provider_adapter": "openai_compatible",
        "model_id": "qwen/qwen3.7-flash",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 16_384},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_qwen37_flash",
            "name": "OpenRouter · Qwen Flash",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3.7-flash",
            "context_limit": 1_000_000,
            "requires_key": True,
        },
    },
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_gemma4_26b",
        "experience": "balanced",
        "label": "OpenRouter · Gemma 4",
        "summary": "A capable Gemma 4 alternative for writing and synthesis.",
        "provider_adapter": "openai_compatible",
        "model_id": "google/gemma-4-26b-a4b-it",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 32_768},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_gemma4_26b",
            "name": "OpenRouter · Gemma 4",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "google/gemma-4-26b-a4b-it",
            "context_limit": 262_144,
            "requires_key": True,
        },
    },
    {
        "kind": "hosted_profile_preset",
        "id": "preset_openrouter_qwen3_coder_next",
        "experience": "deep",
        "label": "OpenRouter · Coding Qwen",
        "summary": "A coding-focused Qwen for technical plans and implementation.",
        "provider_adapter": "openai_compatible",
        "model_id": "qwen/qwen3-coder-next",
        "boundary": "external_service",
        "secret_requirement": "profile_key",
        "context": {"support": "bounded", "working_ceiling_tokens": 32_768},
        "applicability": {"state": "applicable", "reason": None},
        "existing_profile": {
            "target_id": "preset_openrouter_qwen3_coder_next",
            "name": "OpenRouter · Coding Qwen",
            "kind": "openAICompatible",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3-coder-next",
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
            _exact(raw, {"kind", "id", "experience", "label", "summary", "provider_adapter", "model_id", "boundary", "secret_requirement", "context", "applicability", "existing_profile"}, f"preset[{ordinal}]")
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
            _exact(raw, {"kind", "id", "experience", "label", "summary", "runtime_id", "runtime_min_revision", "format", "boundary", "activation", "context", "source", "platforms", "applicability"}, f"preset[{ordinal}]")
            if raw["format"] not in {"gguf", "mlx_safetensors"} or raw["boundary"] != "same_device":
                raise ValueError(f"preset[{ordinal}] has invalid local format/boundary")
            if raw["activation"] not in {"download", "evaluation_only"}:
                raise ValueError(f"preset[{ordinal}].activation is invalid")
            _safe_text(raw["runtime_id"], f"preset[{ordinal}].runtime_id", limit=96)
            if not isinstance(raw["runtime_min_revision"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", raw["runtime_min_revision"]):
                raise ValueError(f"preset[{ordinal}].runtime_min_revision is invalid")
            _exact(raw["context"], {"recommended_tokens", "ceiling_tokens"}, f"preset[{ordinal}].context")
            if (
                type(raw["context"]["recommended_tokens"]) is not int
                or type(raw["context"]["ceiling_tokens"]) is not int
                or raw["context"]["recommended_tokens"] not in {8192, 16384, 32768}
                or raw["context"]["recommended_tokens"] > raw["context"]["ceiling_tokens"]
            ):
                raise ValueError(f"preset[{ordinal}].context is invalid")
            if not isinstance(raw["platforms"], list) or not raw["platforms"] or any(not isinstance(item, str) or not _ID.fullmatch(item) for item in raw["platforms"]):
                raise ValueError(f"preset[{ordinal}].platforms is invalid")
            _exact(
                raw["source"],
                {
                    "repository", "revision", "filename", "file_sha256",
                    "manifest_sha256", "download_bytes", "installed_bytes",
                    "peak_free_bytes", "license",
                },
                f"preset[{ordinal}].source",
            )
            source = raw["source"]
            if not isinstance(source["repository"], str) or not _MODEL_ID.fullmatch(source["repository"]):
                raise ValueError(f"preset[{ordinal}].source.repository is invalid")
            if not isinstance(source["revision"], str) or not re.fullmatch(r"[0-9a-f]{40,64}", source["revision"]):
                raise ValueError(f"preset[{ordinal}].source.revision is mutable")
            if not isinstance(source["manifest_sha256"], str) or not _SHA256.fullmatch(source["manifest_sha256"]):
                raise ValueError(f"preset[{ordinal}].source.manifest is invalid")
            if not isinstance(source["file_sha256"], str) or not _SHA256.fullmatch(source["file_sha256"]):
                raise ValueError(f"preset[{ordinal}].source.file_sha256 is invalid")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", str(source["filename"])):
                raise ValueError(f"preset[{ordinal}].source.filename is invalid")
            if raw["format"] == "gguf" and not str(source["filename"]).endswith(".gguf"):
                raise ValueError(f"preset[{ordinal}].source.filename is not GGUF")
            for size_field in ("download_bytes", "installed_bytes", "peak_free_bytes"):
                if type(source[size_field]) is not int or source[size_field] <= 0:
                    raise ValueError(f"preset[{ordinal}].source.{size_field} is invalid")
            if source["installed_bytes"] != source["download_bytes"]:
                raise ValueError(f"preset[{ordinal}].source installed size is inconsistent")
            if source["peak_free_bytes"] < source["download_bytes"] * 2:
                raise ValueError(f"preset[{ordinal}].source peak storage is unsafe")
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
        _safe_text(raw.get("summary"), f"preset[{ordinal}].summary", limit=200)
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
    "catalog_revision": 4,
    "generated_at": "2026-08-21T00:00:00Z",
    "expires_at": "2036-08-01T00:00:00Z",
    "signing_key_id": _PACKAGED_CATALOG_KEY_ID,
    "entries": _PACKAGED_PRESETS_SOURCE,
}
_PACKAGED_CATALOG_SIGNATURE = "e11fe6bb369cc7ead21771c655fd45ed29e5b9606bfe23ad4d90a9e93aa02983e16c69b219ca9c1f444b38c3a23e267cc896d468f255809d9c6352a7cf7c2109"
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
