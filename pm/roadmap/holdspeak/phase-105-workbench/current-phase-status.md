# Phase 105 - Workbench

**Status:** SCAFFOLDED (0/7, 2026-07-25). Chartered from the owner's
direct verdict on the desk's world layer: "I honestly want the Desk
OS to feel like an OS. Not a gimmick with huge lamp-like icons that
don't do shit and just make it look bad. Think Workbench 2.0 but on
steroids." Takes activation precedence over Phase 104 (Borrowed Fire
II), which is re-sequenced behind it — the innards land better on a
desk that already has the icon/state/Info grammar.

**Last updated:** 2026-07-25 (scaffolded; no story started).

## Why this phase exists

The desk currently speaks two languages at war. Phase 99 gave the
chrome a real OS skin (studied bars, mechanical controls, drawn
scrollbars); the world layer underneath remained a game diorama —
large illustrative sprites floating in empty space. An OS whose
windows are serious and whose desktop is a diorama reads as a
costume, and the owner called it: the world's objects are mascots,
not icons. A mascot's entire informational payload is "I exist." An
icon is a live handle for an object with visible state, uniform
verbs, and composition under direct manipulation.

Amiga Workbench 2.0 is the named reference because it is the purest
proof of the principles this phase installs, achieved under absurd
constraints: objects carry state at rest; one verb set answered
uniformly by everything; composition by drag-and-drop; density with
chosen altitude (icon/name/date views); everything inspectable
(Information on any icon); small, disciplined, dual-state icons; and
real menus that admit everything the system can do. "On steroids" is
what 1991 could not do and this codebase already can: live receipts
as icon state, windows that stream, voice as a verb on every object,
and agents as visible processes.

## Constitutional grounding

- **Article I (The Desk is the operating surface):** this phase IS
  Article I's enforcement pass — the world layer stops decorating
  and starts operating. Snapshot semantics extend the
  sacred-arrangement clause to icon positions inside zone windows.
- **Article II (Everything is a primitive):** the verb contract
  (open/info/rename/snapshot/drag/drop-onto/select) and the
  drop-target matrix are declared per primitive kind in the
  contract, UI derived — never per-surface special cases.
- **Article VII (The interface serves, it does not speak):** state
  badges replace prose; a count, a freshness tick, an armed ring —
  never a sentence.
- **Article VIII (Native-grade craft):** dual-state icons, palette
  discipline, latency budgets on every new interaction.
- **Article IX (Proof over claim):** hands-first sitting loop in the
  Phase-101 round-9 method; headed walks, both viewports, positions
  sampled over time, every screenshot read.

## Goal

Every object on the desk is a working icon: it shows its state at
rest, answers the full uniform verb set, composes by drag-onto,
opens into density the user chooses, and can be inspected to the
atom — under one visual discipline that matches the chrome. The
desk stops being a place where objects are displayed and becomes a
bench where they are used.

## Scope

- In: the seven stories below; the world/GL layer
  (`web/src/desk/gl/`), the primitive contract, the icon asset
  pipeline, zone windows, the Info surface, the menu bar, and their
  evidence.
- Out: ALL iPad/HSM work (the standing web-desk-is-the-spec
  direction; contracts and the spec ledger are the Swift-facing
  artifacts); new primitive KINDS (this phase deepens what exists);
  the Phase-104 stories (re-sequenced behind, untouched); any
  redesign of window chrome itself (Phase 97/98/99 canon stands —
  this phase brings the world UP to the chrome's standard).

## Exit criteria (evidence required)

- [ ] HS-105-01 through HS-105-05 shipped with evidence, each proven
      by a headed hands-first walk at 1440 + 393 (and a touch
      context where pointer grammar changed).
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (pre-existing unrelated failures documented per-story).
- [ ] `cd web && npx tsc --noEmit -p . && npx vitest run && npm run
      build && npm run tokens:gate` green.
- [ ] Voice/vocabulary guards green on every new surface string
      (state badges are counts and marks, never prose).
- [ ] HS-105-06 docs shipped touching the entry points.
- [ ] HS-105-07 closeout: the sitting loop run to the owner's
      verdict per Article IX.4, and the spec ledger recorded (which
      atoms are contract-specified vs TypeScript-only).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-105-01 | The icon system — handles, not mascots | backlog | [story-01-icon-system](./story-01-icon-system.md) | — |
| HS-105-02 | Drop-onto — composition by direct manipulation | backlog | [story-02-drop-onto](./story-02-drop-onto.md) | — |
| HS-105-03 | Zones are windows — density with chosen altitude | backlog | [story-03-zones-are-windows](./story-03-zones-are-windows.md) | — |
| HS-105-04 | Info on everything — the inspectable desk | backlog | [story-04-info-on-everything](./story-04-info-on-everything.md) | — |
| HS-105-05 | The menu bar — the system admits what it can do | backlog | [story-05-menu-bar](./story-05-menu-bar.md) | — |
| HS-105-06 | Docs — the bench at the entry points | backlog | [story-06-docs](./story-06-docs.md) | — |
| HS-105-07 | Closeout — the sitting loop and the spec ledger | backlog | [story-07-closeout](./story-07-closeout.md) | — |

## Sequencing

Phase 103 closes first (the pending second sitting). Then this
phase. Phase 104 (Borrowed Fire II) activates after this phase
closes; its charter records the same order. If a 104 story becomes
urgent (the owner's call alone), it rebases onto the shipped icon
grammar rather than the diorama.

## Decisions deferred (parked, not committed)

- **Pull-down screens / workspaces** (the Workbench screens
  metaphor): multiple desks, front/back. Real OS material, but a
  world-model change; not before the single desk is atomic.
- **Icon editor on glass** (the user redrawing an object's icon in
  place): delightful, Article-IV-friendly via Pixellab, but craft
  dessert — after the meal.
- **The process window** (steered sessions/gate proposals/attempts
  as one "what is running" surface): deliberately left for Phase
  104, which supplies its data spine.

## Where we are

**2026-07-25 — scaffolded.** The owner's verdict and the Workbench
2.0 thesis recorded; seven implementation-grade stories drafted.
Nothing started; activation follows the Phase 103 close.
