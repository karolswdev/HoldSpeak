"""First-party meeting-intel plugin packs.

HS-35-02. The 14 built-in plugins stay hardcoded in
`holdspeak/plugins/builtin/` (behavior-preserving — their registration +
routing are unchanged). This package is the first-party slot for
*pack-shipped* plugins, discovered through the same loader as local user
packs (`holdspeak/plugin_pack_loader.py`).

Each pack module exports:

  - `MANIFEST` — a `PluginManifest` (see `holdspeak.plugin_sdk`).
  - `create_plugin()` — a zero-arg factory returning a `HostPlugin`
    instance whose `.id` matches `MANIFEST.id`.

`ALL_PACKS` is the tuple of first-party pack modules in canonical order.
It is **empty today**: the mechanism exists so plugins can ship outside
the built-in set without editing core, but the built-ins themselves are
not repackaged (the behavior-preserving default — see the phase status
doc's "Decisions deferred").
"""

from __future__ import annotations

ALL_PACKS: tuple = ()

__all__ = ["ALL_PACKS"]
