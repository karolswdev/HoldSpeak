# Council voice — codex CLI (model gpt-5.6-sol, read-only over the tree, 2026-08-31)

> Solicited per the owner's ruling. The requested spelling `gpt-5-6-sol`
> was rejected by the account; the account default resolved to
> `gpt-5.6-sol`. 112,934 tokens; the agent explored the repo before
> answering. Final memo verbatim below.

# Direction memo — HoldSpeak component-library reform

## 1. Architecture: make `surface/` the published Desk material system

Promote web/src/desk/surface in place; do not create a competing
`components/lib/`. It is already the de facto system: Surface.tsx
explicitly declares itself "the ONE way," and supplies rows, sections,
states, splits, ledgers, libraries, settings, streams, and inline
editing. gadgets.tsx supplies the honest native-control grammar, while
roving.ts already encodes composite keyboard law.

Give it an explicit public boundary:

- `surface/index.ts`: the only supported feature import path.
- `surface/primitives/`: layout/material atoms.
- `surface/controls/`: gadgets and reusable input behavior.
- `surface/patterns/`: choice cards, plans, status, disclosures, provenance, receipts.
- `surface/graph/`: topology viewport, nodes, flows, and interaction behavior.
- `surface/contract.md`: states, accessibility, container behavior, allowed tokens, motion, and examples.

Keep compatibility re-exports so this is organization, not a flag-day
move. Remove dependency inversion: `surface` currently imports
`MicButton` from the flat feature directory; reusable controls should
move inward, while `CallChip` remains a thread composition built from a
generic library `StateChip`.

Move feature implementations opportunistically into
`desk/features/<feature>/`, with CSS beside the owning component.
Shell/compositor furniture belongs under `desk/chrome/`. The 1,229-line
thread-pullout.css is the clearest evidence that feature CSS needs
ownership boundaries, not another global sheet.

There is already one token source: design-tokens.json generates
styles/tokens.css. desk-tokens.css is only a six-line import shim;
retire it after import census. Preserve the generated file's
primitive/semantic/component layers rather than creating separate token
files.

**Rejected counterargument:** a fresh `components/lib/` would look
cleaner. It would instead create two centers of gravity and spend
migration energy on paths rather than contracts.

## 2. Delight layer: standardize consequential behavior, not decoration

The first library patterns should be:

1. **`ChoiceCardGroup`** — real radio semantics, roving focus,
   selected/recommended/disabled states, summary, line-item facts,
   cost/size slot, and a separate confirmation verb. A card is
   inspectable before selection and never a clickable `<div>`.
2. **`ProgressPlan`** — stable step IDs; `queued | running | done |
   failed`; optional byte progress/rate; receipt and egress slots; one
   resume/retry action; transition-only `aria-live`; compact and
   detailed presentations from the same model.
3. **`StateChip` + `ActionNotice`** — a closed vocabulary such as
   `idle | active | working | success | warning | failure |
   unreachable`, always icon plus text, never color alone.
   `ActionNotice` permits at most one named next action. `CallChip`'s
   locally styled OFF/LISTENING/THINKING/SPEAKING grammar demonstrates
   the need.
4. **`ProvenanceChip` and `Receipt`** — typed source/boundary labels,
   optional destination and data scope, timestamp/status, and an
   inspect action. They should compose into SurfaceFooter, whose
   egress/receipt/verb law is already sound.
5. **`Disclosure` / `InFlowPanel`** — controlled or uncontrolled open
   state, RAW/Advanced variants, focus return, Escape behavior,
   optional persistence key, and content that pushes layout rather than
   opening a modal. Replace thread-specific RAW folds and repeated
   advanced editors.
6. **`TopologySurface`** — DOM nodes over an SVG edge layer; bounded
   pan; home-node designation; bundled labeled flows; roving selection;
   keyboard pan/select/re-point; inspector and add-node slots;
   reduced-motion support. It owns presentation and interaction only —
   service callbacks remain with the feature.

Roving focus must be inside these composites, following the precedent
already documented in `roving.ts`, never reimplemented by consumers.

**Rejected counterargument:** extract only after a second identical use
appears. The repeated chips, folds, receipts, and mode controls show
that waiting has already externalized the cost into inconsistent
behavior and CSS.

## 3. Reform without a rewrite: use a ratchet fence

Extend guard-architecture.mjs with a checked-in baseline of legacy
violations. The gate should reject:

- New feature imports from private `surface/*` files instead of `surface/index.ts`.
- New raw `.desk-chip` or status-tone markup outside the library.
- New feature CSS defining library-owned states, receipts, plans, disclosures, or roving composites.
- New raw colors, z-indexes, or durations — the existing validate-tokens.cjs already handles this portion.
- New library components that call feature APIs or stores directly.

Existing offenders remain listed and cannot increase. A touched feature
adopts library patterns when it changes that behavior; unrelated
mega-components are left alone. Contract tests live with the library;
feature tests assert meaning and service wiring, not copied markup.

**Rejected counterargument:** migrate all 40-plus flat components
before shipping anything else. That is a rewrite disguised as cleanup
and would delay the front door without improving its first
implementation.

## 4. Visual gates: require human verdicts at three meaningful boundaries

A human-looked-at artifact becomes mandatory when:

1. A library component or variant is introduced or materially changed.
2. A UI story reaches acceptance.
3. A phase/release closes with an altered user journey.

Logic-only changes do not require shots. Reuse shoot.mjs and the
established Glass walks, but make scenarios deterministic and named
rather than only timestamped and gitignored.

Each gate produces a compact shot sheet: component/story, commit, seed,
1440 and 393 views, relevant states, before/after where applicable,
keyboard-focus capture, reviewer/date, verdict, and brief annotations
for intentional differences. CI captures and flags missing states or
gross pixel drift; a person approves hierarchy, legibility, overflow,
and delight. Store the manifest and review Markdown with phase
evidence; keep full PNGs in the existing phase `assets/` convention.

Cheapness comes from capturing only changed scenarios, using the
`/design/components` gallery for library gates, and reviewing one
contact sheet rather than browsing folders.

**Rejected counterargument:** screenshot every PR and gate on pixel
equality. That creates review fatigue and false failures from fonts,
animation, and rendering while still failing to judge whether the
interface makes sense.

## 5. Phase 156: make the reform a prerequisite of stories 03 and 05

Before story 03 (the door surface), the library must ship
`ChoiceCardGroup`, `ProgressPlan`, `StateChip`, `ActionNotice`,
`Disclosure`, `ProvenanceChip`, and `Receipt`, with contract tests and
gallery states at 1440/393. The pack card then supplies domain data; it
does not invent furniture. The apply plan consumes the durable states
already specified by story 02. The health strip is an `ActionNotice`,
not a new Models-only banner.

Before story 05 (the topology), ship the `TopologySurface` harness with
fake nodes/flows, pan containment, bundled edges, keyboard operation,
inspector slots, and visual approval. Be honest about lineage: the
current web has graph.ts, a wire-model builder, but no reusable graph
UI; the DOM-plus-SVG approach exists as design lineage in phase 68's
technical design, not production code to copy.

**Rejected counterargument:** let Phase 156 prototype locally and
extract afterward. That is precisely how the current one-off furniture
accumulated; the first customer should prove the library contract, not
postpone it.
