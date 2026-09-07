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


# ---- Engine display name ----------------------------------------------------

import re as _re

# Known family casing map (lowercase → correct casing)
_FAMILY_CASE: dict[str, str] = {
    "gpt": "GPT", "qwen": "Qwen", "qwythos": "Qwythos", "gemma": "Gemma",
    "llama": "Llama", "mistral": "Mistral", "whisper": "Whisper", "mythos": "Mythos",
    "claude": "Claude", "phi": "Phi", "deepseek": "DeepSeek", "yi": "Yi",
    "codellama": "CodeLlama", "starcoder": "StarCoder", "falcon": "Falcon",
    "mpt": "MPT", "vicuna": "Vicuna", "solar": "Solar", "command": "Command",
}

# Quantization patterns to strip from the name into a separate token
_QUANT_RE = _re.compile(
    r'[-_ ]?'
    r'(?:UD[-_]?)?'                              # optional UD prefix
    r'(?:'
    r'[Qq](?:AT|[0-9]+)(?:[-_][Kk](?:[-_]?[A-Za-z]+)?)?'  # Q4_K_XL, Q6_K, qat, Q5_K_XL
    r'|[Ff](?:16|32|p16)'                        # f16, f32, fp16
    r'|(?:MLX[-_ ]?)?[0-9]+[Bb][Ii][Tt]'         # 4bit, MLX-4bit
    r')'
)

# Extension to strip
_EXT_RE = _re.compile(r'\.(gguf|bin|safetensors|pt|pth|onnx)$', _re.IGNORECASE)

# Provider prefix (Qwen/, meta-llama/, etc.)
_PROVIDER_PREFIX_RE = _re.compile(r'^[A-Za-z][\w-]*/+')

# mmproj file detection
_MMPROJ_RE = _re.compile(r'mmproj', _re.IGNORECASE)


def _fix_family_case(word: str) -> str:
    """Fix casing of a known family name.

    Handles words with version suffixes: 'qwen3.6' → 'Qwen3.6'.
    """
    low = word.lower()
    if low in _FAMILY_CASE:
        return _FAMILY_CASE[low]
    # Check if the alphabetic prefix matches a known family
    alpha_prefix = _re.match(r'^([a-zA-Z]+)', low)
    if alpha_prefix:
        prefix = alpha_prefix.group(1)
        if prefix in _FAMILY_CASE:
            return _FAMILY_CASE[prefix] + word[len(prefix):]
    return word


def engine_display_name(
    *,
    profile_name: str = "",
    profile_model: str = "",
    served_models: list[str] | None = None,
) -> tuple[str, str]:
    """The display name and quant token for an engine.

    Returns (name, quant) where quant may be empty.

    Priority:
    1. First served model id (from /v1/models) → cleaned
    2. profile.model field → cleaned
    3. profile.name — UNLESS it starts with 'Migrated'
    4. host:port fallback (caller provides)
    """
    candidates: list[str] = []
    if served_models:
        candidates.extend(served_models)
    if profile_model and profile_model.lower() not in ("default", ""):
        candidates.append(profile_model)
    if profile_name and not profile_name.startswith("Migrated"):
        candidates.append(profile_name)

    for raw in candidates:
        name, quant = _clean_model_name(raw)
        if name:
            return name, quant

    # Last resort: raw profile name even if Migrated
    if profile_name:
        name, quant = _clean_model_name(profile_name)
        return (name or profile_name, quant)

    return ("Unknown engine", "")


def _clean_model_name(raw: str) -> tuple[str, str]:
    """Clean a raw model name/id into (display_name, quant_token).

    Steps: strip extension, strip provider prefix, extract quant tokens,
    fix family casing, normalize separators.
    """
    s = raw.strip()
    if not s:
        return ("", "")

    # Strip file extension
    s = _EXT_RE.sub("", s)

    # Strip provider prefix (Qwen/, meta-llama/)
    s = _PROVIDER_PREFIX_RE.sub("", s)

    # Extract quant tokens
    quant_parts: list[str] = []
    def _collect_quant(m: _re.Match[str]) -> str:
        quant_parts.append(m.group(0).strip("-_ ").upper())
        return " "
    s = _QUANT_RE.sub(_collect_quant, s)
    quant = " ".join(quant_parts).strip()

    # Normalize separators: replace hyphens/underscores with spaces, collapse
    s = s.replace("-", " ").replace("_", " ")
    s = _re.sub(r'\s+', ' ', s).strip()

    # Fix family casing: the first word, and any known family word
    words = s.split()
    result: list[str] = []
    for w in words:
        fixed = _fix_family_case(w)
        if fixed != w:
            result.append(fixed)
        else:
            # Keep original casing for size tokens (35B, 8B, E4B, 1M)
            if _re.match(r'^[0-9eE]+\.?[0-9]*[bBmMkK]$', w):
                result.append(w.upper() if w[-1].lower() in "bm" else w)
            else:
                result.append(w)
    name = " ".join(result)

    return (name, quant)


