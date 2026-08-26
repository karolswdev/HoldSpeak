# HSEGHS001HS104-143-13 - Capability Assignments Experience

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-02, 143-04, 143-07, 143-11, 143-12
- **Unblocks:** 143-14
- **Owner:** unassigned

## Problem

Granular routing must not become a capability×model matrix or verbose wizard.
Owners need bounded group summaries and one focused ordered-chain editor.

## Scope

- **In:** Bounded Assignments overview; searchable overrides/issues; shared
  AssignmentSummary/Editor/model chooser; atomic reorder save; exact inheritance,
  boundary, issue, and runtime receipt copy.
- **Out:** Select-per-row UI, raw IDs, and duplicate feature-owned selectors.

## Acceptance criteria

- [ ] The twentieth capability does not increase default page height.
- [ ] One-primary editor atomically saves order and supports keyboard reorder.
- [ ] Default/Automatic always names the effective chain.
- [ ] Broken saved entries remain visible; issues sort first with one Fix.
- [ ] 393 has 44 px targets, sticky in-sheet Save, wrapped names, no overflow.
- [ ] Only migrated consumer families are editable; Thoughts ships first, and
  Stories 08–10 activate their groups/leaves without creating new UI.
- [ ] Group/global editors render server-projected compatibility/policy issues;
  leaf Use-default previews its exact effective chain before clearing.

## Test plan

- **Unit:** inheritance, group/global differing-policy compatibility, registry
  growth issues, Use-default preview, reorder, conflict, focus, keyboard, screen reader.
- **Integration:** library→assignment→Thought next-run and fallback receipt.
- **Manual / device:** 1440/393 one-primary/no-matrix real-path glass.

## Notes / open questions

Follow the exact composition and rejection criteria in `assets/owner-experience.md`.

## Progress

- 2026-08-26 — Plan ratified (`assets/story-13-assignments-plan.md`; five
  ORCH-CALLs accepted: peer Settings tile, seven global rows + contextual
  subject summaries, narrow HTTP fold-in, preview→revision-checked
  Use-default, pickers-die-disclosures-live boundary). Round 1 (S1+S2):
  closed `AssignmentEditorProjection@1` + bounded task-override projection
  + server-filtered candidates on the canonical assignment service;
  owner-before-body summary/editor/set/preview/clear routes; the peer
  Settings Assignments destination with the bounded seven-row overview
  and editor shell; real-hub shots (1440/393 × populated/empty/error) in
  `assets/story-13-shots/`. Orchestrator-verified: S1 python + routes +
  glass e2e 31 passed; worker set 77 + component 12 + build/check green.
  Orchestrator eyeball flag for S3: the repair affordance renders doubled
  ("Fix Fix" — label beside button) on issue rows.
- 2026-08-26 — Round 2 (S3, the shared editor sheet): reusable
  AssignmentSummary/AssignmentEditor/AssignmentModelChooser atoms;
  atomic 1–4 leg drafts with reorder/removal and server-only candidates;
  ABA-safe Use-default (preview returns its observed expected_revision,
  clear consumes it, conflict discards preview with in-flow Refresh —
  conflicts map to HTTP 409); Next-run receipts; focus loop/Escape
  restore/Mod+Enter; 393 sticky-footer composition; the doubled Fix
  affordance fixed with regression proof. Eight shots regenerated incl.
  assignments-editor-1440/393. Orchestrator-verified: service/routes/
  glass 34 passed + component 8 passed; worker: frozen next-admission 6,
  census guards 15, build green.
