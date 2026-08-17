# HS-136-02 — The schedule verb (API + MCP)

- **Project:** holdspeak
- **Phase:** 136
- **Status:** done
- **Depends on:** HS-136-01
- **Unblocks:** HS-136-03
- **Owner:** unassigned

## Problem

The spine (HS-136-01) can fire a schedule, but nothing can create,
list, edit, cancel, or delete one — and the owner's standing value is
that the front door be "something we can drive independently with MCP."
A schedule must be reachable over both HTTP and MCP.

## Scope

### In

- **HTTP routes** beside the meeting routes
  (`holdspeak/web/routes/meetings/live.py`): list / create / update /
  delete a scheduled recording, and cancel an armed (counting-down)
  one. Create/update validate the cron (reuse the conductor's parser)
  and the duration; enabling writes the delegation receipt from
  HS-136-01. Refusals are typed and honest (bad cron → named 4xx, never
  a 500), per the house error grammar.
- **MCP tools** in `holdspeak/mcp/tools.py` (beside
  `meeting.start_capture`, lines 514-521): `scheduled_recording.list`,
  `.create`, `.update`, `.delete`, `.cancel_armed`. Same core, same
  refusals, so an agent drives scheduling exactly as the UI does.
- **Receipts.** Create/enable/cancel/delete each leave a receipt
  (V.2); the tools return the receipt reference, not a bare ok.

### Out

- The web surface (HS-136-03).
- The conductor itself (HS-136-01).

## Acceptance criteria

- [ ] CRUD + cancel-armed over HTTP, each with a scoped route test
  (create → list → update → cancel → delete round-trip).
- [ ] The same operations over MCP, tested through the tool layer, with
  identical refusals to the HTTP path.
- [ ] A bad cron or a non-positive duration is refused with a typed
  error, not a 500 (test).
- [ ] Enabling a schedule writes the bounded-delegation receipt; the
  create tool returns its reference (test).

## Test plan

- `uv run pytest -q tests/ -k "schedule and (route or mcp or tool)"`
  — HTTP route contracts + MCP tool contracts + refusal cases.
- Scoped only; live drive-from-MCP proof rides HS-136-04.
