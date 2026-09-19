# Charter audit — the live face walk (Opus worker, isolated HOME, 2026-09-19)

Rig: `uv run holdspeak web --no-open` from the main checkout at 16d78b0b, `HOME` a scratch directory, port 53901; bundle rebuilt first. Shots in `../assets/charter-walk/` (station-width). The owner's desk was never touched; a 52 s room-audio capture the walk made in the scratch HOME was deleted by the orchestrator.

## Stations (a stranger, no docs)

1. **Arrival** is one card: VOICE TYPING / Dictate one sentence / "Tap to speak, edit here, then use". No dock, no menu, no meeting verb; the only exit is `Continue later`. (01-arrival-1440/393)
2. **The Desk**: `Nothing needs you`, NO CALENDAR / Connect calendar, BRIEF / Generate / No brief yet, TALK / Develop a thought · Record meeting · Schedule; chrome chip `→ EXTERNAL REACH ENABLED`. (02-desk-after-continue-later-*)
3. **Record meeting** opens no window; a `0:03` timer chip appears bottom-right. Hub log at that second: `meeting session admission refused: no_assignment (No model assignment can be frozen.)` Nothing of it reached the glass. (03-record-meeting-1440)
4. **Stop**: the chair grows MEETINGS 1 / Untitled meeting / 1 MIN / QUEUED → FAILED. (04a, 04b)
5. **Meetings ledger**: header `Nothing needs you` above one FAILED row with a primary `Retry`. Clicking Retry issued zero requests. (05-*, 09-rail-retry-result-1440)
6. **The record**: INTELLIGENCE FAILED / RETAINED 0 SEG / REMAINING: SUMMARY, TOPICS, ACTION ITEMS, AND ROUTED ARTIFACTS rendered in a ~7-character column, broken mid-word. (06-*)
7. **Retry on the record**: `⚠︎ Meeting transcript is empty; no intelligence can run The Meeting and completed work remain saved.` The block pushes Retry/Skip under the window footer. (07-retry-summary-1440)
8. **Egress chip** → Data boundaries: `All data stays on this device · Enabled destinations: None · MEETING INTELLIGENCE OFF · Destination: This machine`. (08-*)
9. **Restart** on the same HOME: the FAILED meeting is on the Chair in zero moves; the record identical. (10-*, 11-*)
10. **Models** (`/profiles`): `No engine yet`, two Download offers, seven groups on `Quick local Qwen`, `7 WAITINGS`, `Use these`. (12-*)

## Defects (numbered as the worker reported them)

1. The product knows the blocker and no face says it: `/api/setup/status` returns `overall: needs_attention` and `primary_action.label = "Set a valid local model path…"`; the only reader, `web/src/pages/cores/SetupCore.tsx`, has zero importers. The Chair says "Nothing needs you".
2. The ledger's primary Retry does nothing: `history/helpers.ts:227` returns verb `Retry`; `history/CatalogRail.tsx:172` dispatches only on `Run intelligence`.
3. The refusal names the wrong cause: truth is `no_assignment` (`meeting_session/intel_admission.py:211`); the face says "transcript is empty" (`services/meeting_intel_service.py:41`).
4. Recording refusal is invisible when it happens: `_refuse_session` (`intel_admission.py:292-312`) writes `record_only` and logs ERROR; the desk shows a timer. 52 s of microphone captured with no possible transcript.
5. `Record meeting` opens no room; the `record-live` surface never mounts.
6. Broken layout at 1440: `meetings/MeetingIntelRecovery.tsx:137-139`.
7. Error block overlaps the verbs under the window footer.
8. Two contradictions of zero: `Nothing needs you` above a row with a NEEDS YOU section (`ChairHome.tsx:293` headline reused); `EXTERNAL REACH ENABLED` beside `All data stays on this device` (`desk/setup.ts:54-88`).
9. Run-on sentence: `MeetingIntelRecovery.tsx:100` concatenates a period-less server string.
10. Speech recognition assigned a text LLM in the Concierge's proposed set.

## Where the host is shown

- Before the run: nowhere on the meeting path. `HistoryCore.tsx:425` renders `<EgressChip />` with no props, a hardcoded `⌂ This device` (`desk/surface/gadgets.tsx:740-746`).
- After the run only: `CatalogRail.tsx:166-168` shows `runHost` from the POST response (`HistoryCore.tsx:158-168`); never rendered here because the POST never fired.
- Chrome chip: `DeskChrome.tsx:234`, label from `desk/setup.ts:54-88`; `actuators_enabled` alone yields "External reach enabled" with no destination.

## Restart

The result survived; found in zero moves on the Chair, one move to the ledger row, two to the record. DB: one row, `title=''`, `duration_seconds=52.69`.

## Labels not in ASD-STE100

| Label | File |
|---|---|
| "Tap to speak, edit here, then use" | `web/src/desk/components/FirstWords.tsx:356` |
| `RETAINED 0 SEG` | `web/src/meetings/MeetingIntelRecovery.tsx:135` |
| `REMAINING: … ROUTED ARTIFACTS` | `web/src/meetings/MeetingIntelRecovery.tsx:138` |
| `INTELLIGENCE FAILED` / `INTELLIGENCE` for "summary" | `web/src/pages/cores/history/MeetingHeader.tsx`, `MeetingIntelRecovery.tsx:125` |
| "no intelligence can run" | `holdspeak/services/meeting_intel_service.py:41` |
| `7 WAITINGS` | `web/src/features/concierge/ConciergeCore.tsx:388` |
| "Develop a thought", "Settle in", "Places", "Panes" | `web/src/desk/chair/ChairHome.tsx:2078`; `web/src/desk/verbRegistry.ts:245` |
| "Boundary / Authority / Background / Revoke / Last receipt" | `web/src/desk/components/TrustWindow.tsx` |
| "Untitled meeting" | `web/src/desk/api.ts:436` |
| "Meeting intelligence is awaiting Stop settlement" | `holdspeak/services/meeting_intel_service.py:41` |

## Smallest repairs (the worker's sizing)

1 S Retry dispatch · 2 S real placement on the Meetings chip · 3 M `primary_action` on the Chair as the one next action · 4 S the refusal names `no_assignment` · 5 S refusal shown at record time · 6 S layout · 7 S language · 8 M `Record meeting` opens the live room · 9 M chrome chip vs Trust window.

## Unknown

A successful summary was never observed (no model in the isolated HOME; none downloaded). The after-run host display needs a live run. Import audio and Skip not exercised.
