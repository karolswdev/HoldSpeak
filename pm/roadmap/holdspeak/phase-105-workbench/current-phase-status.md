# Phase 105 - Workbench

**Status:** IN PROGRESS (3/7, 2026-07-26). Chartered from the owner's
direct verdict on the desk's world layer: "I honestly want the Desk
OS to feel like an OS. Not a gimmick with huge lamp-like icons that
don't do shit and just make it look bad. Think Workbench 2.0 but on
steroids." Takes activation precedence over Phase 104 (Borrowed Fire
II), which is re-sequenced behind it — the innards land better on a
desk that already has the icon/state/Info grammar.

**Last updated:** 2026-07-26 (HS-105-04 shipped — see "Where we are").

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
| HS-105-01 | The icon system — handles, not mascots | done | [story-01-icon-system](./story-01-icon-system.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-105-02 | Drop-onto — composition by direct manipulation | backlog | [story-02-drop-onto](./story-02-drop-onto.md) | — |
| HS-105-03 | Zones are windows — density with chosen altitude | done | [story-03-zones-are-windows](./story-03-zones-are-windows.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-105-04 | Info on everything — the inspectable desk | done | [story-04-info-on-everything](./story-04-info-on-everything.md) | [evidence-story-04](./evidence-story-04.md) |
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

**2026-07-26 — HS-105-04 SHIPPED: Info on everything.** Right-click
anything (objects AND drawers) → ONE contract-derived Info card
(`infoContract.ts` declares, `InfoWindow` derives — no kind
hand-builds, guard-pinned): Identity with the name editing IN PLACE
through the real update paths (the world icon re-labels live),
honest Footprint measures (null = absence, never zero), Filed chips
opening zone windows, Lineage openable. Properties = tooltypes at
their honest v1: the vocabulary is pinned to exactly
`recipe.runs_on` (the recipe PUT's profile_id) and round-trip-proven
against the wire (select "LAN llama" → GET shows the profile_id).
Receipts deliberately absent in v1 (no per-object route; the kernel
journal is its future feed) per the gate's constraint. Cards coexist
as real desk windows. Guards: infoContract.test.ts; suite 332/332.
Next: HS-105-02 (drop-onto).

**2026-07-26 — HS-105-03 SHIPPED: drawers OPEN.** First, the owner
caught the shipped 01 claiming drawers the glass didn't show (zones
rendered as tray panels outside the sprite system) — fixed as an 01
rider (PR #370): a zone IS a drawer icon in the uniform cell, count
badge live, `drawer_sel` lighting on drop-ready, the tray + its
"drop things here" prose deleted. Then the open grammar: double-click
a drawer → a REAL desk window (ZoneWindow on DeskWindowFrame) flying
from the gesture point — desk visible, several coexisting, dock chips
free via the panel system; Icons view (the cell contract) and List
view (Name/Kind/Modified, sortable, hover Take-out un-files); THE
WINDOW REMEMBERS (view+sort per zone `hs.desk.zone-views`, the open
set `hs.desk.zone-windows`, rect via panels) and RESTORES across
reload — proven live 4-beat walk, shots read. Dive retired to the
Focus menu verb. The walk caught a real crash (fresh-object zustand
selector looping React) — fixed at cause. Guards: zoneWindow.test.tsx;
suite 328/328. Remainder recorded: Clean up/Snapshot + free
arrangement (need drag-reorder), drag-between-windows. Next per the
root-cause order: HS-105-04 (Info/tooltypes — properties on
everything).

**2026-07-25 — HS-105-01 SHIPPED (the same evening it was gated).**
The mush had a root: 64×64 pixel sources rendered at a FRACTIONAL
1.375× upscale, at illustration scale, stateless. Now: one uniform
cell (64px art 1:1, 80px selection box), REAL state images on disk
for all 68 sprites (`gen-sprite-states.py`: _sel brighten+rim,
_stale desaturate; sel > stale > rest picked in the scene), the
selected label inverting onto an accent chip, selection as the CELL
box, a drawer for directories (was "paper"), live badges only from
named routes (member counts, 48h freshness — the adapters now keep
`last_modified` — needs-you, coder-stale), and integer-true motion
(tilt/scale jitter dead). The density walk caught two defects live
and both were fixed at cause: random-jitter default homes stacked
cells (→ deterministic clean grid, the Workbench Clean Up rule), and
a 104px cell cannot grid 33 objects at 393px (→ an unset view choice
leads with the LIST above 16 objects on compact; explicit choice
always wins). Guard: `iconCell.test.ts` (7 pins); law:
`web/ICON-DISCIPLINE.md`. Final shots read at both viewports; web
chain green (tsc, 325/325, build, tokens gate). Next per the owner's
root-cause order: HS-105-03 (zones are windows).

**2026-07-25 — activated; HS-105-01 gated and building.** Phase 103
closed the same day; the pointer moved here. HS-105-01's mockup gate
ran per the AGENT_BRIEF §2 method (real Pixellab dual-state art, the
cell contract, the audited badge map, both form factors, own-eyes
critique). The owner's verdict, verbatim: **"Gimmick comes from some
of the art, but really from the fact that there's no real idea of
directories, properties of them, and so on, and so forth, but also
because of arts. I accept."** Two consequences recorded: (1) the
build proceeds as mocked plus the two gate findings (distinct
silhouette per kind — color alone is soup at density; badges anchor
to art bounds at rest, box bounds when selected); (2) the owner's
diagnosis names directories + properties as the gimmick's ROOT, so
the story order within the phase becomes 01 → 03 (zones are
windows) → 04 (Info/tooltypes) → 02 (drop-onto) → 05 (menu bar) —
the two root-cause stories run before composition and menus.

**2026-07-25 — scaffolded.** The Workbench 2.0 thesis recorded;
seven implementation-grade stories drafted.
