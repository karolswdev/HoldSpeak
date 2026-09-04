# HS-169-02 - The Door built to the canvas (one screen: the outcome line; source rows with in-world pickers and default Watches; the count is the test; Create Project)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** in-progress
- **Depends on:** HS-169-01
- **Unblocks:** HS-169-03, HS-169-05
- **Owner:** unassigned

## Problem

The 168 door needed 17 face steps and ~60 objects to pick a repo and a Jira project. The ratified canvas (01) shows one screen.

## Scope

- **In:** SetupCore replaced by the one-screen Door composed from the library (EditInPlace + MicButton, SurfaceLedgerRow, CheckGadget toggles, ChoiceCard pickers, StateChip/EgressChip, SurfaceFooter); the source rows from `GET /api/connections` (connected first; a not-connected row carries `Connect` → Settings → Connections in place, 168 D2's round trip); the in-world picker (typeahead + mic; recent first; a KNOWN SCOPE first with `ALSO WATCHED BY`, offered never applied); default Watches per provider (GitHub: open PRs on the default branch, CI; Jira: overdue, due 7 days; BLOCKED off) with `Adjust` holding the old population; THE COUNT IS THE TEST — picking a scope fetches the count through the SAME compile the Watch will evaluate (168's law); `Create Project` composes ONE service call from the existing seams (project + watches + baseline) — no new tables; a blank project with zero sources is allowed and named by the receipt; the glass rig at both widths asserting every step (5 clicks connected; the cold round trip).
- **Out:** the Room (03); the wire for needs-you (04); Settings → Connections (168, unchanged).

## Acceptance criteria

- [ ] Connected desk: outcome text → repo → Jira project → Create in 5 clicks, one screen, no scrolling at 1440 (the rig counts clicks and asserts no vertical overflow of the body at 1440).
- [ ] The count on a row equals the count the activated Watch's first evaluation produces (one compile; a parity test).
- [ ] Every verb is the library Button (`grep '<button'` zero in the feature); zero sentences; every egress chip names its host.
- [ ] Cold desk: `Connect` round trip returns to the same door with the row re-read as a picker row.
- [ ] Vitest for the door's states (cold / connected / picker open / checking / can't check); web baseline zero branch-new.

## Test plan

`cd web && npx vitest run src/features/project-room/door`; tests/e2e/test_hs169_door_glass.py at 1440 + 393 (isolated HOME, build-first, settle before every shot); `uv run python scripts/check_web_baseline.py --run`; the parity test under tests/unit/test_hs169_door.py.

## Delivered

_(pending)_
