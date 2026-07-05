# Evidence — HSM-16-01 (the DeskObject parity & sync contract)

**Recorded done on the 2026-07-04 resume survey — pre-paid.**

The story's deliverable — a platform-neutral inventory + spec both thrusts are measured
against — exists as [`THE_PRIMITIVE_FRAMEWORK.md`](../contracts/THE_PRIMITIVE_FRAMEWORK.md),
authored 2026-06-26 on the owner's directive (*"nearly full parity… we are building a HUGE
framework"*) and kept current since:

- **The canonical primitive table** — 12 primitives with kind, sync class, and snake_case wire
  shape (meeting/artifact/note/directory/kb/recipe/chain/workflow/coder/model/connector/membership,
  plus the honest local-only `game` exception).
- **The sync classes** this phase's own design call demanded — content / organization /
  capability / presence / layout, with layout explicitly per-device and never canonical.
- **The per-surface parity inventory** (the legend table the story asked for), updated through
  wave 4 (`directory` promotion) and the Phase-17 owner-ratified recipe rename.
- **The hub + ports model** — desktop = canonical store, LWW by `last_modified`, tombstones on
  the wire; the wire coder mirrored from `apple/Sources/Contracts/Coding.swift`.

The spec is enforced, not aspirational: the Phase-23-04 round-trip matrix golden-pins the wire
shapes on both sides (`swift test` 437/8/0 at the Phase-23 closeout, 2026-07-04), and the hub
serves the shapes from `holdspeak/web/routes/primitives/` (fresh targeted run 2026-07-04:
`uv run pytest tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync.py
tests/unit/test_web_routes_sync_primitives.py tests/unit/test_db_primitives.py
tests/unit/test_primitive_contract.py` → **66 passed**).
