# Phase 121 — The Fluency

**Status:** chartered (0/12). (Record note 2026-08-15, HS-132-13: no
HS-121 commits exist — the phase never executed as chartered — but several
chartered deliverables later shipped through other phases (undo/copy
receipt hooks, LedgerFilter, SurfaceFooter canonized by Phase 129).
Re-scope against production before execution; the held items (frecency,
deep links, browser push, first-run philosophy) are harvested in the
Phase-132 audit.)

**Last updated:** 2026-08-06.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call. This follows the standing Opus->Terra->Orchestrator
pipeline.

## What we're building

Phase 120 made every surface look like one OS. Phase 121 makes it
feel like one — keyboard-fluent, feedback-honest, workflow-fast.

**Kit-first architecture.** The usability audit found the same five
gaps recurring across every surface: empty states can't guide, footers
are 8 species, search is 4 implementations, copy has no receipt, and
undo doesn't exist. Fixing these per-surface would produce 11 well-
built surfaces and guarantee the 12th reinvents everything. Instead:
story 01 builds the five missing kit primitives. Stories 02-11 are
adoption passes that wire existing surfaces into the kit. A new surface
built six months from now gets undo, copy, search, footer, and empty-
state guidance for free — because it composes from primitives, not
because someone remembered.

This is Article II taken to its conclusion: everything is a primitive,
UI is derived.

## The five kit primitives (story 01)

| Primitive | What it is | What composes from it |
|-----------|-----------|----------------------|
| `SurfaceState` action slot | `onAction` + `actionLabel` props → desk-chip button in empty states | 12+ empty states across workbench, directory, chain, notes, zones, commands, cadence |
| `SurfaceFooter` | Shared footer with fixed slots: `egress \| receipt \| verbs` | Every window and pullout footer (replaces 8 species) |
| `LedgerFilter` | `StringGadget` + mic + live-apply + Enter-opens-top-hit + persistence | Meetings, attention, agent picker, commands, palette results |
| `useCopyReceipt` | `copy(text)` → clipboard + transient "Copied" lamp in nearest footer | Ask answers, chat turns, pullout bodies, workbench results, journal |
| `useUndoReceipt` | `undo(label, fire, revert, window)` → receipt token with countdown | Delete, remove, clear-done, any future destructive verb |

## Why kit-first

1. **Leverage.** Five primitives (~300 lines) make 11 adoption stories
   trivial wiring. Without the kit, each story hand-rolls its own
   version and the next phase finds 11 new species.

2. **Correctness.** A copy receipt, an undo receipt, and a footer
   layout tested once in the kit are correct everywhere. Per-surface
   implementations drift.

3. **Discoverability.** When every footer has the same three slots,
   a user who learns one surface knows them all. When empty states
   always have an action button, "what do I do next?" is always
   answered.

4. **The DeskPrimitive contract.** Article II says everything is a
   primitive. The kit primitives ARE the contract for how surfaces
   compose. They're not utility functions — they're the OS's
   interaction vocabulary.

## Method

- **Kit first (story 01).** Build the five primitives with tests,
  no consumers yet. This is the foundation the rest stands on.
- **Footer adoption (story 02).** Migrate all 8 footer species + 10
  footerless programs to SurfaceFooter. This is the highest-leverage
  adoption pass — every surface gets undo/copy receipt slots for free.
- **Trust (stories 03-04).** Wire pullout dead ends and undo into the
  kit. The desk becomes safe.
- **Keyboard (stories 05-06).** ARIA patterns and window management.
  The desk becomes navigable.
- **Power (stories 07-08).** Verb registry and command center palette.
  The desk becomes a command center.
- **Craft (stories 09-11).** Live state, recovery, copy/export,
  attention. The desk becomes honest and complete.
- **The walk (story 12).** Keyboard-first proof.

## Dependency graph

