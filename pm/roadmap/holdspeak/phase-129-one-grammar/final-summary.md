# Phase 129 — One Grammar: final summary

**Closed:** 2026-08-08 (chartered, built, walked, and shipped in one day).
**Branch:** `phase-129-one-grammar`, 15 commits, every one through the gate.
**Verdict awaiting:** the owner's sitting (including the right to overrule
the backend-ledger amendment).

## What the owner asked for

*"Treat this as a wholistic product with the same behavior across nearly
all functional planes. Have your terras dig so incredibly deep."* — after
two screenshots: a Speak status strip that detached mid-scroll and
concealed content, and a Settings footer that never touched the window
bottom.

## How it ran

Four parallel deep audits first (window census, 22-surface live walk with
37 shots, interaction grammar, CSS architecture) — then an
evidence-grounded charter of 11 stories, then thirteen Terra agents
implementing and shipping through the PMO gate with serialized commits on
one branch, the orchestrator verifying on glass between landings.

## What changed

- **One window anatomy.** The frame owns a foot slot (the WingSlot
  precedent made symmetric); all 14 hosted cores' footers pin to the
  window bottom; ≤720px sheets keep head and foot while only the body
  scrolls; DeliveryBoard and DeskToolInspector no longer scroll their own
  title bars; the double-scrolls are gone; the orphan WorkbenchCore is
  deleted.
- **The Brief pathology.** A populated Intelligence Brief opened at
  9,710 px with an unreachable grip — root cause was `.is-floating`
  clearing the card's max-height. Now 804 px with the material scrolling
  inside.
- **The great deletion.** Four dead footer grammars, the `:has()`
  clearance hacks, the last live sticky impostor (`.speak-status`), and
  `DeskWindowFooter` are deleted; Speak has one foot.
- **One interaction grammar.** Every audited text input is speakable
  (Article IV.1); the InlineEditor lightbox died — editing happens in
  real desk windows or in the object's pullout (Article VII.2); loading/
  empty/error dialects converged on SurfaceState; guts fold behind RAW;
  prose became receipts; RuntimeDocs became compact reference rows.
- **One CSS architecture.** Room content reflows on window width
  (`@container surface`), never viewport; the `desk-surface` alias is
  gone; the tokens gate went to 0 (27 gate findings at charter, 23 of them raw
  values, 23 remaining at HS-129-10's start) with tokens generated
  from `design-tokens.json` only; radius/letter-spacing exceptions are
  named tokens.
- **The suite tells the truth.** 17 web test failures repaired — three
  were real product bugs (runAsk/runChatTurn silently discarding hub
  error receipts). Web: 109 files, 779 tests, green. The first-ever full
  backend run found 98 failures; triage on pre-129 main reproduced 96 —
  the inherited Phase 118–128 ledger, transferring to the Phase 130
  charter. The one 129-caused failure (collector conflating
  `incompatible` with `stale`) is fixed; one is flaky/environmental.
- **The walk.** 38 surfaces at 1440 + 393, default/scroll/resized/
  maximized/sheet states, zero assertion violations, zero console
  errors, before/after pairs against every audit defect, reusable
  harness at `scripts/walk-129.mjs`.

## The numbers

| Metric | Before | After |
|---|---|---|
| Hosted cores violating the foot contract | 14 | 0 |
| Sheets scrolling their own chrome | all | 0 |
| Footer grammars | 5 (4 dead) | 1 |
| Tokens-gate findings (27 at charter, 23 raw values) | gate red | 0, gate green |
| Viewport-media law violations | 6 rooms | 0 |
| Unspeakable audited inputs | 10 | 0 |
| Modal editors | 1 (Note/KB/Recipe/Workflow) | 0 |
| Web suite | 17 failing | 779 green |
| Backend ledger | unmeasured | 96 named + logged (inherited) |
| Walked surfaces / violations | 22 / many | 38 / 0 |

## Held for the owner's sitting

1. The backend-ledger amendment (overrule → the 96 fixes block Phase 130's
   charter instead of riding in it).
2. Three verb-home moves judged more-than-placement and backlogged
   (Decision pullout footer Edit; Workbench triple-home; Repo split).
3. The Delivery rail: the registered dw at the mapped clone lacks
   `capabilities --json` — refresh that clone or re-register.
4. HS-91-10 remains the standing owner-gated close (Swift parity + UAT).

## The seed for Phase 130

The Causal Graph (the Terra Council's fourth pillar, recipe in hand) plus
the inherited backend repair story. The desk now behaves like one product;
next it explains itself.
