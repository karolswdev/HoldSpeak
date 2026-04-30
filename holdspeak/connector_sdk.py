"""Connector manifest + SDK shape for the local connector ecosystem.

HS-11-01. Phase 9 shipped three first-party connectors as ad-hoc
Python modules (`activity_github`, `activity_jira`,
`activity_candidates`) plus an extension-events ingester. Phase 11
generalizes them.

A connector pack is anything that:

  - Declares a `ConnectorManifest` describing what it is, what it
    can produce, and what permissions it needs.
  - Implements (some subset of) the four SDK Protocols:
    `Discover`, `Preview`, `Enrich`, `Clear`.
  - Plays nicely with the existing tables (`activity_records`,
    `activity_annotations`, `activity_meeting_candidates`) and the
    shared dry-run harness from HS-9-13.

This module is the contract. It deliberately ships no remote
distribution mechanism and no third-party package loading — the
phase-11 scope is reusable shape, not a marketplace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Protocol, runtime_checkable

# ──────────────────────────── Constants ─────────────────────────────

KNOWN_KINDS: frozenset[str] = frozenset(
    {
        "cli_enrichment",      # gh, jira: read-only CLI calls
        "candidate_inference", # calendar_activity: derives candidates from records
        "extension_events",    # firefox_ext: loopback POST from a browser extension
        "history_import",      # browser-history readers (Safari/Firefox/Chrome)
    }
)

KNOWN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "records",      # produces activity_records rows
        "annotations",  # produces activity_annotations rows
        "candidates",   # produces activity_meeting_candidates rows
        "commands",     # exposes a planned-command preview (dry-run)
    }
)

# Recognized permission strings. The model is intentionally
# coarse-grained; future stories can refine it. The point of this
# round is to make permissions *visible*, not to ACL every call.
KNOWN_PERMISSIONS: frozenset[str] = frozenset(
    {
        "read:activity_records",
        "write:activity_records",
        "write:activity_annotations",
        "write:activity_meeting_candidates",
        "shell:exec",         # invoke a local CLI binary (bounded by requires_cli)
        "fs:read",            # read files outside HoldSpeak's own data dir
        "loopback:http",      # accept loopback POSTs (extension events)
        "network:outbound",   # open *any* outbound socket — high-trust
    }
)

NETWORK_PERMISSIONS: frozenset[str] = frozenset({"network:outbound", "loopback:http"})

# Connector ids match the existing registry shape: lowercase ASCII
# starting with a letter, underscore-separated, max 32 chars. The
# regex is the source of truth — anything else is a manifest error.
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
# Loose semver-ish: MAJOR.MINOR.PATCH with optional `-pre.N`. The
# point is to catch obvious typos, not to be a full semver parser.
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")


# ────────────────────────── Manifest model ──────────────────────────


@dataclass(frozen=True)
class ConnectorManifest:
    """Static description of one connector pack."""

    id: str
    label: str
    version: str
    kind: str
    capabilities: tuple[str, ...]
    description: str = ""
    requires_cli: Optional[str] = None
    requires_network: bool = False
    permissions: tuple[str, ...] = field(default_factory=tuple)
    source_boundary: str = ""
    dry_run: bool = True

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "version": self.version,
            "kind": self.kind,
            "capabilities": list(self.capabilities),
            "description": self.description,
            "requires_cli": self.requires_cli,
            "requires_network": self.requires_network,
            "permissions": list(self.permissions),
            "source_boundary": self.source_boundary,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True)
class ManifestError:
    """One actionable error from manifest validation.

    `field` names the field that failed; `code` is a stable short
    string the SDK consumer can switch on; `message` is the
    human-readable explanation.
    """

    field: str
    code: str
    message: str

    def __str__(self) -> str:  # for assertion messages
        return f"{self.field}: {self.code} — {self.message}"


class ConnectorManifestError(ValueError):
    """Raised by `validate_manifest` when one or more rules fail.

    The list of underlying errors is on `.errors`. The exception's
    string form is the joined error list, so a bare `raise` already
    surfaces every problem at once.
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


