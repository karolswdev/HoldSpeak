# Phase 129 — One Grammar

**Status:** chartered (0/11).

**Last updated:** 2026-08-08.

## What we're building

The owner's verdict, verbatim: *"treat this as a wholistic product with the
same behavior across nearly all functional planes."* HoldSpeak's rooms are
individually crafted but collectively dialectal: footers that float or scroll
away, a window that grows to 9,710 px, editors that are secretly modals,
text inputs a voice-first product cannot speak into, five competing footer
grammars (four of them dead), rooms reflowing on viewport width against the
container-query law, and a failing token gate. This phase makes the window
contract, the interaction grammar, and the CSS architecture ONE — evidence
first, then deletion before invention.

## The evidence base (pre-charter survey)

Four parallel deep audits, 2026-08-08, reports under the session scratchpad
(`reports/audit-{A,B,C,D}-*.md` + 37 walk screenshots), summarized here so the
phase is self-contained:

- **A (window census):** `DeskWindowFrame` has no foot slot; `SurfaceWindowHost`
  mounts all 14 registered cores entirely inside the scrolling
  `.desk-surface-body`, so every hosted-core `SurfaceFooter` scrolls away.
  All 18 primitive pullouts + 8 direct windows compose correctly (ZoneWindow
  is the minimal reference; `WingSlotContext` is the slot precedent). The
  ≤720px sheet rule (`dock.css:173-187`) puts `overflow:auto` on the window
  SHELL, breaking head/body/foot for every sheet. DeliveryBoard and
  DeskToolInspector scroll their own heads away; ConstitutionalContextCore
  and DeliveryDossier double-scroll; legacy WorkbenchCore is unhosted.
- **B (live walk, 22 surfaces, 37 shots):** P0 — Intelligence Brief window
  computes to 9,710 px with no scroll path and an unreachable grip. P1 —
  Settings' footer floats ~179 px above the window bottom; Meetings floats
  130–156 px; small resize clips content and loses footers (Speak's sticky
  strip overlays its clipped body). P2 — Activity list clips at the border;
  desk-object double-click opened no window in the scripted walk. P3 —
  Delivery reports `DW exited 2`.
- **C (interaction grammar):** InlineEditor is a fixed lightbox (Article
  VII.2 breach); WorkflowEditor has four bare mic-less inputs; Note/KB
  editors partially unspeakable; Receipts search bare and unspeakable;
  RepoWindow private controls; RuntimeDocsCore is a prose manual;
  WorkbenchWindow state/verb dialect sprawl; WorkbenchCore bare
  `SurfaceCode` outside a RAW fold; Repo/Coder sentence-prose errors.
- **D (CSS architecture):** `SurfaceFooter` is canon (42 live sites);
  `.surface-status`/`.prefs-status`/`.surface-receiptbar` root/
  `.desk-pullout-foot`/`DeskWindowFooter` are dead — delete;
  `.speak-status` is the one live sticky impostor. Frame anatomy is split
  across `pullout.css` + `window-chrome.css`; six rooms use viewport media
  against the container law; `tokens:gate` fails with 27 raw-value
  violations; z-ladder has six unallowlisted raws plus an undocumented
  `--z-sticky` band. D supplies the no-breakage migration order this
  phase's story sequence follows.

## Constitutional grounding

- **Article I:** features do not own surfaces — the frame owns the foot,
  cores publish into it (the WingSlot precedent made symmetric).
- **Article IV.1:** every text input can be spoken into — the mic census
  closes.
- **Article VII.1–3:** no prose, no modals, one quiet window grammar — the
  InlineEditor lightbox and the room dialects end here.
- **Article VIII.1–3:** OS-grade craft — head fixed, body scrolls, foot
  fixed, in every window, at every size, on every viewport.

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-129-01 | The foot slot — one window anatomy | done | [story-01](story-01-the-foot-slot.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-129-02 | The sheet contract at ≤720px | done | [story-02](story-02-the-sheet-contract.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-129-03 | The Brief pathology and Intelligence polish | in-progress | [story-03](story-03-brief-pathology.md) | — |
| HS-129-04 | Shell-scroller and double-scroll repairs | done | [story-04](story-04-shell-scroller-repairs.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-129-05 | One foot in Speak; the great deletion | backlog | [story-05](story-05-speak-foot-and-deletion.md) | — |
| HS-129-06 | The container-query law | backlog | [story-06](story-06-container-query-law.md) | — |
| HS-129-07 | The speakable desk | done | [story-07](story-07-the-speakable-desk.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-129-08 | In-world editing — the lightbox dies | backlog | [story-08](story-08-in-world-editing.md) | — |
| HS-129-09 | One state grammar | backlog | [story-09](story-09-one-state-grammar.md) | — |
| HS-129-10 | Tokens green and the dead paths | backlog | [story-10](story-10-tokens-and-dead-paths.md) | — |
| HS-129-11 | The walk | backlog | [story-11](story-11-the-walk.md) | — |

## Where we are

HS-129-01 landed the frame-owned foot slot: hosted `SurfaceFooter` instances
now portal into a sibling after the scrolling body, while pullouts and direct
windows retain their in-place composition. HS-129-02 preserves that frame
anatomy at ≤720px: sheet shells no longer scroll, while the body remains the
single scroll owner and the head and foot stay pinned. HS-129-04 repairs the
remaining shell and duplicate scroll paths: DeliveryBoard and DeskToolInspector
now keep their heads fixed, Constitutional Context and Delivery Dossier have
one primary body scroller, and the unreachable legacy WorkbenchCore is gone.
Activity needs no source change: HS-129-01's host body fix made its records
scrollable in the live walk. HS-129-03 and 05 remain unblocked; HS-129-07
closes Audit C's unspeakable-field census with shared text controls and
field-owned mics. The non-waivable exit remains story 11's walk.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Foot-slot refactor breaks a correctly-composed window | medium | contract tests first (D's step 1): footer-sibling invariant + only-body-scrolls; ZoneWindow as the frozen reference | any previously-correct pullout regresses in the walk |
| Deletion removes a live consumer | low | D's census names live vs dead per class; grep-before-delete is in each story's test plan | tokens/tests fail after a deletion commit |
| Sheet fix regresses phone usability | medium | B's four mobile shots are the before-baseline; story 02 reshoots the same four | a sheet that scrolled its whole shell now clips its body |
| Grammar sweeps balloon into redesigns | medium | stories carry explicit out-scopes; no new visual language, only the existing Signal grammar applied | a story PR touches tokens.css aesthetics or invents new components beyond named variants |

## Decisions made (this phase)

- 2026-08-08 — Causal Graph moves to Phase 130; the owner's holistic-product
  mandate takes 129 — direct owner direction.
- 2026-08-08 — Deletion before invention: canonize `SurfaceFooter` + the
  sibling contract; kill the four dead footer grammars rather than
  generalizing them — audit D's consolidation map.
- 2026-08-08 — The foot slot mirrors `WingSlotContext` (a portal seam in
  `SurfaceWindowHost`), not another sticky-CSS workaround — audit A §3.4.

## Decisions deferred

- RuntimeDocsCore's future (demote to real docs page vs restructure as
  compact reference) — default: restructure minimally in 129-09, revisit
  under the docs program.
- A formal sheet-radius exception token (18px top corners at ≤720px) —
  default: keep the current look, document the exception in 129-10.
- Workbench template-picker empty state — named in C §3; kept, as a
  deliberate application state, pending owner taste.
