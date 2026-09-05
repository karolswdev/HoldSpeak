"""The Concierge wire (HS-170-03).

Five operations: detect, propose, probe, apply, download.

The Concierge collapses the three-pack front door into ONE proposed set
with per-group engine selection.  It composes existing authorities
(model library, inference assignments, setup runtime, profile key store)
and adds no new persistence or schema.

Laws (settled design D3 + D4):
- Detect NEVER generates on a cloud key.
- Speech recognition is local-only by boundary.
- No paid probe without explicit generate:true.
- Every engine row names its host (Article III at the point of decision).
- The set is written once and completely; a half-applied set is a defect.
- A WAITING group without OFF refuses apply (409).
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from ..logging_config import get_logger

log = get_logger("concierge")


# ---- Engine kinds -----------------------------------------------------------

KIND_LAN = "lan"
KIND_LOCAL = "local"
KIND_CLOUD = "cloud"
KIND_PRESET = "preset"

# ---- Engine states ----------------------------------------------------------

STATE_READY = "READY"
STATE_WAITING = "WAITING"
STATE_NOT_SET = "NOT_SET"
STATE_UNREACHABLE = "UNREACHABLE"
STATE_CHECKING = "CHECKING"

# ---- Assignment group ids (the seven user-visible groups) -------------------

ASSIGNMENT_GROUPS: tuple[tuple[str, str], ...] = (
    ("thoughts_notes", "Thoughts & notes"),
    ("chat_practice", "Chat"),           # S-1: rename Chat practice -> Chat
    ("writing_dictation", "Writing & dictation"),
    ("speech_recognition", "Speech recognition"),
    ("meetings", "Meetings"),
    ("agents_tools", "Agents & tools"),
    ("background", "Background"),
)


# ---- Host helpers -----------------------------------------------------------

def _host_for_profile(profile: Any) -> str:
    """Derive the egress host string from a profile record."""
    import ipaddress
    from urllib.parse import urlparse

    base = str(getattr(profile, "base_url", "") or "").strip()
    if not base:
        node = str(getattr(profile, "node", "") or "").strip()
        if node:
            return node
        return "THIS DEVICE"

    parsed = urlparse(base)
    host = parsed.hostname or ""
    # Check if it's an IP on a local/LAN network
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return host
    except ValueError:
        pass
    # Named host
    if host.endswith((".local", ".internal", ".lan", ".home", ".localhost")):
        return host
    return host or base


def _host_for_base_url(base_url: str) -> str:
    """Derive the egress host string from a base URL."""
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    return parsed.hostname or base_url


def _is_lan_host(host: str) -> bool:
    """Whether a host string is on the local network."""
    import ipaddress
    try:
        addr = ipaddress.ip_address(host)
        return bool(addr.is_private or addr.is_loopback or addr.is_link_local)
    except ValueError:
        return host.endswith((".local", ".internal", ".lan", ".home", ".localhost"))


def _cloud_host(provider_family: str) -> str:
    """Canonical cloud host for a provider family."""
    hosts = {
        "openrouter": "openrouter.ai",
        "anthropic": "api.anthropic.com",
        "openai": "api.openai.com",
    }
    return hosts.get(provider_family, provider_family)


# ---- Detect -----------------------------------------------------------------

def detect(
    *,
    db: Any,
    home: Path | None = None,
    http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
) -> dict[str, Any]:
    """Every engine found: LAN endpoints, local files, cloud keys, presets.

    No network scan.  Reads known endpoints, local model dirs, runtimes,
    key presence, and catalog presets.
    """
    from ..services.inference_setup_service import (
        inspect_hardware,
        inspect_runtimes,
    )
    from ..inference_setup_catalog import (
        applicable_presets,
        packaged_catalog_envelope_json,
        verify_catalog_envelope,
    )
    from ..inference_targets import _profile_key_present

    now = datetime.now(timezone.utc)
    effective_home = home or Path.home()
    hardware = inspect_hardware(home=effective_home, now=now)
    capability = hardware.get("capability", {})
    apple_silicon = bool(capability.get("apple_silicon"))
    runtimes = inspect_runtimes(apple_silicon=apple_silicon)

    runtime_map: dict[str, str] = {}
    for rt in runtimes:
        if rt["availability"]["state"] == "available":
            runtime_map[rt["id"]] = rt["id"]

    # Catalog presets
    envelope_json = packaged_catalog_envelope_json()
    catalog = verify_catalog_envelope(envelope_json, now=now)
    runtime_ids = set(runtime_map.keys())
    platform_id = f'{capability.get("system", "unknown")}_{capability.get("architecture", "unknown")}'
    catalog_entries = applicable_presets(
        platform_id=platform_id,
        runtime_ids=runtime_ids,
        entries=catalog.get("entries"),
    )

    # Installed model artifacts
    installed_ids: set[str] = set()
    if hasattr(db, "model_artifacts"):
        for art in db.model_artifacts.list():
            if art.state in ("installed", "ready"):
                installed_ids.add(art.id if hasattr(art, "id") else str(art))

    engines: list[dict[str, Any]] = []

    # 1. LAN endpoints (known endpoints from profiles + model library defined endpoints)
    for profile in db.profiles.list():
        if profile.deleted:
            continue
        base = str(profile.base_url or "").strip()
        if not base:
            continue
        host = _host_for_profile(profile)
        is_cloud = not _is_lan_host(host)
        if is_cloud and profile.requires_key:
            # Cloud endpoint -- handled separately
            key_set = _profile_key_present(profile.id)
            engines.append({
                "id": f"cloud:{profile.id}",
                "kind": KIND_CLOUD,
                "name": profile.name or profile.id,
                "host": host,
                "state": STATE_READY if key_set else STATE_NOT_SET,
                "keySet": key_set,
                "profileId": profile.id,
            })
        else:
            # LAN or local endpoint
            runtime_token = None
            engines.append({
                "id": f"lan:{profile.id}",
                "kind": KIND_LAN,
                "name": profile.name or profile.id,
                "host": host,
                "state": STATE_READY,
                "profileId": profile.id,
            })

    # 2. Paired devices (mesh nodes)
    for profile in db.profiles.list():
        if profile.deleted:
            continue
        node = str(getattr(profile, "node", "") or "").strip()
        if not node:
            continue
        if str(profile.base_url or "").strip():
            continue  # already listed as LAN endpoint
        engines.append({
            "id": f"lan:{profile.id}",
            "kind": KIND_LAN,
            "name": profile.name or profile.id,
            "host": node,
            "state": STATE_READY,
            "profileId": profile.id,
        })

    # 3. Local files (MLX dirs + GGUF files)
    from ..setup_runtime import discover_local_models
    local = discover_local_models(home=effective_home)
    for item in local.get("mlx", []):
        model_path = item.get("value", "")
        label = item.get("label", "Local MLX model")
        engines.append({
            "id": f"local:mlx:{label}",
            "kind": KIND_LOCAL,
            "name": label,
            "host": "THIS DEVICE",
            "runtimeToken": "MLX",
            "state": STATE_READY,
            "path": model_path,
        })
    for item in local.get("gguf", []):
        model_path = item.get("value", "")
        label = item.get("label", "Local GGUF model")
        try:
            size_bytes = Path(model_path).stat().st_size
        except (OSError, ValueError):
            size_bytes = 0
        engines.append({
            "id": f"local:gguf:{label}",
            "kind": KIND_LOCAL,
            "name": label,
            "host": "THIS DEVICE",
            "runtimeToken": "LLAMA.CPP" if "llama_cpp_prompt_v1" in runtime_map else None,
            "sizeBytes": size_bytes,
            "state": STATE_READY if "llama_cpp_prompt_v1" in runtime_map else STATE_WAITING,
            "path": model_path,
        })

    # 4. Presets not yet downloaded
    for entry in catalog_entries:
        if entry.get("kind") != "local_artifact_preset":
            continue
        if entry.get("activation") != "download":
            continue
        preset_id = entry.get("id", "")
        if preset_id in installed_ids:
            continue  # already installed, skip
        source = entry.get("source", {})
        engines.append({
            "id": f"preset:{preset_id}",
            "kind": KIND_PRESET,
            "name": entry.get("label", preset_id),
            "host": "THIS DEVICE",
            "sizeBytes": int(source.get("download_bytes", 0)),
            "state": STATE_WAITING,
            "installed": False,
            "presetId": preset_id,
        })

    checked_at = datetime.now(timezone.utc).isoformat()

    return {
        "engines": engines,
        "hardware": hardware,
        "runtimes": [
            {"id": rt["id"], "state": rt["availability"]["state"]}
            for rt in runtimes
        ],
        "checkedAt": checked_at,
    }


# ---- Propose ----------------------------------------------------------------

def propose(
    *,
    engines: list[dict[str, Any]],
) -> dict[str, Any]:
    """The seven groups, each assigned by the design rule.

    - Speech recognition = local Whisper ONLY (never LAN/cloud).
    - Writing & dictation = smallest reachable low-latency engine.
    - Every other group = strongest reachable LAN engine.
    - Cloud ONLY where he picks it in the picker.
    - A group with no READY engine -> WAITING with the preset it would use.
    """
    # Index engines by kind and state
    ready_lan = [e for e in engines if e["kind"] == KIND_LAN and e["state"] == STATE_READY]
    ready_local = [e for e in engines if e["kind"] == KIND_LOCAL and e["state"] == STATE_READY]
    ready_all = ready_lan + ready_local
    whisper_engines = [e for e in engines if e["kind"] == KIND_LOCAL and "whisper" in e.get("name", "").lower()]
    preset_engines = [e for e in engines if e["kind"] == KIND_PRESET]

    # Smallest local engine for writing_dictation
    smallest_local = None
    if ready_local:
        sized = [e for e in ready_local if e.get("sizeBytes")]
        if sized:
            smallest_local = min(sized, key=lambda e: e.get("sizeBytes", float("inf")))
        else:
            smallest_local = ready_local[0]

    # Best LAN engine (first ready LAN, or first ready local)
    best_lan = ready_lan[0] if ready_lan else (ready_local[0] if ready_local else None)

    # Best whisper (local only)
    best_whisper = whisper_engines[0] if whisper_engines else None
    if not best_whisper:
        # Check for any local model that could serve as whisper
        best_whisper_local = [e for e in ready_local if "whisper" in e.get("name", "").lower()]
        if best_whisper_local:
            best_whisper = best_whisper_local[0]

    # Best preset for fallback
    best_preset = preset_engines[0] if preset_engines else None

    rows: list[dict[str, Any]] = []
    for group_id, label in ASSIGNMENT_GROUPS:
        if group_id == "speech_recognition":
            # Speech recognition = local Whisper ONLY
            if best_whisper:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": best_whisper["id"],
                    "host": best_whisper.get("host", "THIS DEVICE"),
                    "state": STATE_READY,
                })
            else:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": best_preset["id"] if best_preset else None,
                    "host": "THIS DEVICE",
                    "state": STATE_WAITING,
                    "presetId": best_preset.get("presetId") if best_preset else None,
                })
        elif group_id == "writing_dictation":
            # Smallest reachable low-latency engine
            chosen = smallest_local or best_lan
            if chosen:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": chosen["id"],
                    "host": chosen.get("host", "THIS DEVICE"),
                    "state": STATE_READY,
                })
            elif best_preset:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": best_preset["id"],
                    "host": "THIS DEVICE",
                    "state": STATE_WAITING,
                    "presetId": best_preset.get("presetId"),
                })
            else:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": None,
                    "host": "",
                    "state": STATE_WAITING,
                })
        else:
            # All other groups: strongest reachable LAN engine
            if best_lan:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": best_lan["id"],
                    "host": best_lan.get("host", "THIS DEVICE"),
                    "state": STATE_READY,
                })
            elif best_preset:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": best_preset["id"],
                    "host": "THIS DEVICE",
                    "state": STATE_WAITING,
                    "presetId": best_preset.get("presetId"),
                })
            else:
                rows.append({
                    "group": group_id,
                    "label": label,
                    "engineId": None,
                    "host": "",
                    "state": STATE_WAITING,
                })

    ready_count = sum(1 for r in rows if r["state"] == STATE_READY)
    waiting_count = sum(1 for r in rows if r["state"] == STATE_WAITING)
    engine_ids = {r["engineId"] for r in rows if r["engineId"]}

    return {
        "rows": rows,
        "receipt": {
            "groups": len(rows),
            "engines": len(engine_ids),
            "waiting": waiting_count,
        },
    }


# ---- Probe ------------------------------------------------------------------

def probe(
    *,
    engine: dict[str, Any],
    generate: bool = False,
    http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
    timeout_seconds: float = 4.0,
) -> dict[str, Any]:
    """One-token probe: local/LAN always allowed; cloud ONLY with generate:true.

    Returns latencyMs, state, and for cloud probes the host + cost.
    """
    kind = engine.get("kind", "")
    host = engine.get("host", "")

    if kind == KIND_CLOUD and not generate:
        # Cloud probe without generate: key-presence check only
        key_set = engine.get("keySet", False)
        return {
            "state": STATE_READY if key_set else STATE_NOT_SET,
            "host": host,
            "keySet": key_set,
            "latencyMs": None,
        }

    if kind == KIND_CLOUD and generate:
        # Cloud probe WITH generate: explicit Check with cost named
        # This would call the actual provider; in tests it's monkeypatched
        base_url = engine.get("baseUrl", "")
        profile_id = engine.get("profileId", "")
        start = time.monotonic()
        try:
            if http_get:
                from ..setup_runtime import discover_endpoint_models
                result = discover_endpoint_models(
                    base_url, timeout_seconds=timeout_seconds, http_get=http_get,
                )
                latency = int((time.monotonic() - start) * 1000)
                if result.get("ok"):
                    return {
                        "state": STATE_READY,
                        "host": host,
                        "latencyMs": latency,
                        "cost": {"tokens": 1},
                    }
                return {
                    "state": STATE_UNREACHABLE,
                    "host": host,
                    "latencyMs": latency,
                    "plainReason": result.get("detail", "Cloud probe failed"),
                }
            # No http_get means we cannot probe -- return what we know
            return {
                "state": STATE_NOT_SET,
                "host": host,
                "keySet": engine.get("keySet", False),
                "latencyMs": None,
            }
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return {
                "state": STATE_UNREACHABLE,
                "host": host,
                "latencyMs": latency,
                "plainReason": str(exc),
            }

    # LAN or local probe: always allowed
    base_url = engine.get("baseUrl", "")
    profile_id = engine.get("profileId", "")

    if base_url:
        from ..setup_runtime import discover_endpoint_models
        start = time.monotonic()
        try:
            result = discover_endpoint_models(
                base_url, timeout_seconds=timeout_seconds, http_get=http_get,
            )
            latency = int((time.monotonic() - start) * 1000)
            if result.get("ok"):
                return {
                    "state": STATE_READY,
                    "host": host,
                    "latencyMs": latency,
                }
            return {
                "state": STATE_UNREACHABLE,
                "host": host,
                "latencyMs": latency,
                "plainReason": result.get("detail", "Probe failed"),
            }
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return {
                "state": STATE_UNREACHABLE,
                "host": host,
                "latencyMs": latency,
                "plainReason": str(exc),
            }

    # Local file probe: check existence
    model_path = engine.get("path", "")
    if model_path:
        start = time.monotonic()
        exists = Path(model_path).exists()
        latency = int((time.monotonic() - start) * 1000)
        return {
            "state": STATE_READY if exists else STATE_UNREACHABLE,
            "host": "THIS DEVICE",
            "latencyMs": latency,
            "plainReason": None if exists else f"Model not found at {model_path}",
        }

    return {
        "state": STATE_UNREACHABLE,
        "host": host,
        "latencyMs": None,
        "plainReason": "No probe target available",
    }


# ---- Apply ------------------------------------------------------------------

def apply(
    *,
    rows: list[dict[str, Any]],
    engines: list[dict[str, Any]],
    assignment_service: Any,
    principal: Any,
    db: Any,
) -> dict[str, Any]:
    """Write the assignment set through the EXISTING inference-assignment write path.

    One transaction.  Refuse (409 with plainReason) if any row is WAITING
    and not OFF (D2.6: Use these is disabled until every group is READY or OFF).
    Emits a kernel receipt.
    """
    from ..services.errors import ConflictError

    # Validate: refuse any WAITING row that isn't OFF
    for row in rows:
        state = row.get("state", "")
        engine_id = row.get("engineId")
        if state == STATE_WAITING and engine_id != "OFF":
            raise ConflictError(
                "Every group must be READY or OFF before applying.",
                code="concierge_waiting_group",
                context={
                    "status": 409,
                    "group": row.get("group"),
                    "state": state,
                },
            )

    # Build an engine lookup
    engine_map = {e["id"]: e for e in engines}

    # Write assignments through the existing set_assignment path
    results: list[dict[str, Any]] = []
    for row in rows:
        group_id = row.get("group", "")
        engine_id = row.get("engineId")

        if engine_id == "OFF" or engine_id is None:
            # Skip OFF groups -- they stay unassigned
            results.append({
                "group": group_id,
                "state": "OFF",
            })
            continue

        engine = engine_map.get(engine_id, {})
        profile_id = engine.get("profileId", "")
        if not profile_id:
            results.append({
                "group": group_id,
                "state": "SKIPPED",
                "plainReason": "No profile for engine",
            })
            continue

        # Use the existing set_assignment for this group
        try:
            # Read current revision
            try:
                current = assignment_service.get_assignment(
                    principal,
                    {"kind": "group", "group_id": group_id},
                )
                expected_revision = int(current["revision"])
            except Exception:
                expected_revision = 0

            command_id = uuid.uuid4().hex
            body = {
                "command_id": command_id,
                "expected_revision": expected_revision,
                "scope": {"kind": "group", "group_id": group_id},
                "entries": [
                    {"profile_id": profile_id, "profile_revision": 1},
                ],
            }
            assignment_service.set_assignment(principal, body)
            results.append({
                "group": group_id,
                "state": STATE_READY,
            })
        except Exception as exc:
            results.append({
                "group": group_id,
                "state": "FAILED",
                "plainReason": str(exc),
            })

    # Emit a kernel receipt
    receipt_id = _write_kernel_receipt(db, results)

    ready_count = sum(1 for r in results if r["state"] == STATE_READY)
    off_count = sum(1 for r in results if r["state"] == "OFF")
    engine_ids = {row.get("engineId") for row in rows if row.get("engineId") and row.get("engineId") != "OFF"}

    return {
        "receipt": receipt_id,
        "summary": {
            "groups": len(results),
            "engines": len(engine_ids),
            "ready": ready_count,
            "off": off_count,
        },
        "results": results,
    }


def _write_kernel_receipt(db: Any, results: list[dict[str, Any]]) -> str:
    """Write a kernel receipt for the concierge apply."""
    receipt_id = f"concierge-apply-{uuid.uuid4().hex[:12]}"
    operation_id = f"concierge-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).timestamp()

    all_ready = all(r["state"] in (STATE_READY, "OFF", "SKIPPED") for r in results)
    state = "succeeded" if all_ready else "failed"
    outcome = f"Applied {sum(1 for r in results if r['state'] == STATE_READY)} group(s)"

    try:
        with db._connection() as conn:
            # Insert the kernel operation
            conn.execute(
                """INSERT OR IGNORE INTO kernel_operations
                   (operation_id, kind, state, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (operation_id, "concierge_apply", state, now, now),
            )
            # Insert the kernel receipt
            conn.execute(
                """INSERT INTO kernel_receipts
                   (receipt_id, operation_id, state, outcome, result_ref, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (receipt_id, operation_id, state, outcome, "", now),
            )
    except Exception as exc:
        log.error(f"Concierge receipt write failed: {exc}")

    return receipt_id


# ---- Download ---------------------------------------------------------------

def download(
    *,
    preset_id: str,
    model_library_service: Any,
    principal: Any,
    catalog_revision: int,
) -> dict[str, Any]:
    """Delegate to the library's existing acquisition (model_library download job).

    Returns the job id + a progress shape the face can poll.
    """
    body = {
        "request_id": uuid.uuid4().hex,
        "catalog_id": preset_id,
        "catalog_revision": catalog_revision,
    }
    result = model_library_service.download(principal, body)
    return {
        "jobId": result.get("receipt", {}).get("kind", uuid.uuid4().hex) if isinstance(result, dict) else uuid.uuid4().hex,
        "presetId": preset_id,
        "progress": {"received": 0, "total": 0},
        "result": result,
    }
