# HS-162-04 - The verbs on the wire: draft, regenerate, save, copy, publish

- **Project:** holdspeak
- **Phase:** 162
- **Status:** backlog
- **Depends on:** HS-162-03
- **Unblocks:** HS-162-05, HS-162-06
- **Owner:** unassigned

## Problem

UPD-005: Save, Copy Markdown, and Mark Published are SEPARATE
commands with honest receipts. The driver names the verbs:
project.list_updates / draft_update / update_draft / publish_update.

## Scope

- **In:** routes under the house law (envelope where commands speak
  it): GET /api/projects/{id}/updates (list),
  POST /api/projects/{id}/updates/draft (draft; body {generator}),
  PUT /api/updates/{id} (save the owner's edit — draft only, UPD-004
  enforced on the wire), POST /api/updates/{id}/regenerate
  (supersede-unaccepted), POST /api/updates/{id}/publish (lifecycle
  + project revision law + receipt), GET /api/updates/{id}/markdown
  (the copyable artifact — Copy is a client act over an honest GET,
  the receipt is the read). command_id replay law; api-surface regen
  additive; integration tests through the real app incl. the
  publish-immutability refusal and the full draft→edit→publish loop.
- **Out:** UI (05).

## Acceptance criteria

- [ ] Every route success + failure typed; publish refuses on a published row; save refuses on published (409/typed per house law).
- [ ] The loop through HTTP: draft(deterministic) → save edit → publish → list shows lifecycle; regenerate on published creates a NEW draft.
- [ ] api-surface additive; prior pins untouched.

## Test plan

- **Integration:** tests/integration/test_update_routes.py.
