"""Plugin manifest + SDK shape for the meeting-intel plugin ecosystem.

HS-35-02. The 14 built-in meeting-intel plugins are hardcoded in
`holdspeak/plugins/builtin/` — no manifest, no discovery. This module is
the externalizable contract that lets a plugin ship *outside* the
built-in set: a static `PluginManifest` describing what the plugin is,
what host capabilities it needs, and which profiles/intents it wants to
fire on, validated up front with every error surfaced at once.

It deliberately mirrors `holdspeak/connector_sdk.py` (the proven
connector-pack precedent) so the two ecosystems read the same. Plugins
themselves implement the `HostPlugin` contract — see
`holdspeak/plugins/host.py` and `docs/PLUGIN_AUTHORING.md`.

Like `connector_sdk`, this ships no remote distribution mechanism: the
manifest is reusable shape, not a marketplace. The discovery loader
(`holdspeak/plugin_pack_loader.py`) reads first-party + local user packs
only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

# ──────────────────────────── Constants ─────────────────────────────

# Plugin kinds the host understands today. These match the `kind` values
# the 14 built-ins declare (see `plugins/builtin/__init__.py`). `actuator`
# is intentionally absent — actuators stay blocked until Phase 36, so a
# pack cannot yet declare one.
KNOWN_PLUGIN_KINDS: frozenset[str] = frozenset(
    {
        "synthesizer",        # structured intermediate data (decisions, requirements, …)
        "validator",          # flags gaps/issues (owner-less action items, scope creep)
        "artifact_generator", # a diagram or formatted document
        "signals",            # extracted customer/intelligence signals
        "detector",           # identifies associated projects/entities
    }
)

# Host capabilities a plugin may require. The host gates execution on
# these (a plugin requiring an un-enabled capability is *blocked*, not
# failed). `llm` is the only one today — declared by every LLM-backed
# plugin (see `PluginHost._missing_capabilities`).
KNOWN_PLUGIN_CAPABILITIES: frozenset[str] = frozenset({"llm"})

# Valid execution modes. `inline` runs during window dispatch; `deferred`
# queues the run for the background worker. Mirrors the host's
# `_is_deferred_plugin` (which also accepts queued/queue/heavy synonyms,
# but the manifest contract is the strict pair).
KNOWN_EXECUTION_MODES: frozenset[str] = frozenset({"inline", "deferred"})

# Profiles + intents a plugin may hint it wants to join. These mirror
# `holdspeak.plugins.router.PROFILE_PLUGIN_BASE_CHAINS` keys +
# `SUPPORTED_INTENTS`. Kept as local constants (like connector_sdk's
# KNOWN_KINDS) so the SDK stays dependency-light; a unit test asserts they
# stay in sync with the router (see `test_plugin_sdk.py`).
KNOWN_PROFILES: frozenset[str] = frozenset(
    {"balanced", "architect", "delivery", "product", "incident"}
)
KNOWN_INTENTS: frozenset[str] = frozenset(
    {"architecture", "delivery", "product", "incident", "comms"}
)

# Plugin ids match the host registry shape: lowercase ASCII starting with
# a letter, underscore-separated, ≤ 32 chars. The regex is the source of
# truth — anything else is a manifest error.
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
# Loose semver-ish: MAJOR.MINOR.PATCH with optional `-pre.N`. Catches
# obvious typos, not a full semver parser. Matches connector_sdk.
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")


# ────────────────────────── Manifest model ──────────────────────────


@dataclass(frozen=True)
class PluginManifest:
    """Static description of one meeting-intel plugin pack."""

    id: str
    label: str
    version: str
    kind: str
    required_capabilities: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    execution_mode: str = "inline"
    # Chain hints — which profile base-chains and which intents the plugin
    # wants to fire on. Declarative metadata: the discovery loader registers
    # the plugin on the host so it can execute by id; wiring these hints into
    # the live router/dispatch chain is HS-35-03 (per-project enable/disable
    # at dispatch). The 14 built-ins keep their hardcoded routing unchanged.
    profiles: tuple[str, ...] = field(default_factory=tuple)
    intents: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "version": self.version,
            "kind": self.kind,
            "required_capabilities": list(self.required_capabilities),
            "description": self.description,
            "execution_mode": self.execution_mode,
            "profiles": list(self.profiles),
            "intents": list(self.intents),
        }


@dataclass(frozen=True)
class ManifestError:
    """One actionable error from manifest validation.

    `field` names the field that failed; `code` is a stable short string
    the SDK consumer can switch on; `message` is the human-readable
    explanation.
    """

    field: str
    code: str
    message: str

    def __str__(self) -> str:  # for assertion messages
        return f"{self.field}: {self.code} — {self.message}"


class PluginManifestError(ValueError):
    """Raised by `validate_manifest` when one or more rules fail.

    The list of underlying errors is on `.errors`. The exception's string
    form is the joined error list, so a bare `raise` already surfaces every
    problem at once.
    """

    def __init__(self, errors: list[ManifestError]) -> None:
        self.errors = errors
        super().__init__("\n".join(str(e) for e in errors) or "manifest invalid")


# ───────────────────────────── Validation ───────────────────────────


def _require_string(
    raw: Mapping[str, Any], field_name: str, errors: list[ManifestError]
) -> Optional[str]:
    value = raw.get(field_name)
    if not isinstance(value, str) or not value.strip():
        errors.append(
            ManifestError(
                field=field_name,
                code="required_string",
                message=f"`{field_name}` must be a non-empty string",
            )
        )
        return None
    return value.strip()


def _validate_string_list(
    raw: Any,
    *,
    field_name: str,
    allowed: frozenset[str],
    unknown_code: str,
    errors: list[ManifestError],
) -> tuple[str, ...]:
    """Validate an optional list of strings constrained to `allowed`.

    A non-list is a hard error; unknown members are collected into one
    `unknown_code` error and dropped. Returns the surviving members.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        errors.append(
            ManifestError(
                field_name,
                "must_be_list",
                f"{field_name}, when present, must be a list of strings",
            )
        )
        return ()
    members = [str(item).strip().lower() for item in raw if str(item).strip()]
    bad = sorted({m for m in members if m not in allowed})
    if bad:
        errors.append(
            ManifestError(
                field_name,
                unknown_code,
                f"{field_name} {bad} are not in {sorted(allowed)}",
            )
        )
    # Preserve order, drop unknowns + duplicates.
    out: list[str] = []
    for member in members:
        if member in allowed and member not in out:
            out.append(member)
    return tuple(out)


