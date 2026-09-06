# HS-169-02 - The Door built to the canvas (one screen: the outcome line; source rows with in-world pickers and default Watches; the count is the test; Create Project)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** done
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

## Delivered (2026-09-05)

- **The wire (holdspeak/services/project_door_service.py; routes/project_door.py):**
  `POST /api/projects/door/count` {provider, scope, watches, adjust?} →
  tokens · plain count · checkedAt · host · state live/cant_check ·
  plain reason — the count runs the SAME source snapshot and compile the
  Watch's evaluation runs (parity tests for GitHub and Jira in
  tests/unit/test_hs169_door.py); `POST /api/projects/door` {outcome,
  sources[]} → ONE service call: project (name = outcome[:80], the
  finalize derivation) + one Watch per default per source + baseline;
  zero sources = a blank project. Defaults: GitHub OPEN PRS + CI (the
  `branch_ci` kind from 04); Jira OVERDUE + DUE 7 DAYS (+ BLOCKED off).
- **The face (web/src/features/project-room/door/):** DoorCore replaces
  SetupCore at the `project-setup` surface key (applications.ts; the
  setup/ folder stays in the tree unused for 07 to park). Composed from
  the library: the outcome well + MicButton; SOURCES rows (boxed, one
  grammar at both widths — a container query switches to the four-line
  grammar under 560px); the beveled picker control with the stroke
  chevron; default-Watch toggles as the TOKEN species (CheckGadget
  `variant="token"` added to the library); the three row states
  (UNPICKED / CHECKING pulsing / LIVE); the in-world picker (typeahead +
  mic; recent first; known scope by token); Adjust as a Disclosure well
  (BASE BRANCH · LABELS · INCLUDE DRAFTS; ISSUE TYPES · JQL); the
  not-connected row with `Connect` → Settings → Connections in place and
  the re-read on return; the footer receipt at the left edge; motion
  moments 1 and 2. The window opens at 640 × 580 so the picker fits.
- **Tests:** vitest door 28; tests/unit/test_hs169_door.py 11; design
  system + density guards; web baseline zero Door branch-new; the glass
  rig tests/e2e/test_hs169_door_glass.py (1440 + 393; connected + cold
  legs): 5 clicks to Create, no body scroll at 1440, no overlapping row
  children at 393, the cold Connect round trip returns to the door;
  shots in assets/story-02-shots/ read beside the artboards.
- **168's Sources rig** retired with a documented skip naming its
  replacement.
- **Debt (07 ledger):** the door window should hug its content and grow
  with the picker (DeskWindow's `fitContent` is not exposed to surface
  windows and does not re-measure); MCP twins for the two door routes.