def validate_manifest(raw: Mapping[str, Any]) -> ConnectorManifest:
    """Parse + validate a manifest dict and return a `ConnectorManifest`.

    Raises `ConnectorManifestError` listing every problem found,
    not just the first. The intent is to fail fast at install time
    with a complete report, so connector authors fix everything in
    one pass.
    """
    if not isinstance(raw, Mapping):
        raise ConnectorManifestError(
            [ManifestError("<root>", "must_be_object", "manifest must be a JSON object")]
        )

    errors: list[ManifestError] = []

    connector_id = _require_string(raw, "id", errors)
    label = _require_string(raw, "label", errors)
    version = _require_string(raw, "version", errors)
    kind = _require_string(raw, "kind", errors)

    if connector_id is not None and not _ID_RE.match(connector_id):
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

    if kind is not None and kind not in KNOWN_KINDS:
        errors.append(
            ManifestError(
                "kind",
                "unknown_kind",
                f"kind must be one of {sorted(KNOWN_KINDS)}",
            )
        )

    capabilities_raw = raw.get("capabilities", [])
    if not isinstance(capabilities_raw, list) or not capabilities_raw:
        errors.append(
            ManifestError(
                "capabilities",
                "required_list",
                "capabilities must be a non-empty list of strings",
            )
        )
        capabilities: tuple[str, ...] = ()
    else:
        bad = [c for c in capabilities_raw if c not in KNOWN_CAPABILITIES]
        if bad:
            errors.append(
                ManifestError(
                    "capabilities",
                    "unknown_capability",
                    f"capabilities {sorted(set(bad))} are not in "
                    f"{sorted(KNOWN_CAPABILITIES)}",
                )
            )
        capabilities = tuple(c for c in capabilities_raw if c in KNOWN_CAPABILITIES)

    requires_cli = raw.get("requires_cli")
    if requires_cli is not None and not (
        isinstance(requires_cli, str) and requires_cli.strip()
    ):
        errors.append(
            ManifestError(
                "requires_cli",
                "must_be_string_or_null",
                "requires_cli, when present, must be a non-empty string "
                "(the CLI binary name)",
            )
        )
        requires_cli = None
    elif isinstance(requires_cli, str):
        requires_cli = requires_cli.strip()

    if kind == "cli_enrichment" and not requires_cli:
        errors.append(
            ManifestError(
                "requires_cli",
                "required_for_cli_enrichment",
                "kind=cli_enrichment connectors must declare requires_cli "
                "(the binary they shell out to)",
            )
        )

    permissions_raw = raw.get("permissions", [])
    if not isinstance(permissions_raw, list):
        errors.append(
            ManifestError(
                "permissions",
                "must_be_list",
                "permissions must be a list of permission strings",
            )
        )
        permissions: tuple[str, ...] = ()
    else:
        unknown_perms = [p for p in permissions_raw if p not in KNOWN_PERMISSIONS]
        if unknown_perms:
            errors.append(
                ManifestError(
                    "permissions",
                    "unknown_permission",
                    f"permissions {sorted(set(unknown_perms))} are not in "
                    f"{sorted(KNOWN_PERMISSIONS)}",
                )
            )
        permissions = tuple(p for p in permissions_raw if p in KNOWN_PERMISSIONS)

    requires_network = bool(raw.get("requires_network", False))
    if requires_network and not (set(permissions) & NETWORK_PERMISSIONS):
        errors.append(
            ManifestError(
                "permissions",
                "network_permission_required",
                f"requires_network=true demands at least one of "
                f"{sorted(NETWORK_PERMISSIONS)} in permissions",
            )
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

    source_boundary = raw.get("source_boundary", "") or ""
    if not isinstance(source_boundary, str):
        errors.append(
            ManifestError(
                "source_boundary",
                "must_be_string",
                "source_boundary, when present, must be a string",
            )
        )
        source_boundary = ""

    dry_run_value = raw.get("dry_run", True)
    if not isinstance(dry_run_value, bool):
        errors.append(
            ManifestError(
                "dry_run",
                "must_be_bool",
                "dry_run, when present, must be a boolean (true/false)",
            )
        )
        dry_run = True
    else:
        dry_run = dry_run_value

    if errors:
        raise ConnectorManifestError(errors)

    return ConnectorManifest(
        id=connector_id or "",
        label=label or "",
        version=version or "",
        kind=kind or "",
        capabilities=capabilities,
        description=description.strip(),
        requires_cli=requires_cli,
        requires_network=requires_network,
        permissions=permissions,
        source_boundary=source_boundary.strip(),
        dry_run=dry_run,
    )


# ───────────────────────── SDK Protocols ────────────────────────────
#
# These are runtime-checkable Protocols rather than ABCs so a
# connector pack can implement only the subset that matches its
# manifest capabilities. The dry-run harness from HS-9-13 already
# uses a similar shape — phase-11 stories will adapt the harness
# to dispatch through these protocols instead of dispatching by
# id literal.

@runtime_checkable
class Discover(Protocol):
    """Optional: enumerate work entities the connector can act on."""

    def discover(self, db: Any, *, limit: int = 25) -> Iterable[Mapping[str, Any]]: ...


@runtime_checkable
class Preview(Protocol):
    """Mutation-free preview producing the dry-run payload shape.

    Returns a mapping that round-trips through
    `ConnectorDryRunResult` (see `holdspeak/activity_connector_preview.py`).
    """

    def preview(
        self,
        db: Any,
        *,
        limit: int = 25,
    ) -> Mapping[str, Any]: ...


@runtime_checkable
class Enrich(Protocol):
    """Imports / enriches local rows. May write to the DB.

    The runtime ensures the connector is `enabled=True` before
    calling `enrich`, and updates `last_run_at` / `last_error` from
    the returned status afterwards. The connector itself does not
    own enablement.
    """

    def enrich(
        self,
        db: Any,
        *,
        limit: int = 25,
    ) -> Mapping[str, Any]: ...


@runtime_checkable
class Clear(Protocol):
    """Per-capability output deletion (annotations / candidates).

    Each call clears exactly the rows authored by this connector
    via `source_connector_id = self.manifest.id`. Connectors
    delegating to `db.delete_activity_annotations(...)` /
    `db.delete_activity_meeting_candidates(...)` get this for free.
    """

    def clear(self, db: Any, *, capability: str) -> int: ...