def is_mmproj_file(path_or_label: str) -> bool:
    """Whether a path/label is a vision projector file (mmproj-*.gguf)."""
    return bool(_MMPROJ_RE.search(path_or_label))


def mmproj_base_name(path_or_label: str) -> str | None:
    """Extract the base model name from an mmproj filename.

    E.g. 'mmproj-Qwythos-9B.gguf' → 'Qwythos-9B'.
    Returns None if not an mmproj file.
    """
    if not is_mmproj_file(path_or_label):
        return None
    import os
    base = os.path.basename(path_or_label)
    base = _EXT_RE.sub("", base)
    # Remove mmproj prefix
    base = _re.sub(r'^mmproj[-_ ]*', '', base, flags=_re.IGNORECASE)
    return base.strip() if base.strip() else None


# ---- Profile id resolution --------------------------------------------------

def resolve_profile_id(db: Any, pid: str) -> str:
    """Resolve a profile id that may carry legacy double-prefixes.

    The Phase 143 migration left some assignment entries with
    'legacy-legacy-intel' while the actual profile row is 'legacy-intel'.
    Strip leading 'legacy-' segments until a profile exists or nothing
    is left.
    """
    if not pid:
        return pid
    # Fast path: profile exists as-is
    try:
        if db.profiles.get(pid) is not None:
            return pid
    except Exception:
        pass
    # Strip leading legacy- prefixes one at a time
    candidate = pid
    while candidate.startswith("legacy-"):
        candidate = candidate[len("legacy-"):]
        try:
            if db.profiles.get(candidate) is not None:
                return candidate
        except Exception:
            pass
    return pid  # return original if nothing resolved


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


_CGNAT_NETWORK = None  # lazy

