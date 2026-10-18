# Parked pull-out bodies

- `MeetingPullout.tsx` — the meeting card (HS-117-15). PHILO-17 (owner
  2026-10-10, "A meeting opens in one window"): the meeting window
  `pullout:meeting:<id>` shows the whole record (`MeetingWindow.tsx`), so
  this card body is parked. Not compiled (`tsconfig.json` excludes
  `_parked`).
- `ThreadPullout.tsx` and `thread-pullout.css` — the Thread window
  (HS-151-05). Betterment Q4 ("One Ask window", DECISIONS #14): Ask and
  Thread are one window; every Ask is kept as a thread and every thread opens
  in Ask (`openPullout` sends `thread:<id>` to `openAskThread`). The window's
  modes, tool rows, annotations and call chip are parked with it; its tests
  are in `_parked/__tests__/` (not collected). Not compiled.
- `threadWindowName.test.tsx` (from `desk/__tests__/`): the Thread window's title and Dock chip naming.
