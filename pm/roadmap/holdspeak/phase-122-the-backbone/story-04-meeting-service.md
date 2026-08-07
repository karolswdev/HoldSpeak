# HS-122-04 — Meeting service

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-122-06 (thin routes audit)
- **Owner:** unassigned

## The thesis (the bar)

Meeting lifecycle routes are already thin — they delegate to WebContext
callbacks (`on_start`, `on_meeting_stop`, `on_bookmark`,
`on_update_meeting`). But those callbacks live on the web composition
context, not on a named service. An MCP adapter cannot call WebContext
without importing the web layer.

When this ships, a `MeetingService` wraps the meeting lifecycle and
query operations. The WebContext callbacks delegate to this service.
The routes delegate to this service. MCP can call this service.

## Scope

- `MeetingService.list(principal, query?, from?, to?, limit?, cursor?)`
- `MeetingService.get(principal, id, include?)`
- `MeetingService.start_capture(principal, config?)`
- `MeetingService.stop_capture(principal, meeting_id?)`
- `MeetingService.bookmark(principal, meeting_id)`
- `MeetingService.update(principal, meeting_id, patch)`
- `MeetingService.delete(principal, meeting_id)`
- `MeetingService.export(principal, meeting_id, format)`
- `MeetingService.search_artifacts(principal, query, limit?)`

## Acceptance criteria

- [ ] `MeetingService` class exists.
- [ ] WebContext callbacks delegate to MeetingService methods.
- [ ] Meeting routes delegate to MeetingService.
- [ ] Service is importable without FastAPI or WebContext.
- [ ] Existing API behavior unchanged.
- [ ] Tests pass.

## Files in scope

- New: `holdspeak/services/meeting_service.py`
- `holdspeak/web/routes/meetings/live.py`
- `holdspeak/web/routes/meetings/` (other meeting route modules)
- `holdspeak/web/context.py` (WebContext callback wiring)
