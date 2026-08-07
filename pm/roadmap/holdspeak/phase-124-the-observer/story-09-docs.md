# HS-124-09 — Docs story

- **Project:** holdspeak
- **Phase:** 124
- **Status:** backlog
- **Depends on:** HS-124-07, HS-124-08
- **Unblocks:** HS-124-10
- **Owner:** unassigned

## The thesis (the bar)

After features, before closeout. Update entry-point documentation to
reflect the observer layer.

### Touchpoints

1. **`README.md`** — mention the pipeline observer in the architecture
   section (if one exists) or in the "what HoldSpeak does" summary.
2. **HANDOVER.md** — update or create a new handover noting the observer
   is shipped, what's next (analytics surface, retention policy, the two
   remaining run endpoints from Phase 123's handover).
3. **MCP docs** — add the 4 new resources and 1 new tool to whatever MCP
   documentation exists (inline in `holdspeak/mcp/` or in `docs/`).
4. **Service layer docs** — if any internal doc describes the service
   architecture, add the observer decorator and event flow.

### What this story does NOT do

- Does not create new standalone documentation files unless they already
  exist as stubs.
- Does not rewrite existing docs — only updates entry points.

## Acceptance

- Each touchpoint above is updated or confirmed already accurate.
- No broken internal links.

## Test plan

Manual review of updated files.
