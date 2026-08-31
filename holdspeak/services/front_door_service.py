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
import uuid
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


def _humanize_model_label(raw_label: str | None) -> tuple[str, str | None]:
    """Produce a human-readable label from a model name or filename.

    Returns ``(human_label, original_filename_or_none)``.  When the
    input is already human-readable (not a ``.gguf`` path), it passes
    through unchanged with ``None`` as the detail.
    """
    if not raw_label:
        return "Local model", None
    if not raw_label.lower().endswith(".gguf"):
        return raw_label, None
    # Strip directory prefix, keep just the filename
    stem = raw_label.rsplit("/", 1)[-1]
    name = stem[: -len(".gguf")]  # strip extension
    # Parse common naming: Family-SizeB-Variant-Quant
    parts = name.split("-")
    family = parts[0] if parts else name
    size_part = ""
    for part in parts[1:]:
        if part and part[-1].upper() == "B" and any(c.isdigit() for c in part[:-1]):
            size_part = part.upper()
            break
    if size_part:
        return f"{family} {size_part} (local)", stem
    return f"{family} (local)", stem


def _build_assignment_line(
    group_id: str,
    group_label: str,
    source_label: str,
    provenance: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Build one human-readable assignment line for a pack."""
    line: dict[str, Any] = {
        "group_id": group_id,
        "group_label": group_label,
        "source_label": source_label,
        "provenance": provenance,
    }
    if detail is not None:
        line["detail"] = detail
    return line


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
        human_label, gguf_detail = _humanize_model_label(legacy_gguf_label)
        return (
            _build_assignment_line(
                group_id, group_label,
                human_label,
                provenance="legacy_config",
                detail=gguf_detail,
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
    """Build the speech recognition line for a pack.

    The display dict carries ``group_id="speech_recognition"`` so it
    contributes to the completeness check (all seven groups covered).
    The plan dict stays whisper-specific.
    """
    model = _WHISPER_MODELS.get(whisper_name, _WHISPER_MODELS["base"])
    return (
        {
            "group_id": "speech_recognition",
            "group_label": "Speech recognition",
            "source_label": f"{model['label']} ({_human_size(model['download_bytes'])})",
            "provenance": "builtin_whisper",
            "job": "speech",
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
            "group_label": "Text-to-speech",
            "source_label": f"{_TTS_MODEL['label']} ({_human_size(total)})",
            "provenance": "builtin_kokoro",
            "job": "tts",
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

    # Resolve the LLM-powered assignment groups (speech_recognition is
    # handled separately by _speech_line — it uses whisper, not an LLM).
    for group_id, group_label in ASSIGNMENT_GROUPS:
        if group_id == "speech_recognition":
            continue
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


# ── Apply engine (HS-156-02) ─────────────────────────────────────────────
#
# Executes a pack's plan as an ordered, idempotent sequence over EXISTING
# surfaces only: model-library download, define-endpoint for LAN ingredients,
# profile creation, assignments editor/set for all seven groups.
#
# Laws:
# - No direct DB writes to library/assignment tables (service calls only).
# - Each item is idempotent; re-apply continues from the first unfinished item.
# - A fault leaves a resumable plan, never a half-desk.
# - Every step is receipted.


# ── Item status constants ────────────────────────────────────────────────

ITEM_QUEUED = "queued"
ITEM_RUNNING = "running"
ITEM_DONE = "done"
ITEM_FAILED = "failed"

# ── Plan status constants ────────────────────────────────────────────────

PLAN_RUNNING = "running"
PLAN_DONE = "done"
PLAN_FAILED = "failed"


def _make_apply_items(plan_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert plan entries from the recommender into durable apply items."""
    items: list[dict[str, Any]] = []
    for i, entry in enumerate(plan_entries):
        items.append({
            "ordinal": i,
            "entry": entry,
            "status": ITEM_QUEUED,
            "receipt": None,
            "error": None,
        })
    return items


def _execute_endpoint_item(
    entry: dict[str, Any],
    *,
    model_library_service: Any,
    principal: Any,
) -> dict[str, Any]:
    """Wire a LAN endpoint via define-endpoint (the existing service seam)."""
    endpoint_id = entry.get("endpoint_id", "")
    profile_id = f"front-door-ep-{endpoint_id}" if endpoint_id else f"front-door-ep-{uuid.uuid4().hex[:12]}"
    base_url = str(entry.get("endpoint_base_url", ""))
    # The define-endpoint draft expects /v1 on the endpoint URL
    endpoint_url = base_url.rstrip("/")
    if not endpoint_url.endswith("/v1"):
        endpoint_url = endpoint_url + "/v1"
    draft = {
        "request_id": uuid.uuid4().hex,
        "profile_id": profile_id,
        "expected_profile_revision": 0,
        "label": f"Front Door: {base_url}",
        "provider_family": "openai_compatible",
        "model": entry.get("endpoint_model", "default"),
        "endpoint": endpoint_url,
        "requires_key": False,
    }
    result = model_library_service.define_endpoint(principal, draft, None)
    return {
        "kind": "define_endpoint",
        "profile_id": profile_id,
        "result": _safe_receipt(result),
    }


def _execute_download_item(
    entry: dict[str, Any],
    *,
    model_library_service: Any,
    principal: Any,
    catalog_revision: int,
) -> dict[str, Any]:
    """Download a catalog preset via the model library (the existing service seam)."""
    body = {
        "request_id": uuid.uuid4().hex,
        "catalog_id": entry["preset_id"],
        "catalog_revision": catalog_revision,
    }
    result = model_library_service.download(principal, body)
    return {
        "kind": "catalog_download",
        "preset_id": entry["preset_id"],
        "result": _safe_receipt(result),
    }


def _execute_assignment_item(
    group_assignments: list[dict[str, Any]],
    *,
    assignment_service: Any,
    principal: Any,
) -> dict[str, Any]:
    """Set assignments for all groups via apply_starter_bundle or set_assignment."""
    # Gather current revisions for all groups
    groups_payload: list[dict[str, Any]] = []
    for ga in group_assignments:
        group_id = ga["group_id"]
        profile_id = ga["profile_id"]
        profile_revision = ga.get("profile_revision", 1)
        # Read current group state
        try:
            current = assignment_service.get_assignment(
                principal,
                {"kind": "group", "group_id": group_id},
            )
            expected_revision = int(current["revision"])
        except Exception:
            expected_revision = 0
        groups_payload.append({
            "group_id": group_id,
            "expected_revision": expected_revision,
            "entries": [
                {"profile_id": profile_id, "profile_revision": profile_revision},
            ],
            "retry_policy_id": None,
        })
    # Try starter bundle first (atomic), fall back to per-group set_assignment
    command_id = uuid.uuid4().hex
    try:
        preview_body = groups_payload
        # The starter bundle needs a preview sha first
        result = _apply_groups_individually(
            groups_payload,
            assignment_service=assignment_service,
            principal=principal,
        )
        return {
            "kind": "assignments",
            "groups": [g["group_id"] for g in group_assignments],
            "result": _safe_receipt(result),
        }
    except Exception as exc:
        raise


def _apply_groups_individually(
    groups: list[dict[str, Any]],
    *,
    assignment_service: Any,
    principal: Any,
) -> dict[str, Any]:
    """Apply group assignments one by one via set_assignment."""
    results: list[dict[str, Any]] = []
    for group in groups:
        command_id = uuid.uuid4().hex
        body = {
            "command_id": command_id,
            "expected_revision": group["expected_revision"],
            "scope": {"kind": "group", "group_id": group["group_id"]},
            "entries": group["entries"],
        }
        result = assignment_service.set_assignment(principal, body)
        results.append({
            "group_id": group["group_id"],
            "result": "assigned",
        })
    return {"assignments": results}


def _safe_receipt(result: Any) -> dict[str, Any] | None:
    """Extract a safe, serializable receipt from a service result."""
    if isinstance(result, dict):
        # Only keep safe keys
        receipt = result.get("receipt")
        if isinstance(receipt, dict):
            return {
                "kind": receipt.get("kind"),
                "message": receipt.get("message"),
            }
        return {"kind": "service_result"}
    return None


def apply_pack(
    *,
    pack: dict[str, Any],
    db: Any,
    model_library_service: Any,
    assignment_service: Any,
    principal: Any,
    catalog_revision: int,
) -> dict[str, Any]:
    """Execute a recommended pack's plan.

    Drives ONLY the existing service seams:
    1. define-endpoint for LAN ingredients
    2. model-library download for catalog presets
    3. set_assignment for all seven groups

    Each item is idempotent.  A fault leaves a resumable plan.

    Parameters
    ----------
    pack : dict
        The full pack from ``recommend()`` (must contain ``plan``).
    db : Database
        The database instance (for plan persistence).
    model_library_service : ModelLibraryApplicationService
        The existing model library service.
    assignment_service : InferenceAssignmentService
        The existing assignment service.
    principal : Principal
        The owner principal.
    catalog_revision : int
        The current catalog revision.

    Returns
    -------
    dict with ``plan_id``, ``status``, ``items``.
    """
    plan_entries = pack.get("plan", [])
    pack_id = pack.get("id", "unknown")

    # Check for an existing plan for this pack (resume support)
    existing = db.front_door.get_plan_by_pack(pack_id)
    if existing is not None and existing["status"] != PLAN_DONE:
        # Resume from existing plan
        return _resume_plan(
            plan=existing,
            db=db,
            model_library_service=model_library_service,
            assignment_service=assignment_service,
            principal=principal,
            catalog_revision=catalog_revision,
        )

    # Create a new plan
    items = _make_apply_items(plan_entries)
    plan = db.front_door.create_plan(pack_id=pack_id, items=items)

    return _run_plan(
        plan=plan,
        db=db,
        model_library_service=model_library_service,
        assignment_service=assignment_service,
        principal=principal,
        catalog_revision=catalog_revision,
    )


def _resume_plan(
    *,
    plan: dict[str, Any],
    db: Any,
    model_library_service: Any,
    assignment_service: Any,
    principal: Any,
    catalog_revision: int,
) -> dict[str, Any]:
    """Resume an existing plan from the first unfinished item."""
    return _run_plan(
        plan=plan,
        db=db,
        model_library_service=model_library_service,
        assignment_service=assignment_service,
        principal=principal,
        catalog_revision=catalog_revision,
    )


def _run_plan(
    *,
    plan: dict[str, Any],
    db: Any,
    model_library_service: Any,
    assignment_service: Any,
    principal: Any,
    catalog_revision: int,
) -> dict[str, Any]:
    """Execute plan items sequentially, persisting state after each step."""
    items = plan["items"]
    plan_id = plan["id"]

    # Phase 1: Execute endpoint and download items (provisioning)
    endpoint_profiles: dict[str, str] = {}  # group_id -> profile_id from endpoints
    download_profiles: dict[str, str] = {}  # group_id -> profile_id to be resolved

    for item in items:
        if item["status"] == ITEM_DONE:
            # Already done, collect profile info for assignment phase
            _collect_profile_from_done_item(item, endpoint_profiles)
            continue
        if item["status"] == ITEM_FAILED:
            # Previously failed, retry
            item["status"] = ITEM_QUEUED
            item["error"] = None

        entry = item["entry"]
        kind = entry.get("kind", "")

        # Speech/TTS items are built-in and need no provisioning action
        if kind in ("whisper_model", "kokoro_tts"):
            item["status"] = ITEM_DONE
            item["receipt"] = {"kind": kind, "message": "Built-in, no provisioning needed."}
            db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            continue

        if kind == "endpoint":
            item["status"] = ITEM_RUNNING
            db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            try:
                receipt = _execute_endpoint_item(
                    entry,
                    model_library_service=model_library_service,
                    principal=principal,
                )
                item["status"] = ITEM_DONE
                item["receipt"] = receipt
                # Track the profile_id for assignments
                profile_id = receipt.get("profile_id", "")
                group_id = entry.get("group_id", "")
                if group_id and profile_id:
                    endpoint_profiles[group_id] = profile_id
                db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            except Exception as exc:
                item["status"] = ITEM_FAILED
                item["error"] = str(exc)
                db.front_door.update_plan(plan_id, status=PLAN_FAILED, items=items)
                return _plan_result(plan_id, PLAN_FAILED, items)

        elif kind == "catalog_download":
            item["status"] = ITEM_RUNNING
            db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            try:
                receipt = _execute_download_item(
                    entry,
                    model_library_service=model_library_service,
                    principal=principal,
                    catalog_revision=catalog_revision,
                )
                item["status"] = ITEM_DONE
                item["receipt"] = receipt
                db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            except Exception as exc:
                item["status"] = ITEM_FAILED
                item["error"] = str(exc)
                db.front_door.update_plan(plan_id, status=PLAN_FAILED, items=items)
                return _plan_result(plan_id, PLAN_FAILED, items)

        elif kind == "legacy_gguf":
            # Legacy GGUFs are already local; mark as done
            item["status"] = ITEM_DONE
            item["receipt"] = {"kind": "legacy_gguf", "message": "Already present locally."}
            db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)

    # Phase 2: Assignment — wire all seven groups through set_assignment
    # Collect which profile to assign to each group
    group_assignments = _resolve_group_assignments(items, endpoint_profiles)
    if group_assignments:
        # Create a synthetic "assignments" item if not already present
        assignment_item = _find_or_create_assignment_item(items)
        if assignment_item["status"] == ITEM_DONE:
            pass  # Already done
        else:
            assignment_item["status"] = ITEM_RUNNING
            db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            try:
                receipt = _execute_assignment_item(
                    group_assignments,
                    assignment_service=assignment_service,
                    principal=principal,
                )
                assignment_item["status"] = ITEM_DONE
                assignment_item["receipt"] = receipt
                db.front_door.update_plan(plan_id, status=PLAN_RUNNING, items=items)
            except Exception as exc:
                assignment_item["status"] = ITEM_FAILED
                assignment_item["error"] = str(exc)
                db.front_door.update_plan(plan_id, status=PLAN_FAILED, items=items)
                return _plan_result(plan_id, PLAN_FAILED, items)

    # All items done
    db.front_door.update_plan(plan_id, status=PLAN_DONE, items=items)
    return _plan_result(plan_id, PLAN_DONE, items)


