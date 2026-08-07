# HS-121-10 — Recovery is a first-class state

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (SurfaceState action slot for retry)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Template picker infinite spinner on error. Constitutional context no
loading state. LLM errors raw in chat/ask. Delivery terminal no retry
from refused. SurfaceState error retry not always wired. Unchanged
from the original story.

Covers: N-C2 (raw LLM errors), N-C5 (workbench failure reasons),
N-C7 (template error), N-C8 (constitutional loading), N-C10 (retry
not wired), N-B2 (delivery retry).

## Acceptance criteria

- [ ] Template picker: error state with retry.
- [ ] Constitutional context: loading state visible.
- [ ] Ask/chat: human-readable LLM error messages.
- [ ] Delivery terminal: retry from refused.
- [ ] Workbench item failure: error reason surfaced.
- [ ] Every SurfaceState error usage has onRetry where retriable.

## Files in scope

- `web/src/desk/components/WorkbenchTemplatePicker.tsx`
- `web/src/pages/cores/ConstitutionalContextCore.tsx`
- `web/src/desk/chat.ts`, `web/src/desk/ask.ts`
- `web/src/desk/components/DeliveryTerminalWindow.tsx`
- `web/src/desk/components/WorkbenchWindow.tsx`
