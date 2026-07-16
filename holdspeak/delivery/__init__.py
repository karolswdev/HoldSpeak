"""The Delivery Runtime foundation package (HS-94-02).

Phase 94's platform contract (PLATFORM-CONTRACT.md) turns the v1
"label -> one local path" project map into a versioned Delivery
Source registry, one single-flight collector per hub, and a coherent
`delivery_schema: 1` read model that clients poll without ever
causing a fresh dw/gh process. Raw paths and credentialed URLs stay
server-side; the wire carries labels and opaque IDs only (§12, §13).

- ``registry``   — Delivery Source + Worktree identity, persisted at
  ``~/.holdspeak/delivery_sources.json`` (``registry_schema: 1``),
  with a non-destructive one-time import of the v1 project map.
- ``collector``  — the single-flight, bounded, last-known-good
  collector over the vendored dw counterpart (§11).
- ``read_model`` — the coherent snapshot / cursor / revision wire
  shapes (§4.4) plus the redaction walk that keeps them honest.

The `/api/missioncontrol/*` compat surface stays on the legacy
bridge for now (the lower-risk option); `/api/delivery/*` runs
alongside it.
"""

from .collector import DeliveryCollector
from .registry import DeliveryRegistry, normalize_git_url

__all__ = [
    "DeliveryCollector",
    "DeliveryRegistry",
    "normalize_git_url",
]