def _is_lan_host(host: str) -> bool:
    """Whether a host string is on the local network.

    Covers RFC1918 (10/8, 172.16/12, 192.168/16), loopback (127/8),
    link-local (169.254/16), CGNAT/Tailscale (100.64/10), and named
    local suffixes (.local, .ts.net, .internal, .lan, .home, .localhost).
    """
    import ipaddress
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return True
        # CGNAT / Tailscale range 100.64.0.0/10
        global _CGNAT_NETWORK
        if _CGNAT_NETWORK is None:
            _CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
        return addr in _CGNAT_NETWORK
    except ValueError:
        return host.endswith((".local", ".internal", ".lan", ".home", ".localhost", ".ts.net"))


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
    from ..setup_runtime import discover_endpoint_models

    # 1. LAN endpoints (known endpoints from profiles + model library defined endpoints)
    for profile in db.profiles.list():
        if profile.deleted:
            continue
        base = str(profile.base_url or "").strip()
        if not base:
            continue
        host = _host_for_profile(profile)
        is_cloud = not _is_lan_host(host)
        is_lan = _is_lan_host(host)
        is_loopback = False
        try:
            import ipaddress as _ipa
            is_loopback = _ipa.ip_address(host).is_loopback
        except (ValueError, AttributeError):
            is_loopback = host in ("localhost", "127.0.0.1", "::1")

        if not is_lan and profile.requires_key:
            # Cloud endpoint
            key_set = _profile_key_present(profile.id)
            raw_label = profile.name or profile.id
            display, quant = engine_display_name(
                profile_name=raw_label,
                profile_model=str(getattr(profile, "model", "") or ""),
            )
            engines.append({
                "id": f"cloud:{profile.id}",
                "kind": KIND_CLOUD,
                "name": display,
                "quantToken": quant or None,
                "legacyLabel": raw_label,
                "host": host,
                "state": STATE_READY if key_set else STATE_NOT_SET,
                "keySet": key_set,
                "profileId": profile.id,
                # HS-200-04: the probe needs the endpoint it is meant to reach.
                # Without it `probe()` fell through to its local-file branch and
                # answered "No probe target available" for every endpoint row.
                "baseUrl": base,
            })
        else:
            # LAN or local endpoint — resolve name via /v1/models
            raw_label = profile.name or profile.id
            profile_model = str(getattr(profile, "model", "") or "")
            served_models: list[str] = []
            try:
                discovered = discover_endpoint_models(
                    base, timeout_seconds=1.5, http_get=http_get,
                )
                if discovered.get("ok"):
                    served_models = list(discovered.get("models") or [])
            except Exception:
                pass  # timeout/failure — fall back
            # Fallback name: host:port when no model resolved and label is migration
            from urllib.parse import urlparse as _up
            _parsed = _up(base)
            host_port_fallback = f"{_parsed.hostname or host}:{_parsed.port}" if _parsed.port else host
            display, quant = engine_display_name(
                profile_name=raw_label,
                profile_model=profile_model,
                served_models=served_models,
            )
            # If display is still a migration label, use host:port
            if display.startswith("Migrated"):
                display = host_port_fallback
                quant = ""
            kind = KIND_LOCAL if is_loopback else KIND_LAN
            engines.append({
                "id": f"{kind}:{profile.id}",
                "kind": kind,
                "name": display,
                "quantToken": quant or None,
                "legacyLabel": raw_label,
                "host": host,
                "state": STATE_READY,
                "profileId": profile.id,
                "baseUrl": base,
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
        raw_label = profile.name or profile.id
        display, quant = engine_display_name(
            profile_name=raw_label,
            profile_model=str(getattr(profile, "model", "") or ""),
        )
        engines.append({
            "id": f"lan:{profile.id}",
            "kind": KIND_LAN,
            "name": display,
            "quantToken": quant or None,
            "legacyLabel": raw_label,
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
        display, quant = engine_display_name(profile_name=label)
        engines.append({
            "id": f"local:mlx:{label}",
            "kind": KIND_LOCAL,
            "name": display,
            "quantToken": quant or None,
            "legacyLabel": label,
            "host": "THIS DEVICE",
            "runtimeToken": "MLX",
            "state": STATE_READY,
            "path": model_path,
        })
    # Collect GGUF engines and mmproj files separately
    gguf_engines: list[dict[str, Any]] = []
    mmproj_bases: set[str] = set()
    for item in local.get("gguf", []):
        model_path = item.get("value", "")
        label = item.get("label", "Local GGUF model")
        if is_mmproj_file(label) or is_mmproj_file(model_path):
            base = mmproj_base_name(label) or mmproj_base_name(model_path)
            if base:
                mmproj_bases.add(base.lower())
            continue  # never a FOUND row
        try:
            size_bytes = Path(model_path).stat().st_size
        except (OSError, ValueError):
            size_bytes = 0
        display, quant = engine_display_name(profile_name=label)
        gguf_engines.append({
            "id": f"local:gguf:{label}",
            "kind": KIND_LOCAL,
            "name": display,
            "quantToken": quant or None,
            "legacyLabel": label,
            "host": "THIS DEVICE",
            "runtimeToken": "LLAMA.CPP" if "llama_cpp_prompt_v1" in runtime_map else None,
            "sizeBytes": size_bytes,
            "state": STATE_READY if "llama_cpp_prompt_v1" in runtime_map else STATE_WAITING,
            "path": model_path,
        })
    # Attach VISION token to engines whose name matches an mmproj base
    for eng in gguf_engines:
        eng_label = (eng.get("legacyLabel") or "").lower()
        for mp_base in mmproj_bases:
            if mp_base in eng_label:
                eng["visionToken"] = "VISION"
                break
    engines.extend(gguf_engines)

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


# ---- Repair states (HS-200-04) ----------------------------------------------
#
# The setup verdict says `needs_attention`; that word repairs nothing.  Four
# named states, each with ONE verb that opens an existing control:
#
#   MODEL FILE MISSING   Download    -> the Model Library acquisition
#   ENDPOINT UNREACHABLE Check       -> the endpoint editor (Add an engine...)
#   TOOL INCOMPATIBLE    Choose      -> the group's engine picker
#   CREDENTIAL EXPIRED   Connections -> the Connections door
#
# Every row is derived from an ASSIGNED route or a real source connection: a
# repair the product will actually hit, never a warning about something nothing
# uses.  No prose, no second doctor, no new persistence.

REPAIR_MODEL_FILE_MISSING = "MODEL FILE MISSING"
REPAIR_ENDPOINT_UNREACHABLE = "ENDPOINT UNREACHABLE"
REPAIR_TOOL_INCOMPATIBLE = "TOOL INCOMPATIBLE"
REPAIR_CREDENTIAL_EXPIRED = "CREDENTIAL EXPIRED"

# One verb per state.  The face renders the verb as the library Button and
# routes on `control`; it never decides the policy.
_REPAIR_VERBS: dict[str, tuple[str, str]] = {
    REPAIR_MODEL_FILE_MISSING: ("Download", "model_library"),
    REPAIR_ENDPOINT_UNREACHABLE: ("Check", "endpoint_editor"),
    REPAIR_TOOL_INCOMPATIBLE: ("Choose", "engine_picker"),
    REPAIR_CREDENTIAL_EXPIRED: ("Connections", "connections"),
}

# The order the rows are shown in: the states that block work outright first.
_REPAIR_ORDER = (
    REPAIR_CREDENTIAL_EXPIRED,
    REPAIR_ENDPOINT_UNREACHABLE,
    REPAIR_MODEL_FILE_MISSING,
    REPAIR_TOOL_INCOMPATIBLE,
)

# A source connection in one of these states needs the owner's credential.
_SOURCE_NEEDS_OWNER = frozenset({"owner_action_required", "disconnected", "revoked"})

_GROUP_LABELS: dict[str, str] = dict(ASSIGNMENT_GROUPS)


def _repair_row(
    token: str,
    *,
    subject: str,
    host: str,
    scope: str,
    groups: list[str],
    engine_id: str = "",
    preset_id: str = "",
    base_url: str = "",
    detail: str = "",
) -> dict[str, Any]:
    verb, control = _REPAIR_VERBS[token]
    return {
        "id": f"{token.lower().replace(' ', '-')}:{subject}",
        "token": token,
        "subject": subject,
        "host": host,
        "scope": scope,
        "groups": groups,
        "groupLabels": [_GROUP_LABELS.get(g, g) for g in groups],
        "verb": verb,
        "control": control,
        "engineId": engine_id,
        "presetId": preset_id,
        "baseUrl": base_url,
        "detail": detail,
    }


def _assigned_entries(
    assignment_service: Any, principal: Any
) -> list[tuple[str, dict[str, Any], list[dict[str, Any]]]]:
    """(group_id, first entry, blocking issues) for every assigned group.

    Reads the existing seven-row owner roster; it never re-derives assignment
    precedence here.
    """
    try:
        summary = assignment_service.assignment_summary(principal)
    except Exception as exc:  # pragma: no cover - a roster read never blocks the face
        log.warning(f"concierge repairs: assignment summary unavailable ({exc})")
        return []
    out: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    for row in summary.get("rows") or []:
        group_id = str(row.get("id") or "")
        if group_id in ("", "global"):
            continue
        projection = row.get("assignment")
        if not isinstance(projection, dict):
            continue
        entries = [e for e in (projection.get("entries") or []) if isinstance(e, dict)]
        if not entries:
            continue
        blocking = [
            issue
            for issue in (projection.get("issues") or [])
            if isinstance(issue, dict) and issue.get("severity") == "blocking"
        ]
        out.append((group_id, entries[0], blocking))
    return out


def repairs(
    *,
    db: Any,
    assignment_service: Any = None,
    principal: Any = None,
    http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
    timeout_seconds: float = 1.5,
) -> list[dict[str, Any]]:
    """The named repair states for the routes this product will actually use.

    Deduped by (state, subject): one engine that four groups share is one row
    naming the four groups, not four rows.
    """
    from ..inference_targets import _profile_key_present, local_model_file_present
    from ..setup_runtime import discover_endpoint_models

    found: dict[tuple[str, str], dict[str, Any]] = {}

    def _add(row: dict[str, Any]) -> None:
        key = (row["token"], row["subject"])
        existing = found.get(key)
        if existing is None:
            found[key] = row
            return
        for group in row["groups"]:
            if group not in existing["groups"]:
                existing["groups"].append(group)
                existing["groupLabels"].append(_GROUP_LABELS.get(group, group))

    # Endpoint reachability is read at most once per endpoint, for assigned
    # routes only.  A bounded read, never a scan.
    reachable: dict[str, bool] = {}

    def _reachable(base_url: str) -> bool:
        if base_url not in reachable:
            try:
                result = discover_endpoint_models(
                    base_url, timeout_seconds=timeout_seconds, http_get=http_get
                )
                reachable[base_url] = bool(result.get("ok"))
            except Exception:
                reachable[base_url] = False
        return reachable[base_url]

    if assignment_service is not None and principal is not None:
        for group_id, entry, blocking in _assigned_entries(assignment_service, principal):
            label = str(entry.get("label") or entry.get("profile_id") or "")
            if blocking:
                _add(
                    _repair_row(
                        REPAIR_TOOL_INCOMPATIBLE,
                        subject=label,
                        host="",
                        scope="local",
                        groups=[group_id],
                        detail=",".join(
                            sorted({str(i.get("code") or "") for i in blocking})
                        ),
                    )
                )
                continue
            profile_id = resolve_profile_id(db, str(entry.get("profile_id") or ""))
            try:
                profile = db.profiles.get(profile_id)
            except Exception:
                profile = None
            if profile is None or getattr(profile, "deleted", False):
                continue
            host = _host_for_profile(profile)
            base_url = str(getattr(profile, "base_url", "") or "").strip()
            model_file = str(getattr(profile, "model_file", "") or "").strip()
            requires_key = bool(getattr(profile, "requires_key", False))
            name = str(getattr(profile, "name", "") or profile_id)
            engine_kind = (
                KIND_CLOUD
                if base_url and not _is_lan_host(host) and requires_key
                else (KIND_LAN if base_url else KIND_LOCAL)
            )
            engine_id = f"{engine_kind}:{profile_id}"

            if requires_key and not _profile_key_present(profile_id):
                _add(
                    _repair_row(
                        REPAIR_CREDENTIAL_EXPIRED,
                        subject=name,
                        host=host,
                        scope="cloud" if engine_kind == KIND_CLOUD else "local",
                        groups=[group_id],
                        engine_id=engine_id,
                    )
                )
            elif model_file and not local_model_file_present(model_file):
                _add(
                    _repair_row(
                        REPAIR_MODEL_FILE_MISSING,
                        subject=name,
                        host="THIS DEVICE",
                        scope="local",
                        groups=[group_id],
                        engine_id=engine_id,
                    )
                )
            elif (
                base_url
                # A cloud endpoint is never read without his verb (D4): a key
                # that is set is all this list can honestly say about it. Its
                # reachability belongs to the row's own `Check`.
                and engine_kind != KIND_CLOUD
                and _is_lan_host(host)
                and not _reachable(base_url)
            ):
                _add(
                    _repair_row(
                        REPAIR_ENDPOINT_UNREACHABLE,
                        subject=name,
                        host=host,
                        scope="cloud" if engine_kind == KIND_CLOUD else "local",
                        groups=[group_id],
                        engine_id=engine_id,
                        base_url=base_url,
                    )
                )

    # Source credentials: the Connections door owns their repair.
    try:
        connections = db.automations.list_provider_connections()
    except Exception:
        connections = []
    for row in connections or []:
        state = str((row or {}).get("state") or "")
        if state not in _SOURCE_NEEDS_OWNER:
            continue
        provider_id = str(row.get("provider_id") or "")
        _add(
            _repair_row(
                REPAIR_CREDENTIAL_EXPIRED,
                subject=provider_id,
                host=provider_id,
                scope="cloud",
                groups=[],
                detail=str(row.get("last_error_code") or ""),
            )
        )

    order = {token: index for index, token in enumerate(_REPAIR_ORDER)}
    return sorted(
        found.values(), key=lambda row: (order.get(row["token"], 99), row["subject"])
    )


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
