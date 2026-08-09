# HS-130-09 — Workbench: one gesture one record, live voice

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Two shallow web defects that make the Workbench feel untrustworthy. **Double
create:** the create path persists a blank Workbench and opens it
(dataSlice.ts:150,163-188); the blank Workbench then shows a template picker
whose Template and Blank exits **each create another record**
(WorkbenchTemplatePicker.tsx:46-55 instantiate, :69-76 createBlank) — the first
blank is orphaned, listed, never cleaned up. Entry points: verbRegistry.ts:225,
WorkbenchesHomeCore.tsx:65. **Dead voice:** the grammar advertises `set-agent`
(workbench.ts:44-53) and `dismiss` (workbench.ts:34-43); the proposal switch
(WorkbenchWindow.tsx:1170-1221) handles neither, falling through to
`setVoiceProposal(null)` — the user sees the proposal accepted and nothing
happens.

### What changes

1. **Choose the template before persistence, then create one record.** The
   create gesture opens the picker first (or a picker-less "blank" path
   creates exactly one record); no blank Workbench is persisted before the
   choice. One creation gesture → one Workbench.
2. The dead cosmetic-only "Runs on" default (WorkbenchWindow.tsx:322 shows
   `profile_id || "this_machine"` while the picker maps the sentinel back to
   `null` on create) is reconciled to HS-130-01's one empty-value meaning
   (inherit, with source shown) — the stored and displayed token match.
3. **Wire or remove the dead voice intents.** `set-agent` either invokes the
   same assignment mutation the UI uses (assign an Agent/capability to the
   Workbench) or is removed from the grammar; `dismiss` likewise wired or
   removed. No intent may be advertised without a handler.

## Acceptance criteria

1. Creating a Workbench (from either entry point, template or blank) results
   in exactly one persisted Workbench record; no orphan remains.
2. The Workbench "Runs on" display and stored value are the same token and
   carry HS-130-01's inherit-with-source meaning.
3. Every voice intent the Workbench grammar advertises has a handler that runs
   (proven by exercising each), or the intent is absent from the grammar.

## Test plan

- Web: create-path test asserting one record for each exit; a store test for
  no orphan; a grammar/handler parity test (every advertised intent maps to a
  live case); the "Runs on" token-match test.
- `npm --prefix web run test:web -- run` read from file before flip.

## Out of scope

- `capability_ref` generalization (Workbench hosts Agent/Sequence/Workflow) —
  out of the whole program (status doc decision, SOL-COUNSEL.md #5).
- Workbench skill-binding scope (issue Wave 1 / Phase 132).
- Workbench sync bucket repair (Phase 131, with the sync registry).