```
01 the kit ──→ 02 one footer ──→ 03 doors open (uses SurfaceState action)
                              ──→ 04 safe hands (uses useUndoReceipt + SurfaceFooter)
                              ──→ 09 live desk truth (receipts in footer)
                              ──→ 10 recovery (SurfaceState + error retry)
                              ──→ 11 output leaves desk (useCopyReceipt)

05 keyboard complete ──┐
06 windowcraft       ──┤
07 universal verbs   ──┤  (04 safe hands → 07, delete needs undo)
08 command center    ──┤
09 live desk truth   ──┤
10 recovery          ──┤
11 output + attention──┤
                       └──→ 12 the walk
```

## What's held (needs owner ruling or architectural scope)

- **F20 escape consolidation:** 19 independent listeners.
  Architectural hardening, separate phase.
- **N-B3 lazy window mounting:** Performance architecture, not
  validated user pain yet.
- **Push notifications:** Badge semantics in scope; browser/OS push
  deferred pending owner notification policy.
- **Onboarding flow:** Blank desk may be intentional. Needs owner
  first-run philosophy.
- **Frecency:** Fuzzy match and object search first. Frecency needs
  privacy/persistence/decay policy.
- **Voice proposal dismissal timing:** Product feel decision for
  owner review.
- **Per-object deep links:** Needs identity/durability decisions.

## Stories

### The kit

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | The kit | Why do surfaces keep reinventing the same five patterns? | backlog |
| 02 | One footer | Why are there 8 footer species and 10 programs with none? | backlog |

### Trust

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 03 | The door must open | Why do 7 pullout kinds silently fail? | backlog |
| 04 | Safe hands | Why can destructive actions not be undone? | backlog |

### Keyboard

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 05 | Keyboard is a complete path | Why do some controls require a mouse? | backlog |
| 06 | Windowcraft | Why can't I snap, reverse-cycle, or find a Window menu? | backlog |

### Power

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 07 | Universal object verbs | Why can't I delete, rename, or duplicate from the palette? | backlog |
| 08 | The command center | Why doesn't the palette find objects and settings? | backlog |

### Craft

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 09 | Live desk truth | Why is a dead WebSocket invisible and workbench state unreliable? | backlog |
| 10 | Recovery is a first-class state | Why do errors strand me with no next step? | backlog |
| 11 | Output leaves the desk and attention confirms | Why can't I copy an Ask answer, and why is completion silent? | backlog |

### Proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 12 | The walk | Can a power user drive the desk without touching the mouse? | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-121-01 | The kit | backlog | [story-01](story-01-the-kit.md) | — |
| HS-121-02 | One footer | backlog | [story-02](story-02-one-footer.md) | — |
| HS-121-03 | The door must open | backlog | [story-03](story-03-the-door-must-open.md) | — |
| HS-121-04 | Safe hands | backlog | [story-04](story-04-safe-hands.md) | — |
| HS-121-05 | Keyboard is a complete path | backlog | [story-05](story-05-keyboard-is-a-complete-path.md) | — |
| HS-121-06 | Windowcraft | backlog | [story-06](story-06-windowcraft.md) | — |
| HS-121-07 | Universal object verbs | backlog | [story-07](story-07-universal-object-verbs.md) | — |
| HS-121-08 | The command center | backlog | [story-08](story-08-the-command-center.md) | — |
| HS-121-09 | Live desk truth | backlog | [story-09](story-09-live-desk-truth.md) | — |
| HS-121-10 | Recovery is a first-class state | backlog | [story-10](story-10-recovery-is-a-first-class-state.md) | — |
| HS-121-11 | Output leaves the desk and attention confirms | backlog | [story-11](story-11-output-leaves-the-desk-and-attention-confirms.md) | — |
| HS-121-12 | The walk | backlog | [story-12](story-12-the-walk.md) | — |

## Where we are

Chartered. Kit-first resequence complete. Four Opus scouts + Terra
weighting completed the usability audit. 12 stories scaffolded —
5 kit primitives in story 01, footer adoption in story 02, then 9
feature stories that compose from the kit, and the walk. Ready to
begin.