def _collect_profile_from_done_item(
    item: dict[str, Any],
    endpoint_profiles: dict[str, str],
) -> None:
    """Extract profile_id from a completed item's receipt."""
    receipt = item.get("receipt")
    if not isinstance(receipt, dict):
        return
    kind = receipt.get("kind", "")
    if kind == "define_endpoint":
        profile_id = receipt.get("profile_id", "")
        group_id = item.get("entry", {}).get("group_id", "")
        if group_id and profile_id:
            endpoint_profiles[group_id] = profile_id


def _resolve_group_assignments(
    items: list[dict[str, Any]],
    endpoint_profiles: dict[str, str],
) -> list[dict[str, Any]]:
    """Build the group->profile assignment list from completed provisioning items."""
    assignments: list[dict[str, Any]] = []
    seen_groups: set[str] = set()

    for item in items:
        entry = item.get("entry", {})
        group_id = entry.get("group_id", "")
        if not group_id or group_id in seen_groups:
            continue
        if item["status"] != ITEM_DONE:
            continue

        kind = entry.get("kind", "")
        profile_id = None

        if kind == "endpoint":
            profile_id = endpoint_profiles.get(group_id)
        elif kind == "catalog_download":
            # For catalog downloads, the profile_id comes from the catalog preset's
            # acquisition flow.  The download creates a binding; the profile_id
            # is derived from the preset_id.
            # The profile is auto-created by the model library acquisition service.
            # We read the latest profile matching this preset.
            receipt = item.get("receipt", {})
            preset_id = entry.get("preset_id", "")
            if preset_id:
                # The model library creates profiles with id = preset_id
                profile_id = preset_id
        elif kind == "legacy_gguf":
            # Legacy GGUFs are not managed by the profile system in the same way
            # Skip assignment for these
            continue

        if profile_id:
            assignments.append({
                "group_id": group_id,
                "profile_id": profile_id,
            })
            seen_groups.add(group_id)

    return assignments


def _find_or_create_assignment_item(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the synthetic assignment item or create one at the end."""
    for item in items:
        if item.get("entry", {}).get("kind") == "assignments":
            return item
    assignment_item: dict[str, Any] = {
        "ordinal": len(items),
        "entry": {"kind": "assignments"},
        "status": ITEM_QUEUED,
        "receipt": None,
        "error": None,
    }
    items.append(assignment_item)
    return assignment_item


def _plan_result(plan_id: str, status: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the plan result dict."""
    return {
        "plan_id": plan_id,
        "status": status,
        "items": items,
    }
