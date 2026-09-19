# HS-201-04 - Ask for the summary and find it again

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** HS-201-03
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The ledger's primary `Retry` does nothing (`history/helpers.ts:227` returns `Retry`; `history/CatalogRail.tsx:172` dispatches only on `Run intelligence`; zero requests measured). The Meetings footer chip is `<EgressChip />` with no props, a hardcoded `This device` (`HistoryCore.tsx:425`, `gadgets.tsx:740-746`). The Chair's Open passes a bare id where History wants `meeting:<id>` (`ChairHome.tsx:1743`, `HistoryCore.tsx:40`). The record's REMAINING facts render in a 7-character column and the error block overlaps the footer verbs (`MeetingIntelRecovery.tsx:100-139`) (audits/face-walk-opus.md defects 2, 6, 7, 9; "where the host is shown").

## Scope

- **In:** the first summary of a SAVED meeting (the normal case) and Retry on a FAILED one both run; the disclosure from 03 (`planned_route`) is shown beside EVERY verb that starts a run (Chair Run, ledger Retry/Run, record Retry) before the click, and the executed destinations after; the Meetings footer chip reads the same truth; Chair Open reaches the meeting; the summary is shown on the record with its meeting (traceable: the `intel_snapshots` row's `meeting_id`); after a hub restart the same summary is reached in at most two moves; the two layout defects fixed in the species where they are species bugs.
- **Out:** new windows; the live recording room; Room linking.

## Acceptance criteria

- [ ] The first summary of a saved meeting runs from its verb; Retry on a FAILED row issues the run POST; fences assert the requests, not the clicks.
- [ ] Beside each run verb, before the click: the planned route (host, and fallback if any); after: the destinations contacted. The Meetings chip is never a constant.
- [ ] Chair Open lands on the meeting record.
- [ ] Restart on the same HOME: the summary is found in at most 2 moves; shots before and after.
- [ ] REMAINING facts span the row at 1440; no error surface overlaps a verb (standing rule).

## Test plan

- **Unit:** vitest for the verb dispatch and the chip props.
- **Integration:** e2e in an isolated HOME with a stub engine: record, Retry, summary, restart, found.
- **Manual / device:** shots at 1440 and 393 for each station.

## Notes / open questions

Lane B (Muad'Dib to Opus). Depends on 03 for `planned_route` (the API contract is settled and checked before either lane builds against it). Serves exit criteria 3, 4, 5.
