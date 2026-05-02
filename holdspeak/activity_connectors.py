"""Pack-derived registry of activity connectors known to the runtime.

HS-13-01 + HS-13-04. The runtime registry now derives from
both first-party packs (`connector_packs.ALL_PACKS`) and any
user packs discovered under `~/.holdspeak/connector_packs/`
via `connector_pack_loader.build_registry`. The descriptor
surface is unchanged for downstream consumers; only the source
field on `ConnectorDescriptor` and the new
`reload_registry()`/`discovery_errors()` helpers are new.

`ConnectorDescriptor` carries:

  - `id`, `label`, `kind`, `capabilities`, `requires_cli`,
    `description` — sourced from the manifest.
  - `source` — `"first-party"` or `"user"` so the API + doctor
    can label each connector by provenance.
  - `manifest` — the underlying `ConnectorManifest`.
  - `cli_status()` — dispatches by id (gh / jira only).

The descriptor's `capabilities` is the manifest's
`capabilities` filtered to row-producing capabilities so the
manifest's `commands` / pure-preview capabilities don't leak
into API consumers expecting a row-shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .activity_github import CONNECTOR_ID as GH_CONNECTOR_ID, github_cli_status
from .activity_jira import CONNECTOR_ID as JIRA_CONNECTOR_ID, jira_cli_status
from .connector_pack_loader import (
    DiscoveryResult,
    RegisteredPack,
    build_registry,
)
from .connector_sdk import ConnectorManifest

_ROW_CAPABILITIES: frozenset[str] = frozenset({"records", "annotations", "candidates"})

ENRICHMENT_KINDS: frozenset[str] = frozenset(
    {"cli_enrichment", "candidate_inference"}
)


@dataclass(frozen=True)
class ConnectorDescriptor:
    """Runtime view of one pack-registered connector."""

    id: str
    label: str
    kind: str
    capabilities: tuple[str, ...]
    requires_cli: Optional[str]
    description: str
    source: str
    manifest: ConnectorManifest

    def cli_status(self) -> Optional[dict]:
        if self.id == GH_CONNECTOR_ID:
            return github_cli_status()
        if self.id == JIRA_CONNECTOR_ID:
            return jira_cli_status()
        return None


def _descriptor_from_pack(pack: RegisteredPack) -> ConnectorDescriptor:
    manifest = pack.manifest
    return ConnectorDescriptor(
        id=manifest.id,
        label=manifest.label,
        kind=manifest.kind,
        capabilities=tuple(c for c in manifest.capabilities if c in _ROW_CAPABILITIES),
        requires_cli=manifest.requires_cli,
        description=manifest.description,
        source=pack.source,
        manifest=manifest,
    )


# ───────────────────── Module-level registry state ────────────────────
#
# Populated at import time and refreshable via `reload_registry`.
# The web API + the dry-run harness + the fixture runner all
# read these globals; tests that exercise user-pack discovery
# call `reload_registry(user_packs_dir=tmp_path)` to swap them.

_DISCOVERY: DiscoveryResult = DiscoveryResult()
KNOWN_CONNECTORS: tuple[ConnectorDescriptor, ...] = ()
KNOWN_CONNECTOR_IDS: frozenset[str] = frozenset()


def _apply_discovery(result: DiscoveryResult) -> None:
    global _DISCOVERY, KNOWN_CONNECTORS, KNOWN_CONNECTOR_IDS
    _DISCOVERY = result
    KNOWN_CONNECTORS = tuple(_descriptor_from_pack(p) for p in result.packs)
    KNOWN_CONNECTOR_IDS = frozenset(c.id for c in KNOWN_CONNECTORS)


def reload_registry(
    user_packs_dir: Optional[Path] = None,
) -> DiscoveryResult:
    """Recompute the registry. Returns the resulting
    `DiscoveryResult` for callers that want to inspect errors.

    Tests use this to swap in a tmp_path-scoped user-pack dir.
    Production code calls it implicitly at module import; a
    runtime restart re-discovers any new files dropped into
    `~/.holdspeak/connector_packs/`.
    """
    result = build_registry(user_packs_dir=user_packs_dir)
    _apply_discovery(result)
    return result


def discovery_errors() -> tuple:
    """Return the discovery errors from the most recent registry
    load. Doctor + the API surface these so a malformed user
    pack is visible without grepping logs."""
    return _DISCOVERY.errors


def get_descriptor(connector_id: str) -> Optional[ConnectorDescriptor]:
    for descriptor in KNOWN_CONNECTORS:
        if descriptor.id == connector_id:
            return descriptor
    return None


def enrichment_descriptors() -> tuple[ConnectorDescriptor, ...]:
    """Subset of the registry that drives the activity-enrichment
    surface. Records-ingesters (firefox_ext) live in the registry
    but not on this surface."""
    return tuple(c for c in KNOWN_CONNECTORS if c.kind in ENRICHMENT_KINDS)


# Initial load at module-import time.
reload_registry()
