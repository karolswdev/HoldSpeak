# HS-122-11 — The walk

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-07 through HS-122-10
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The backbone exists: services, MCP server, walk harness, desk doctor.
This story proves everything works together.

When this ships:

1. **Desk doctor passes.** All 8 checks green against the real hub.

2. **MCP drives real state.** From Claude Code (or a test script):
   - `desk.create("note", {name: "Architecture Decision"})` → note
     appears on the desk.
   - `desk.list("note")` → lists the note.
   - `workbench.add_item(wb_id, {title: "Review PR"})` → item appears
     in the workbench window.
   - `workbench.run(wb_id)` → run completes, results visible.
   - `desk.delete("note", note_id)` → note removed, receipt returned.
   - `meeting.list()` → meetings listed.

3. **Playwright captures the rendered state.** The walk harness runs
   the screenshot manifest. Each MCP-driven state change is
   reflected in the UI screenshots.

4. **No silent failures.** Console errors, failed requests, and
   unhandled exceptions are caught by assertion helpers.

## Acceptance criteria

- [ ] `holdspeak doctor` → all pass.
- [ ] MCP 10 tools exercised with real data.
- [ ] Walk harness captures all manifest states at 1440px + 393px.
- [ ] Assertion helpers pass on all captured states.
- [ ] Screenshots land in evidence assets.

## Test plan

- Run desk doctor. Capture output.
- Run MCP tool sequence. Capture results.
- Run walk harness. Capture screenshots.
- Review screenshots for visual correctness.

## Files in scope

- Evidence: `assets/` next to the evidence file.
