# HS-92-01 — The words HoldSpeak uses

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress (pre-close implementation; Phase 91 remains current)
- **Depends on:** HS-91-10
- **Unblocks:** HS-92-02, HS-92-03, HS-92-05, HS-92-06, HS-92-07
- **Owner:** unassigned

## Problem

Python, Web, Swift, sync, tests, and UAT each carry overlapping “canonical”
vocabularies. A saved Recipe is also an Agent, a live coding process is also an
Agent, a Profile can mean execution placement or routing, and Zone/Directory/KB
all look like grouping. Independent label edits would create another drift
cycle.

## Scope

- **In:** A versioned, machine-readable product-language registry under `docs/`;
  typed Python accessors under `holdspeak/`; generated or fixture-verified Web
  and Swift mappings; compatibility aliases for `recipe`, `profile`, `chain`,
  and `directory`; primary Desk labels updated to Persona, Zone, Knowledge,
  Workflow/Sequence, Coder session, Integration, and Runs on; a source census
  with intentional internal/SDK exceptions.
- **Out:** Renaming database tables or public wire keys; rewriting every
  historical document; introducing invocation/authority behavior owned by later
  stories.
- **Paths:** `docs/product-language.json` (proposed), `holdspeak/db/models.py`,
  `holdspeak/db/primitives.py`, `web/src/lib/primitives.ts`,
  `web/src/desk/components/`, `apple/Sources/Contracts/Primitives.swift`,
  `apple/Sources/Contracts/Sync.swift`,
  `apple/App/MeetingCapture/DeskPrimitive.swift`, contract fixtures, and the
  corresponding Python/Vitest/Swift tests.

## Acceptance criteria

- [x] One versioned registry defines canonical terms, lifecycle axes,
      destination classes, decision kinds, ControlMode values, and every legacy
      alias named in `adoption-convergence-map.md`.
- [x] Python, TypeScript, and Swift decode the same golden fixtures and reject an
      unknown canonical value without silently substituting a generic string.
- [x] `web/src/lib/primitives.ts`, Desk create/editor/pullout/rail labels,
      `apple/App/MeetingCapture/DeskPrimitive.swift`, and canonical native Desk
      menus use Persona for saved behavior and Coder session for live processes.
- [x] Product UI says Zone, Knowledge, Workflow/Sequence, Integration, and Runs
      on; compatibility adapters continue to accept existing `directory`, `kb`,
      `recipe`, `chain`, and `profile` wires.
- [x] The registry classifies Swift summary/actions/transcript/topics cards as
      Meeting projections rather than forcing Web/sync to invent peer resources.
- [x] A terminology census fails on new unqualified product uses of Profile,
      Agent, Action, Context, Target, Pending, or Local unless the path is an
      explicitly documented compatibility/SDK exception.
- [ ] The Desk still materializes, opens, edits, files, runs, and syncs every
      existing kind; this story is a language seam, not feature deletion.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_product_language.py tests/unit/test_primitive_contract.py tests/unit/test_db_primitives.py tests/unit/test_doc_drift_guard.py`; `cd web && npm run check`; `cd apple && swift test` with focused product-language fixtures.
- **Integration:** `uv run pytest -q tests/integration/test_primitive_framework_sync.py tests/integration/test_web_built_mount.py`; regenerate and diff `docs/API_SURFACE.md`/`docs/api-surface.json` only if routes change.
- **Manual / device:** On Web and the canonical Swift root, create/open a Persona,
  Coder session, Zone, Knowledge collection, and Workflow; verify identical
  meaning while the native presentation remains platform-specific.

## Notes / open questions

The product term is **Persona**. `recipe` remains the compatibility/API noun
until all sync clients migrate. A Chain is presented as an advanced linear
**Sequence** of a Workflow; do not promise full graph equivalence.

Implementation began on 2026-07-10 by direct owner instruction while the
Phase-91 owner/device evidence gate remains open. The registry, strict Python,
TypeScript, and Swift adapters, fixture parity, compatibility aliases, primary
Web/native labels, Meeting-projection classification, package inclusion, and
terminology census are implemented. Automated proof is green: 57 focused
Python tests, 112 Web tests plus typecheck/build/architecture guard, 521 Swift
tests with 9 expected skips, and the generated iOS simulator app build. The
last acceptance item remains open until the cross-client manual Desk walk is
performed; no physical-device result is inferred from simulator compilation.
