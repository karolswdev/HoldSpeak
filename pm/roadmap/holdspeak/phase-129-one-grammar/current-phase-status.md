# Phase 129 — One Grammar

**Status:** done (11/11).

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
| HS-129-03 | The Brief pathology and Intelligence polish | done | [story-03](story-03-brief-pathology.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-129-04 | Shell-scroller and double-scroll repairs | done | [story-04](story-04-shell-scroller-repairs.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-129-05 | One foot in Speak; the great deletion | done | [story-05](story-05-speak-foot-and-deletion.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-129-06 | The container-query law | done | [story-06](story-06-container-query-law.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-129-07 | The speakable desk | done | [story-07](story-07-the-speakable-desk.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-129-08 | In-world editing — the lightbox dies | done | [story-08](story-08-in-world-editing.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-129-09 | One state grammar | done | [story-09](story-09-one-state-grammar.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-129-10 | Tokens green and the dead paths | done | [story-10](story-10-tokens-and-dead-paths.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-129-11 | The walk | done | [story-11](story-11-the-walk.md) | [evidence-story-11](./evidence-story-11.md) |

## Where we are

Phase 129 is complete: the frame owns one pinned-foot anatomy across desktop
windows and sheets; shell and double-scroll paths are repaired; Speak, state,
editing, and responsive container grammar converge on the shared primitives; and
the token gate is green. HS-129-11's final live walk passes 38 surfaces with
zero assertion violations and zero console errors, including every dock and Go
surface, engine-hit zone/meeting/artifact/workbench opening, Trust, Components,
the in-world Note editor, and the four mobile sheets. The web check chain is
green (779 tests). The backend criterion is amended by the recorded triage:
96 failures reproduce on pre-129 main and transfer as inherited debt to Phase
130, the one 129-caused delivery failure is fixed, and the mesh case is
flaky/environmental; the owner may overrule that amendment at the sitting.

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
- 2026-08-08 — Keep the 18px top corners on ≤720px sheets as the reviewed
  `--desk-sheet-top-radius` exception; the 6px inlet picker is likewise named
  `--desk-inlet-radius`, preserving both established silhouettes.
- 2026-08-08 — ShortcutSheet and attention/system surfaces are documented OS
  chrome outside Article VII.2's modal ban. **Narrowed 2026-08-09 per Sol's
  counsel (SOL-COUNSEL.md #7):** the exemption covers ONLY surfaces that are
  read-only, non-focus-trapping, immediately dismissible (Escape/backdrop),
  carry no creation/edit flow, and conceal no actionable failure. It is not
  an open-ended 'system chrome' escape hatch; anything beyond that boundary
  is an Article VII.2 modal and must become an in-world window or drawer.
- 2026-08-08 — **The inherited backend ledger (owner may overrule at the
  sitting):** the phase's first-ever full backend run found 98 failures;
  triage on pre-129 main (4c63c997, same env) reproduced 96 — inherited
  Phase 118–128 integration debt (companion slack/github/webhook, intel
  streaming, dictation surfaces, history slack, decision records, live bus,
  workbench-walk e2e, sync/guards). One was 129-caused (delivery collector
  conflated protocol-`incompatible` with source-failure-`stale`) and is
  fixed; one is flaky/environmental (mesh dispatch — passes on rerun).
  HS-129-11's suite criterion is amended accordingly (see the story file);
  the 96-test ledger transfers to the Phase 130 charter as a dedicated
  repair story. Reproduction logs ride in evidence-story-11.md.

## Decisions deferred

- RuntimeDocsCore's future (demote to real docs page vs restructure as
  compact reference) — default: restructure minimally in 129-09, revisit
  under the docs program.
- Workbench template-picker empty state — named in C §3; kept, as a
  deliberate application state, pending owner taste.
