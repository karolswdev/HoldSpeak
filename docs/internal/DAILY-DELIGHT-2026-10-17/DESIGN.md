# Daily work — continuing the owner's usability direction

The owner: “And I'm yelling still. I really still need you to keep pushing for delighting the end user.”

The previous functional/layout pass is shipped, not aesthetically accepted. This pass is judged through populated screens and the complete writing → answer → save → return journey. The Tuesday question is whether the owner can concentrate on the work with clear outcomes and little interface housekeeping.

Base: `ebd2387b1`; tree `wt-daily-delight-20261017`; branch `feat/daily-delight-20261017`. The serving tree is `wt-daily-recall-delivery-20261017`, PID82970, frontend22aa76d6327046a1 at the start; re-derive before delivery. No builds/tests in that tree. Preserve Jupiter4488 and dependencies.

## Direction to settle on the actual library canvas

- Decision: a coherent saved document, tighter supporting facts and one clear Send entry. Editing and reading should feel like the same document. No duplicate labels or default empty sections.
- Ask: let the answer lead. Keep the route disclosure where it belongs, but make ordinary status human-readable. The saved answer must have an obvious, truthful continuation. Context tools should occupy space when used, with the writer and primary action always reachable.
- Thread: compact, findable commands and sources, preserving the conversation and writer. Keep command labels, keyboard behavior and draft custody. Do not turn a routine picker into a second full screen of choices.
- Use existing Workbench paper, steel, type and component species. Any shared material change is settled once by root. Preserve voice, target sizes, visible errors, source identity and retained drafts.

Initial worker assignment is bounded read-only diagnosis/proposal. Root settles the canvas and exclusive implementation files before build. Workers use Sol HIGH under the owner-invoked KICKOFF and hold for SHIP. No staging or commits by workers.

## Verification and delivery

Real isolated graph walks at1440/393, before/after screenshots, actual pointer/focus checks for changed controls, smallest relevant scoped tests, ordinary quick, merge and normal idle local delivery. All heavy jobs serialized under scripts/test_lock.py; private HOME/keys; no real provider/native actions. Root inspects screenshots and an independent worker reviews the integrated result. Full-main and formal review follow merge in a separate tree. Keep prior Room/People findings visible without derailing this UI batch into speculative backend work.

## Settled direction — 17 October

Root inspected actual-library canvas shots in `.tmp/delight/canvas/` (Decision desktop, Decision editing phone, Ask phone, Thread commands phone). Canvas source is `canvas/`. This is design evidence with sample data, not runtime proof or owner acceptance. Implement the composition while retaining real state, routing and errors.

1. **Decision**: one paper document wraps Decision, Background and Consequences; omit absent saved sections. Compact wrapping steel facts omit the redundant visible status label. Editing keeps the same document, with visible Cancel beside facts and Save in the footer. Use existing per-object `editorDraft`/`deskMemory` helpers to retain unsaved fields across close and reload; reopening restores editing. Explicit Cancel discards this draft; only an acknowledged current Save clears submitted draft values. A late save must not erase newer text, including edits in a reopened instance. Closing does not commit to the DB and requires no modal. Remove only the repeated static Send label from shared SendWellsFold; retain its button, held state, receipts and lazy history.
2. **Ask**: collapsed Question fold keeps the exact sent prompt inspectable; the answer is the first expanded material. Move sent Sources below it; Run details contains the unchanged canonical route receipt. Ordinary footer says Answered (or real nonzero duration); route/egress remains visible. Editing has one bounded context well below the writer, retaining source names and all selection controls. Keep opens the exact confirmed artifact via canonical `openRef`; always retain Ask behind it, preserving newer writing and selections. Returning offers Open saved answer, not a second Keep. Ordinary typing increments the existing generation guard so a late answer cannot hide newer writing.
3. **Thread**: a bounded command well above the writer with Find command and roughly four visible single-line results (name plus slash syntax). Source and argument result lists use the same compact height. Arrow keys/Enter operate on the actual selected result; selected items scroll into view; Escape returns to the writer and IME is preserved. Keep as note stays in the thread and exposes Note saved / Open note for the exact returned id; artifacts use the same continuation if already supported.
4. **Scroll hints**: Ask owns a minimal shared CSS extension: vertical hint background/depth accept custom properties with the existing surface/28px defaults. Ask and Thread paper readers set paper color and 12px depth. Preserve overflow behavior and announcements. No new component or duplicated fade implementation.

Ownership: delight_decision owns DecisionPullout, its rules in attention-records.css, shared SendWellsFold, and named Decision/Send tests. delight_ask owns AskPanel, ask-panel.css, the minimal ScrollHint custom-property seam in surface.css, and named Ask tests. delight_thread owns ThreadComposer, ThreadPullout, thread-pullout.css and their tests. Root owns this record, canvas, graph atlas/harness, shared contract documentation and integration. Workers do not edit each other's files, stage or commit. Focused suites named in briefs run under the machine lock, with private HOME/keys. HOLD FOR SHIP.

Runtime visual refinement: command/source fields need visible Find command / Find source placeholders. Results cap at144px desktop and132px phone (three44px choices), giving conversation space back. Empty argument collections use their existing named state once.

Ask receipt placement is an implementation decision for the owner's current usability request: the former full technical footer line (2026-10-05 direction) becomes the unchanged canonical receipt inside Run details. The actual destination/egress chip and fallback remain visible in the footer, and the answer/refusal keeps its receipt-derived lamp. Thread retains its existing full-route footer. This changes placement, not route truth or provenance; it is not recorded as a separate owner ruling. Broad route tests must prove the same facts in these locations.
