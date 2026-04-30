"""Pack-derived registry of activity connectors known to the runtime.

HS-13-01. Phase 9 / 11 left the runtime reading from a
hand-written `KNOWN_CONNECTORS` tuple while the manifests under
`connector_packs/` sat alongside as documentation. This module
flips the source of truth: `KNOWN_CONNECTORS` is now derived
from `connector_packs.ALL_PACKS`, so adding or removing a pack
module is the only change required to register a connector with
the runtime.

`ConnectorDescriptor` is preserved as a thin wrapper over a
`ConnectorManifest` because every existing call site (the
`/api/activity/enrichment/connectors` endpoint, the
`activity_connector_preview.dry_run` harness, the fixture
runner) reads through this surface. The descriptor exposes:

  - `id`, `label`, `kind`, `capabilities`, `requires_cli`,
    `description` — all sourced from the underlying manifest.
  - `cli_status()` — dispatches to the pack's CLI status helper
    (currently `gh` and `jira` only). Packs that do not shell
    out return `None`.

The descriptor's `capabilities` is the manifest's `capabilities`
filtered down to *data-row* capabilities (annotations, candidates,
records). The pack manifests may declare additional capabilities
like "commands" (the dry-run command preview surface); those are
not row-producing and are intentionally excluded from the
descriptor that downstream consumers iterate over.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .activity_github import CONNECTOR_ID as GH_CONNECTOR_ID, github_cli_status
from .activity_jira import CONNECTOR_ID as JIRA_CONNECTOR_ID, jira_cli_status
from .connector_packs import ALL_PACKS
from .connector_sdk import ConnectorManifest

# Capabilities that produce rows in the local schema. The
# descriptor surfaces only these; non-row capabilities (e.g.
# "commands", which describes the dry-run preview surface) are
# filtered out so existing API + fixture consumers keep their
# stable shape.
_ROW_CAPABILITIES: frozenset[str] = frozenset({"records", "annotations", "candidates"})

# Connectors the activity-enrichment surface (the
# `/api/activity/enrichment/connectors` endpoint and its DB-backed
# enable/disable state) cares about. Records-ingesters like the
# Firefox companion live in the registry for completeness but are
# not enrichment-shaped — the API filters them out.
ENRICHMENT_KINDS: frozenset[str] = frozenset(
    {"cli_enrichment", "candidate_inference"}
)


@dataclass(frozen=True)
class ConnectorDescriptor:
    """Runtime view of one pack-registered connector.

    Built from a `ConnectorManifest` via
    `_descriptor_from_manifest`. The fields mirror what every
    pre-phase-13 call site already consumed; the underlying
    manifest is kept on the descriptor so callers needing the
    full manifest (permissions, version, source boundary) can
    reach it without a second lookup.
    """

    id: str
    label: str
    kind: str
    capabilities: tuple[str, ...]
    requires_cli: Optional[str]
    description: str
    manifest: ConnectorManifest

    def cli_status(self) -> Optional[dict]:
        if self.id == GH_CONNECTOR_ID:
            return github_cli_status()
        if self.id == JIRA_CONNECTOR_ID:
            return jira_cli_status()
        return None


def _descriptor_from_manifest(manifest: ConnectorManifest) -> ConnectorDescriptor:
    return ConnectorDescriptor(
        id=manifest.id,
        label=manifest.label,
        kind=manifest.kind,
        capabilities=tuple(c for c in manifest.capabilities if c in _ROW_CAPABILITIES),
        requires_cli=manifest.requires_cli,
        description=manifest.description,
        manifest=manifest,
    )


KNOWN_CONNECTORS: tuple[ConnectorDescriptor, ...] = tuple(
    _descriptor_from_manifest(pack.MANIFEST) for pack in ALL_PACKS
)

KNOWN_CONNECTOR_IDS: frozenset[str] = frozenset(c.id for c in KNOWN_CONNECTORS)


def get_descriptor(connector_id: str) -> Optional[ConnectorDescriptor]:
    for descriptor in KNOWN_CONNECTORS:
        if descriptor.id == connector_id:
            return descriptor
    return None


def enrichment_descriptors() -> tuple[ConnectorDescriptor, ...]:
    """Subset of the registry that drives the activity-enrichment surface.

    The browser's Connectors panel and the
    `/api/activity/enrichment/connectors` endpoint care about
    connectors that *enrich* an existing ledger (cli_enrichment,
    candidate_inference). Records-ingesters such as the Firefox
    companion are part of the registry but live behind a
    different ingestion surface; this helper filters them out so
    the enrichment surface stays focused.
    """
    return tuple(c for c in KNOWN_CONNECTORS if c.kind in ENRICHMENT_KINDS)
