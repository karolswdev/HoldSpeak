"""Packaged, read-only inference preset catalogue for Capability Truth.

The catalogue is code/data shipped with HoldSpeak.  Reading it performs no
network access and no row/config mutation.  Local candidates deliberately do
not appear here until their immutable source and runtime qualification exist.

Revision 6 (RECIPE LINE-6) adds a third kind, ``speech_model_preset``: the
Line's two speech models (Parakeet in, Pocket TTS out), each a pinned
Hugging Face revision with every file's path, size and SHA-256 and its
licences. They are not inference presets, so :func:`applicable_presets`
leaves them out; :func:`speech_presets` reads them (``holdspeak/line/models.py``).
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
PACKAGED_CATALOG_MIN_REVISION = 6
_PACKAGED_CATALOG_KEY_ID = "holdspeak_catalog_2026_10_29"
_PACKAGED_CATALOG_TRUST_ROOTS = {
    "holdspeak_catalog_2026_08_02": bytes.fromhex(
        "dc6956be38eb49dc0c0f4c1e993bfc911ccea50632f8e742231e5cade38d809c"
    ),
    "holdspeak_catalog_2026_10_13": bytes.fromhex(
        "b6c0d32ff01baf7df5b403f83f68965af5fb87a1586ca1912e695d9ba9324605"
    ),
    _PACKAGED_CATALOG_KEY_ID: bytes.fromhex(
        "07daac564bd2f90aee6521f516e32d3c8c4db065201eadff40ea8a7611be4e9d"
    ),
}
_SPEECH_ROLES = {"stt": "onnx_asr", "tts": "pocket_tts"}
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
            "file_sha256": "sha256:00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4",
            "manifest_sha256": "sha256:b82ebc361b075d5b73abc33d07831733941515f66b51f204d3942684b1582d2a",
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
    # RECIPE LINE-6: the Line's speech models. The pins are the Hugging Face
    # revisions and the files the Line's engines load (onnx-asr's int8
    # Parakeet files; pocket-tts 4.0.1's English config, its tokenizer and
    # the voice it speaks with), each with its SHA-256 (LFS digests; the
    # small text files hashed at pinning, 2026-10-29).
    {
        "kind": "speech_model_preset",
        "id": "speech_line_parakeet_tdt_06b_v2_int8",
        "role": "stt",
        "label": "Phone speech in · Parakeet (int8, onnx-asr)",
        "summary": "Hears your words on a phone call, on this machine.",
        "runtime_id": "onnx_asr",
        "target": "line",
        "source": {
            "repository": "istupakov/parakeet-tdt-0.6b-v2-onnx",
            "revision": "0bbb45a3365852604aef28b538a8f066f4ccaa85",
            "files": [
                {"path": "config.json", "bytes": 97,
                 "sha256": "sha256:666903c76b9798caf2c210afd4f6cd60b08a8dbf9800ec8d7a3bc0d2148ac466"},
                {"path": "vocab.txt", "bytes": 9_384,
                 "sha256": "sha256:ec182b70dd42113aff6c5372c75cac58c952443eb22322f57bbd7f53977d497d"},
                {"path": "decoder_joint-model.int8.onnx", "bytes": 8_998_286,
                 "sha256": "sha256:a449f49acd68979d418651dd2dcb737cc0f1bf0225e009e29ee326354edbf7d3"},
                {"path": "encoder-model.int8.onnx", "bytes": 652_184_014,
                 "sha256": "sha256:3e0581fda6ab843888b51e56d7ee78b6d5bc3237ec113af1f732d1d5286aa155"},
            ],
            "download_bytes": 661_191_781,
            "license": "CC-BY-4.0",
            "code_license": "MIT",
            "attribution": "NVIDIA Parakeet TDT 0.6B v2 (ONNX export by istupakov)",
        },
        "applicability": {"state": "applicable", "reason": None},
    },
    {
        "kind": "speech_model_preset",
        "id": "speech_line_pocket_tts_en",
        "role": "tts",
        "label": "Phone voice · Pocket TTS",
        "summary": "Speaks the desk's answers on a phone call, on this machine.",
        "runtime_id": "pocket_tts",
        "target": "line",
        "source": {
            "repository": "kyutai/pocket-tts-without-voice-cloning",
            "revision": "a7056f505a4a8ca72d8b5fb1440071d6f1a35739",
            "files": [
                {"path": "languages/english/tokenizer.json", "bytes": 245_020,
                 "sha256": "sha256:f498428e1eafee50492f7be13dc9bfafcfc12e508cd0eb1b01c92ecd5d8c6687"},
                {"path": "languages/english/embeddings/alba.safetensors", "bytes": 6_244_152,
                 "sha256": "sha256:5850f417028fb2bf6de31e5e395e56ee7a21ac0e52ef31aebd4a6a2847d72e9c"},
                {"path": "languages/english/model.safetensors", "bytes": 219_029_196,
                 "sha256": "sha256:4c56cbd171c63e8a26ea61f5d48b8a0cd8f3c51f4652c0ab9a19bfcced8c931d"},
            ],
            "download_bytes": 225_518_368,
            "license": "CC-BY-4.0",
            "code_license": "MIT",
            "attribution": "Kyutai Pocket TTS",
        },
        "applicability": {"state": "applicable", "reason": None},
    },
)


def _validate_speech(raw: dict[str, Any], ordinal: int) -> None:
    """``speech_model_preset``: a pinned multi-file Hugging Face source."""
    where = f"preset[{ordinal}]"
    _exact(raw, {"kind", "id", "role", "label", "summary", "runtime_id", "target", "source", "applicability"}, where)
    if raw["role"] not in _SPEECH_ROLES or raw["runtime_id"] != _SPEECH_ROLES[raw["role"]] or raw["target"] != "line":
        raise ValueError(f"{where} has an invalid speech role/runtime/target")
    source = raw["source"]
    _exact(source, {"repository", "revision", "files", "download_bytes", "license", "code_license", "attribution"}, f"{where}.source")
    if not isinstance(source["repository"], str) or not _MODEL_ID.fullmatch(source["repository"]):
        raise ValueError(f"{where}.source.repository is invalid")
    if not isinstance(source["revision"], str) or not re.fullmatch(r"[0-9a-f]{40,64}", source["revision"]):
        raise ValueError(f"{where}.source.revision is mutable")
    files = source["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 16:
        raise ValueError(f"{where}.source.files is invalid")
    paths: set[str] = set()
    total = 0
    for index, item in enumerate(files):
        _exact(item, {"path", "bytes", "sha256"}, f"{where}.source.files[{index}]")
        path = item["path"]
        if (
            not isinstance(path, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}(/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}){0,3}", path)
            or ".." in path.split("/")
            or path in paths
        ):
            raise ValueError(f"{where}.source.files[{index}].path is invalid")
        paths.add(path)
        if type(item["bytes"]) is not int or item["bytes"] <= 0:
            raise ValueError(f"{where}.source.files[{index}].bytes is invalid")
        if not isinstance(item["sha256"], str) or not _SHA256.fullmatch(item["sha256"]):
            raise ValueError(f"{where}.source.files[{index}].sha256 is invalid")
        total += item["bytes"]
    if type(source["download_bytes"]) is not int or source["download_bytes"] != total:
        raise ValueError(f"{where}.source.download_bytes is inconsistent")
    for text_field in ("license", "code_license"):
        _safe_text(source[text_field], f"{where}.source.{text_field}", limit=64)
    _safe_text(source["attribution"], f"{where}.source.attribution", limit=120)


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
        if kind == "speech_model_preset":
            _validate_speech(raw, ordinal)
        elif kind == "hosted_profile_preset":
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
        if kind != "speech_model_preset" and raw.get("experience") not in _EXPERIENCES:
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
    "catalog_revision": 6,
    "generated_at": "2026-10-29T00:00:00Z",
    "expires_at": "2036-10-29T00:00:00Z",
    "signing_key_id": _PACKAGED_CATALOG_KEY_ID,
    "entries": _PACKAGED_PRESETS_SOURCE,
}
_PACKAGED_CATALOG_SIGNATURE = "8e2a04c218a57a872a3b64d00a1e29173a490154c10d19b6d566e8e1f308ad54995c11d54f0f04f4ea06098049b507b72be22a5600f32b2db94dbc931cb5110c"
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
        if row["applicability"]["state"] != "applicable" or row["kind"] == "speech_model_preset":
            continue
        if row["kind"] == "local_artifact_preset":
            if platform_id not in row["platforms"] or row["runtime_id"] not in runtime_ids:
                continue
        result.append(row)
    return result


def speech_presets(*, now: datetime | None = None) -> tuple[dict[str, Any], ...]:
    """The Line's speech models from the signed catalogue (RECIPE LINE-6)."""
    return tuple(row for row in packaged_presets(now=now) if row["kind"] == "speech_model_preset")
