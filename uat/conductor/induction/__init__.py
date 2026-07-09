"""The induction engine: decks, seed manifests, and idempotent state recipes.

A UAT scenario is only meaningful if it starts from a *described* world,
and only repeatable if that world can be induced identically on demand.
This package makes those worlds named, idempotent, self-verifying verbs of
the conductor:

- **Decks** (`decks.py`) — named sparse config overlays the run boots with.
- **Seed manifests** (`seeds.py`) — desk/context state applied through the
  product's own public routes, so a seeded object is indistinguishable
  from a user-made one.
- **Probes** (`probes.py`) — assertions read back through product ``GET``
  routes; a recipe that cannot verify itself fails loudly.
- **Nodes** (`nodes.py`) — local ``holdspeak mesh serve`` workers, spawned
  and killed as their own process groups.
- **Recipes** (`recipes.py`) — the composition layer: deck + seeds +
  actions, closed by a verify probe, idempotent by contract.

Everything here drives the product over HTTP or as a subprocess — it never
imports the ``holdspeak`` package (the conductor's subprocess boundary).
"""

from __future__ import annotations
