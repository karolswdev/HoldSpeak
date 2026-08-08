# HS-126-01 — Brief window and generation model

- **Project:** holdspeak
- **Phase:** 126
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-126-02 through HS-126-09
- **Owner:** unassigned

## The thesis (the bar)

A brief must answer for a precise, local-time window, not an ambiguous
"since last time." Define timezone-aware daily and Monday windows and a
`MondayBriefService` whose `generate()` operation has one stable result per
window. Reopening the desk must retrieve that result, never create a second
brief for the same period.

### What changes

1. Define daily window boundaries: previous close through current open.
2. Define Monday boundaries: Friday close through Monday open.
3. Establish the configured local timezone and the close/open boundary
   contract used by all callers.
4. Add the `MondayBriefService` skeleton and `generate()` API, including
   idempotency semantics keyed by the brief period.

## Acceptance criteria

1. Daily and Monday window calculation is timezone-aware, including DST.
2. A Monday brief spans Friday close to Monday open; a daily brief spans
   the preceding close to the current open.
3. Calling `generate()` repeatedly for one period returns the same brief
   identity and does not duplicate persisted output.
4. The service boundary is ready for collectors without coupling them to UI,
   HTTP, or MCP delivery.

## Test plan

- Unit: calculate ordinary daily, Friday-to-Monday, and DST-transition windows.
- Unit: generate twice for one period and assert one stable brief result.
- Unit: assert callers receive an explicit period and timezone in the model.