def validate_manifest(raw: Mapping[str, Any]) -> PluginManifest:
    """Parse + validate a manifest dict and return a `PluginManifest`.

    Raises `PluginManifestError` listing **every** problem found, not just
    the first, so plugin authors fix everything in one pass.
    """
    if not isinstance(raw, Mapping):
        raise PluginManifestError(
            [ManifestError("<root>", "must_be_object", "manifest must be a JSON object")]
        )

    errors: list[ManifestError] = []

    plugin_id = _require_string(raw, "id", errors)
    label = _require_string(raw, "label", errors)
    version = _require_string(raw, "version", errors)
    kind = _require_string(raw, "kind", errors)

    if plugin_id is not None and not _ID_RE.match(plugin_id):
        errors.append(
            ManifestError(
                "id",
                "id_format",
                "id must match ^[a-z][a-z0-9_]{0,31}$ (lowercase, "
                "underscores, ≤ 32 chars, starting with a letter)",
            )
        )

    if version is not None and not _VERSION_RE.match(version):
        errors.append(
            ManifestError(
                "version",
                "version_format",
                "version must look like MAJOR.MINOR.PATCH (with an "
                "optional `-pre` suffix)",
            )
        )

    if kind is not None and kind not in KNOWN_PLUGIN_KINDS:
        errors.append(
            ManifestError(
                "kind",
                "unknown_kind",
                f"kind must be one of {sorted(KNOWN_PLUGIN_KINDS)} "
                "(actuators are deferred to a later phase)",
            )
        )

    required_capabilities = _validate_string_list(
        raw.get("required_capabilities"),
        field_name="required_capabilities",
        allowed=KNOWN_PLUGIN_CAPABILITIES,
        unknown_code="unknown_capability",
        errors=errors,
    )

    execution_mode_raw = raw.get("execution_mode", "inline")
    if not isinstance(execution_mode_raw, str) or (
        execution_mode_raw.strip().lower() not in KNOWN_EXECUTION_MODES
    ):
        errors.append(
            ManifestError(
                "execution_mode",
                "invalid_execution_mode",
                f"execution_mode must be one of {sorted(KNOWN_EXECUTION_MODES)}",
            )
        )
        execution_mode = "inline"
    else:
        execution_mode = execution_mode_raw.strip().lower()

    profiles = _validate_string_list(
        raw.get("profiles"),
        field_name="profiles",
        allowed=KNOWN_PROFILES,
        unknown_code="unknown_profile",
        errors=errors,
    )
    intents = _validate_string_list(
        raw.get("intents"),
        field_name="intents",
        allowed=KNOWN_INTENTS,
        unknown_code="unknown_intent",
        errors=errors,
    )

    description = raw.get("description", "") or ""
    if not isinstance(description, str):
        errors.append(
            ManifestError(
                "description",
                "must_be_string",
                "description, when present, must be a string",
            )
        )
        description = ""

    if errors:
        raise PluginManifestError(errors)

    return PluginManifest(
        id=plugin_id or "",
        label=label or "",
        version=version or "",
        kind=kind or "",
        required_capabilities=required_capabilities,
        description=description.strip(),
        execution_mode=execution_mode,
        profiles=profiles,
        intents=intents,
    )


__all__ = [
    "KNOWN_PLUGIN_KINDS",
    "KNOWN_PLUGIN_CAPABILITIES",
    "KNOWN_EXECUTION_MODES",
    "KNOWN_PROFILES",
    "KNOWN_INTENTS",
    "PluginManifest",
    "ManifestError",
    "PluginManifestError",
    "validate_manifest",
]
