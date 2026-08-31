"""Front Door recommendation engine (HS-156-01).

Pure recommender over facts the desk already has: hardware snapshot, catalog,
downloaded/connected state, legacy config, and explicitly-known OpenAI-compatible
endpoints.  Output: up to three COMPLETE packs (Light / Balanced / Full), each
covering all seven assignment groups + speech + TTS.  A pack that cannot be
completed is not offered.

Laws (settled design D1):
- No network-wide scan.  Only explicitly-known endpoints are probed.
- Packs never auto-change after setup.
- Cloud ingredients only when a credential already exists.
- The door never asks for an API key on the A path.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


# ── Assignment group ids (the seven user-visible groups) ──────────────────

ASSIGNMENT_GROUPS: tuple[tuple[str, str], ...] = (
    ("thoughts_notes", "Thoughts & notes"),
    ("chat_practice", "Chat practice"),
    ("writing_dictation", "Writing & dictation"),
    ("speech_recognition", "Speech recognition"),
    ("meetings", "Meetings"),
    ("agents_tools", "Agents & tools"),
    ("background", "Background"),
)

# ── Pack tier definitions ─────────────────────────────────────────────────

PACK_LIGHT = "light"
PACK_BALANCED = "balanced"
PACK_FULL = "full"

_PACK_META: dict[str, dict[str, Any]] = {
    PACK_LIGHT: {
        "id": PACK_LIGHT,
        "label": "Light",
        "summary": "Fits comfortably, fastest to get started.",
        "recommended": False,
    },
    PACK_BALANCED: {
        "id": PACK_BALANCED,
        "label": "Balanced",
        "summary": "Recommended for this hardware.",
        "recommended": True,
    },
    PACK_FULL: {
        "id": PACK_FULL,
        "label": "Full",
        "summary": "The most capable setup that fits.",
        "recommended": False,
    },
}


# ── Whisper speech models (built-in, not catalog entries) ─────────────────

_WHISPER_MODELS: dict[str, dict[str, Any]] = {
    "tiny": {"name": "tiny", "label": "Whisper tiny", "download_bytes": 75_000_000},
    "base": {"name": "base", "label": "Whisper base", "download_bytes": 142_000_000},
    "small": {"name": "small", "label": "Whisper small", "download_bytes": 466_000_000},
    "medium": {"name": "medium", "label": "Whisper medium", "download_bytes": 1_530_000_000},
}

# ── TTS models (kokoro-onnx) ──────────────────────────────────────────────

_TTS_MODEL: dict[str, Any] = {
    "id": "kokoro_v1_fp16",
    "label": "Kokoro TTS (fp16)",
    "download_bytes": 156_000_000,
    "voices_bytes": 50_000_000,
}


# ── Memory thresholds (bytes) ────────────────────────────────────────────

_8GB = 8 * 1024 ** 3
_16GB = 16 * 1024 ** 3
_32GB = 32 * 1024 ** 3


# ── Endpoint probe interface ─────────────────────────────────────────────

def _default_probe(base_url: str, *, timeout: float = 3.0) -> bool:
    """Probe a known endpoint for reachability.  Returns True if /v1/models responds."""
    import urllib.request
    import urllib.error

    url = base_url.rstrip("/") + "/v1/models"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


# ── Core recommender ──────────────────────────────────────────────────────

def _sha(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _catalog_by_id(catalog_entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in catalog_entries}


def _find_preset(
    catalog_entries: list[dict[str, Any]],
    preset_id: str,
) -> dict[str, Any] | None:
    for entry in catalog_entries:
        if entry["id"] == preset_id:
            return entry
    return None


def _endpoint_facts(
    known_endpoints: list[dict[str, Any]],
    *,
    probe: Any = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Probe known endpoints and return (reachable, probed_urls).

    Every endpoint in known_endpoints is probed exactly once.
    Unreachable endpoints get a reason field.
    """
    _probe = probe or _default_probe
    reachable: list[dict[str, Any]] = []
    probed_urls: list[str] = []

    for ep in known_endpoints:
        base_url = str(ep.get("base_url") or "").strip()
        if not base_url:
            continue
        probed_urls.append(base_url)
        if _probe(base_url):
            reachable.append({**ep, "reachable": True, "reason": None})
        else:
            reachable.append({**ep, "reachable": False, "reason": "Endpoint did not respond."})

    return reachable, probed_urls


