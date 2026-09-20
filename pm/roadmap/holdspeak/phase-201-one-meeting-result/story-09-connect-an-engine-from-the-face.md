# HS-201-09 - Connect an engine from the face

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The rehearsal (audits/rehearsal-07-opus.md) proves a stranger cannot connect an engine from the face. "Add an engine…" posts `{request_id,label,endpoint,model,requires_key}` (web/src/features/concierge/useConciergeController.ts:542-553) while the service demands `profile_id`, `expected_profile_revision`, `provider_family` and 400s "Provider draft is invalid." (holdspeak/services/model_library_service.py:277-294), rendered 400 px below the button. "Use these" is disabled while an unrelated group (Speech recognition) is WAITING (useConciergeController.ts:294). OFF on the meetings group changes no assignment, and the face forgets the applied truth on reopen. After setup there is no door to Models except ⌘K. At 393 the engine card overlaps the group labels and `⚠ TOOL INCOMPATIBLE` gives no reason. Tenets 3, 4, 5; Article VI; HS-201-05's exit is not deliverable by a stranger.

## Scope

- **In:** the face sends what the service accepts (the service mints `profile_id` and `provider_family` from the endpoint when the face omits them, or the face supplies them; smallest honest change, named in evidence); a failed check shows its reason beside the button in plain words; "Use these" is enabled per group: the summary group applies on its own, an unrelated WAITING group never blocks it; OFF on the summary group clears the exact `meeting.deferred_analysis` assignment and the face shows the APPLIED state on reopen (read from `summaryAssignment`, not the proposal); Models is one move from the desk (an entry in Go / the dock's Settings, whichever the manifest already supports) and its label is "Models"; "Add an engine…" is a library Button; the 393 card does not overlap; TOOL INCOMPATIBLE carries its reason.
- **Out:** downloads; the model-era collapse; cloud key handling beyond what exists.

## Acceptance criteria

- [ ] Isolated HOME, no engine: Models → Add an engine → the LAN URL → Check → READY → Use this for summaries → `summaryAssignment: assigned`; every step from the face, no route calls (e2e, real LAN engine at http://192.168.1.43:8080/v1 when reachable, else a local OpenAI-compatible stub).
- [ ] With Speech recognition WAITING, the summary group still applies.
- [ ] OFF then Use these → no exact assignment remains; reopen Models → shows OFF, not a proposal.
- [ ] From the arrival with setup done, Models is reachable in one move without ⌘K.
- [ ] Shots at 1440 and 393: no overlap; one filled primary; every verb a Button.

## Test plan

- **Unit:** vitest for canApply per group, the applied-state read, the reason rendering; pytest for the service accepting the face's body (fence red first).
- **Integration:** the e2e above.
- **Manual / device:** shots in assets/story-09-shots/.

## Notes / open questions

Lane B (Opus). Files: web/src/features/concierge/**, holdspeak/services/model_library_service.py, holdspeak/web/routes/concierge.py, web/src/desk/applications.ts or verbRegistry.ts for the Models door. Do not touch ChairHome.tsx, meeting_import.py, ImportSection.tsx.
