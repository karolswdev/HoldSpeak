# Frozen action and receipt source counsel — 2026-10-16

UNCHECKED — awaiting formal Muad'Dib review. This is bounded source counsel,
not Muad'Dib's check or a delivery verdict. Reviewed the frozen action and
receipt edits against base `9038911d9`, the settled `DESIGN.md`, and the current
fast cycle in `CLAUDE.md:6`. Product files were read only. No tests or browser
were run. Material, PR-result and frame work is outside this pass.

VERDICT: RATIFY

FINDINGS:

1. No material source regression found in the frozen scope. The controls
   compose the existing Button and CheckGadget species without adding a
   route, service or policy workflow. This supports Tenets 1, 3 and 5.
   Evidence: `web/src/desk/components/SpeakerGlyph.tsx:48`,
   `web/src/desk/components/MissionControlConveyor.tsx:165`,
   `web/src/desk/components/DeliveryDossierWindow.tsx:240`,
   `web/src/desk/components/WorkbenchResourceful.tsx:177`.

2. Replay has one native activation path. The Button defaults to native
   `type="button"`; SpeakerGlyph has only `onClick`, and retains the
   message-specific speaking test and replay/stop branches. The recorded
   Enter and Space checks assert one replay; the active-message Enter check
   asserts one stop. Evidence: `web/src/components/signal/Button.tsx:25`,
   `web/src/desk/components/SpeakerGlyph.tsx:33`,
   `web/src/desk/__tests__/speakerGlyph.test.tsx:118`,
   `.tmp/edges/actions-collect.log:21`.

3. Story selection now compares repo, project and Story ID before toggling
   or marking the control pressed. Proposal navigation retains that exact
   tuple. Pin and evidence handlers keep their own session/record identity
   and stop click propagation. Waiting sessions open their exact key; phase
   dossiers expose a Story verb only when its state is `ready`. Evidence:
   `web/src/desk/components/MissionControlConveyor.tsx:127`,
   `web/src/desk/components/MissionControlConveyor.tsx:174`,
   `web/src/desk/components/MissionControlConveyor.tsx:97`,
   `web/src/desk/components/MissionControlConveyor.tsx:195`,
   `web/src/desk/components/MissionControlConveyor.tsx:487`,
   `web/src/desk/components/MissionControlConveyor.tsx:697`,
   `web/src/desk/components/DeliveryDossierWindow.tsx:239`.

4. Ask zero grounding is explicit and has no zero counter. Positive
   grounding remains `max(0, matchedCount - overflowCount) OF matchedCount`.
   Citation refs and flagged claims remain adjacent to the same receipt;
   Keep and Retry still use their sent snapshot. Evidence:
   `web/src/desk/surface/citations.tsx:14`,
   `web/src/desk/components/AskPanel.tsx:463`,
   `web/src/desk/components/AskPanel.tsx:468`,
   `web/src/desk/components/AskPanel.tsx:300`,
   `web/src/desk/__tests__/askPanelRunsOn.test.tsx:80`,
   `.tmp/edges/receipts-collect.log:22`. This supports Tenets 3 and 4 and
   Constitution VI.

5. Resourceful routine names now appear in the token CheckGadget, whose
   native checkbox still owns selection. Existing policy limits, selected
   maintenance boundary, owner authority and paused state remain visible.
   The write callback still owns `pendingRef`; Retry retains its original
   settings/routines closure. Enable still arms before committing, and
   completed progress uses the stored denominator while the draft changes.
   Evidence: `web/src/desk/surface/gadgets.tsx:114`,
   `web/src/desk/components/WorkbenchResourceful.tsx:71`,
   `web/src/desk/components/WorkbenchResourceful.tsx:175`,
   `web/src/desk/components/WorkbenchResourceful.tsx:188`,
   `web/src/desk/components/WorkbenchResourceful.tsx:216`,
   `web/src/desk/components/WorkbenchResourceful.tsx:225`,
   `web/src/desk/components/__tests__/workbenchAutomations.test.tsx:246`.

6. The named recorded collections and run tails were read. Actions collect
   25 named tests and report 3 files / 25 tests passed; receipts collect 30
   named tests and report 3 files / 30 tests passed. The collections include
   duplicate Story identity, pin/evidence propagation, native activation,
   zero/overflow grounding, stored progress and Retry payload checks.
   Evidence: `.tmp/edges/actions-collect.log:7`,
   `.tmp/edges/actions-collect.log:25`, `.tmp/edges/actions-run.log:5`,
   `.tmp/edges/receipts-collect.log:7`,
   `.tmp/edges/receipts-collect.log:30`, `.tmp/edges/receipts-final.log:5`.
   These are recorded component results, not a claim that I reran them or
   verified the hub/provider path.

CONDITIONS:

None required by this source pass. Formal Muad'Dib review remains outstanding
under the current fast cycle; this report does not replace it.

MISSED:

No additional material source defect established. The new four-selector
phone target rule reserves target size and margins only; the wrapping remains
in the owned Rails stylesheet (`web/src/styles/global.css:214`,
`web/src/desk/components/mission-control.css:135`). Its real cost in belt
height and pointer ownership needs the root's actual observations.

TUESDAY:

The source preserves the owner's replay, exact Story, evidence and idle-policy
jobs with clearer controls; actual ease of use is not established by this pass.

UNKNOWN:

- Actual 1440/393 layout, readable ink, focus treatment, active replay paint,
  target corners/edges, clipping and overlap. No browser or shots inspected
  in this source-only task; root owns actual proof separately.
- Real audio, provider execution, durable writes, kernel receipts and live
  session/evidence destinations. The focused tests exercise component seams.
- Test isolation/lock invocation and later quick-check results. The supplied
  collection/run files show names and totals, not the launch environment.
- Material, PR-result and frame changes, which were still building when this
  pass was assigned.