def _build_assignment_line(
    group_id: str,
    group_label: str,
    source_label: str,
    provenance: str | None = None,
) -> dict[str, Any]:
    """Build one human-readable assignment line for a pack."""
    return {
        "group_id": group_id,
        "group_label": group_label,
        "source_label": source_label,
        "provenance": provenance,
    }


def _build_plan_entry(
    group_id: str,
    *,
    kind: str,
    preset_id: str | None = None,
    endpoint_id: str | None = None,
    endpoint_base_url: str | None = None,
    endpoint_model: str | None = None,
    legacy_model_path: str | None = None,
    runtime_id: str | None = None,
    download_bytes: int = 0,
) -> dict[str, Any]:
    """Build one machine-readable apply-plan entry for a pack."""
    return {
        "group_id": group_id,
        "kind": kind,
        "preset_id": preset_id,
        "endpoint_id": endpoint_id,
        "endpoint_base_url": endpoint_base_url,
        "endpoint_model": endpoint_model,
        "legacy_model_path": legacy_model_path,
        "runtime_id": runtime_id,
        "download_bytes": download_bytes,
    }


def _pick_llm_for_group(
    group_id: str,
    group_label: str,
    *,
    tier: str,
    catalog_entries: list[dict[str, Any]],
    reachable_endpoints: list[dict[str, Any]],
    legacy_gguf_path: str | None,
    legacy_gguf_label: str | None,
    apple_silicon: bool,
    total_memory_bytes: int | None,
    has_llama_cpp: bool,
    has_mlx: bool,
    has_cloud_credential: bool,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Pick an LLM source for one group.  Returns (display_line, plan_entry) or None."""
    mem = total_memory_bytes or 0

    # Priority 1: a reachable known endpoint (best for all tiers when available)
    for ep in reachable_endpoints:
        if ep.get("reachable"):
            return (
                _build_assignment_line(
                    group_id, group_label,
                    f"{ep.get('name', 'Server')} on {ep.get('base_url', '')}",
                    provenance="known_endpoint",
                ),
                _build_plan_entry(
                    group_id,
                    kind="endpoint",
                    endpoint_id=ep.get("id"),
                    endpoint_base_url=ep.get("base_url"),
                    endpoint_model=ep.get("model"),
                ),
            )

    # Priority 2: legacy GGUF from config (if llama.cpp available)
    if legacy_gguf_path and has_llama_cpp:
        return (
            _build_assignment_line(
                group_id, group_label,
                legacy_gguf_label or "Legacy local model",
                provenance="legacy_config",
            ),
            _build_plan_entry(
                group_id,
                kind="legacy_gguf",
                legacy_model_path=legacy_gguf_path,
                runtime_id="llama_cpp_prompt_v1",
            ),
        )

    # Priority 3: catalog preset (local download)
    if has_llama_cpp and apple_silicon:
        # Choose a preset based on tier and memory
        preset_id = _select_preset_for_tier(
            tier, mem, catalog_entries,
        )
        if preset_id:
            preset = _find_preset(catalog_entries, preset_id)
            if preset:
                source = preset.get("source", {})
                return (
                    _build_assignment_line(
                        group_id, group_label,
                        f"{preset['label']} ({_human_size(source.get('download_bytes', 0))})",
                        provenance="catalog_preset",
                    ),
                    _build_plan_entry(
                        group_id,
                        kind="catalog_download",
                        preset_id=preset_id,
                        runtime_id=preset.get("runtime_id"),
                        download_bytes=source.get("download_bytes", 0),
                    ),
                )

    # Priority 4: check non-Apple-Silicon with llama.cpp
    if has_llama_cpp and not apple_silicon:
        preset_id = _select_preset_for_tier(tier, mem, catalog_entries)
        if preset_id:
            preset = _find_preset(catalog_entries, preset_id)
            if preset:
                source = preset.get("source", {})
                return (
                    _build_assignment_line(
                        group_id, group_label,
                        f"{preset['label']} ({_human_size(source.get('download_bytes', 0))})",
                        provenance="catalog_preset",
                    ),
                    _build_plan_entry(
                        group_id,
                        kind="catalog_download",
                        preset_id=preset_id,
                        runtime_id=preset.get("runtime_id"),
                        download_bytes=source.get("download_bytes", 0),
                    ),
                )

    return None


def _select_preset_for_tier(
    tier: str,
    memory_bytes: int,
    catalog_entries: list[dict[str, Any]],
) -> str | None:
    """Pick the right catalog preset id for a tier/memory combination.

    Only ``local_artifact_preset`` entries with ``activation == "download"``
    are eligible.
    """
    downloadable = [
        e for e in catalog_entries
        if e.get("kind") == "local_artifact_preset"
        and e.get("activation") == "download"
    ]
    if not downloadable:
        return None

    # Sort by download size ascending
    downloadable.sort(key=lambda e: e.get("source", {}).get("download_bytes", 0))

    if tier == PACK_LIGHT:
        # Pick the smallest model that fits
        for entry in downloadable:
            peak = entry.get("source", {}).get("peak_free_bytes", 0)
            if memory_bytes >= peak:
                return entry["id"]
        return None

    if tier == PACK_BALANCED:
        # Pick the largest model whose peak fits comfortably (with headroom)
        best = None
        for entry in downloadable:
            peak = entry.get("source", {}).get("peak_free_bytes", 0)
            if memory_bytes >= peak * 1.5:
                best = entry["id"]
        # Fallback: the smallest that fits at all
        if best is None:
            for entry in downloadable:
                peak = entry.get("source", {}).get("peak_free_bytes", 0)
                if memory_bytes >= peak:
                    best = entry["id"]
        return best

    if tier == PACK_FULL:
        # Pick the largest model that fits
        best = None
        for entry in downloadable:
            peak = entry.get("source", {}).get("peak_free_bytes", 0)
            if memory_bytes >= peak:
                best = entry["id"]
        return best

    return None


def _human_size(n: int) -> str:
    """Format bytes as a human-readable size."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.0f} KB"
    if n < 1024 ** 3:
        return f"{n / (1024 ** 2):.0f} MB"
    return f"{n / (1024 ** 3):.1f} GB"


def _speech_line(whisper_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the speech recognition line for a pack."""
    model = _WHISPER_MODELS.get(whisper_name, _WHISPER_MODELS["base"])
    return (
        {
            "job": "speech",
            "label": f"Speech recognition -- {model['label']} ({_human_size(model['download_bytes'])})",
            "source": "builtin_whisper",
        },
        {
            "job": "speech",
            "kind": "whisper_model",
            "whisper_name": model["name"],
            "download_bytes": model["download_bytes"],
        },
    )


def _tts_line() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the TTS line for a pack."""
    total = _TTS_MODEL["download_bytes"] + _TTS_MODEL["voices_bytes"]
    return (
        {
            "job": "tts",
            "label": f"Text-to-speech -- {_TTS_MODEL['label']} ({_human_size(total)})",
            "source": "builtin_kokoro",
        },
        {
            "job": "tts",
            "kind": "kokoro_tts",
            "download_bytes": total,
        },
    )


def recommend(
    *,
    hardware: dict[str, Any],
    catalog_entries: list[dict[str, Any]],
    known_endpoints: list[dict[str, Any]],
    legacy_gguf_path: str | None = None,
    legacy_gguf_label: str | None = None,
    has_llama_cpp: bool = False,
    has_mlx: bool = False,
    has_cloud_credential: bool = False,
    probe: Any = None,
) -> dict[str, Any]:
    """Pure recommender: compute packs from the desk's existing knowledge.

    Parameters
    ----------
    hardware : dict
        The hardware snapshot from ``inspect_hardware``.
    catalog_entries : list[dict]
        The applicable catalog entries (from ``applicable_presets``).
    known_endpoints : list[dict]
        Explicitly-known OpenAI-compatible endpoints (each has at least
        ``id``, ``name``, ``base_url``).  These -- and ONLY these -- are
        probed for reachability.
    legacy_gguf_path : str | None
        The legacy config's named local GGUF model path (if any).
    legacy_gguf_label : str | None
        Human label for the legacy GGUF.
    has_llama_cpp : bool
        Whether the llama.cpp runtime is available.
    has_mlx : bool
        Whether the MLX runtime is available (Apple Silicon only).
    has_cloud_credential : bool
        Whether any cloud credential already exists.
    probe : callable | None
        Optional probe function (for testing).  Signature:
        ``probe(base_url: str) -> bool``.

    Returns
    -------
    dict with keys ``packs`` and ``facts``.
    """
    capability = hardware.get("capability", {})
    apple_silicon = bool(capability.get("apple_silicon"))
    total_memory = capability.get("total_memory_bytes")

    # Probe known endpoints
    endpoint_results, probed_urls = _endpoint_facts(known_endpoints, probe=probe)
    reachable_endpoints = [ep for ep in endpoint_results if ep.get("reachable")]

    # Determine which whisper model to use per tier
    whisper_by_tier = _whisper_for_tiers(total_memory)

    # Build packs
    packs: list[dict[str, Any]] = []
    for tier in (PACK_LIGHT, PACK_BALANCED, PACK_FULL):
        pack = _build_pack(
            tier=tier,
            catalog_entries=catalog_entries,
            reachable_endpoints=reachable_endpoints,
            legacy_gguf_path=legacy_gguf_path,
            legacy_gguf_label=legacy_gguf_label,
            apple_silicon=apple_silicon,
            total_memory_bytes=total_memory,
            has_llama_cpp=has_llama_cpp,
            has_mlx=has_mlx,
            has_cloud_credential=has_cloud_credential,
            whisper_name=whisper_by_tier.get(tier, "base"),
        )
        if pack is not None:
            packs.append(pack)

    # Facts: what was detected, for provenance chips
    facts: dict[str, Any] = {
        "apple_silicon": apple_silicon,
        "total_memory_bytes": total_memory,
        "has_llama_cpp": has_llama_cpp,
        "has_mlx": has_mlx,
        "has_cloud_credential": has_cloud_credential,
        "endpoints": endpoint_results,
        "probed_urls": probed_urls,
        "legacy_gguf_path": legacy_gguf_path,
        "legacy_gguf_label": legacy_gguf_label,
    }

    return {"packs": packs, "facts": facts}


def _whisper_for_tiers(total_memory: int | None) -> dict[str, str]:
    """Choose the whisper model name for each tier based on memory."""
    mem = total_memory or 0
    result: dict[str, str] = {}
    # Light: always base (small and reliable)
    result[PACK_LIGHT] = "base"
    # Balanced: small if >= 16GB, else base
    result[PACK_BALANCED] = "small" if mem >= _16GB else "base"
    # Full: medium if >= 32GB, small if >= 16GB, else base
    if mem >= _32GB:
        result[PACK_FULL] = "medium"
    elif mem >= _16GB:
        result[PACK_FULL] = "small"
    else:
        result[PACK_FULL] = "base"
    return result


def _build_pack(
    *,
    tier: str,
    catalog_entries: list[dict[str, Any]],
    reachable_endpoints: list[dict[str, Any]],
    legacy_gguf_path: str | None,
    legacy_gguf_label: str | None,
    apple_silicon: bool,
    total_memory_bytes: int | None,
    has_llama_cpp: bool,
    has_mlx: bool,
    has_cloud_credential: bool,
    whisper_name: str,
) -> dict[str, Any] | None:
    """Build one complete pack or return None if it cannot be completed."""
    display_lines: list[dict[str, Any]] = []
    plan_entries: list[dict[str, Any]] = []
    total_download = 0

    # Resolve each of the seven assignment groups
    for group_id, group_label in ASSIGNMENT_GROUPS:
        result = _pick_llm_for_group(
            group_id,
            group_label,
            tier=tier,
            catalog_entries=catalog_entries,
            reachable_endpoints=reachable_endpoints,
            legacy_gguf_path=legacy_gguf_path,
            legacy_gguf_label=legacy_gguf_label,
            apple_silicon=apple_silicon,
            total_memory_bytes=total_memory_bytes,
            has_llama_cpp=has_llama_cpp,
            has_mlx=has_mlx,
            has_cloud_credential=has_cloud_credential,
        )
        if result is None:
            # Cannot complete this group -> pack is not offerable
            return None
        line, plan = result
        display_lines.append(line)
        plan_entries.append(plan)
        total_download += plan.get("download_bytes", 0)

    # Speech recognition (whisper)
    speech_line, speech_plan = _speech_line(whisper_name)
    display_lines.append(speech_line)
    plan_entries.append(speech_plan)
    total_download += speech_plan.get("download_bytes", 0)

    # TTS (kokoro)
    tts_line, tts_plan = _tts_line()
    display_lines.append(tts_line)
    plan_entries.append(tts_plan)
    total_download += tts_plan.get("download_bytes", 0)

    meta = {**_PACK_META[tier]}
    return {
        **meta,
        "display_lines": display_lines,
        "plan": plan_entries,
        "total_download_bytes": total_download,
    }
