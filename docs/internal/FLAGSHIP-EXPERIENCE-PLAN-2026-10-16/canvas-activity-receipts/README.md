# Activity Finished receipts — reviewed direction, 2026-10-16

Minimal direction on the current Button, SurfaceSection/Rows/Row, StringGadget,
EgressChip, ActionNotice and StatusStrip. The existing programme canvas material
provides the window and type context. Samples are declared direction; no owner
state, APIs, writers or navigation run. Root inspected all three direction poses
at 1440 and 393, then inspected actual Activity and source-door browser shots.

Root preview from the repository root:

```sh
./web/node_modules/.bin/vite --config docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/canvas-activity-receipts/vite.config.mjs
```

Capture each at 1440 and 393:

- `http://127.0.0.1:4502/?pose=populated`: existing Records plus Finished rows,
  title, timestamp, source name, outcome and qualified Open receipt; Load more.
- `http://127.0.0.1:4502/?pose=read-failed`: read failure, explicit GET Retry,
  retained rows marked Last read. No writer retry or false empty state.
- `http://127.0.0.1:4502/?pose=missing-door`: receipt remains readable with
  Receipt view unavailable; no dead Open or fallback navigation.

Root review correction: SurfaceRow `verbs` are intentionally revealed only on
hover/focus (or a coarse pointer); quiet controls title weight only. Receipt
navigation uses the existing row child slot with Button, so Open receipt
is visible without hover at both widths. No CSS was added. Failure copy names
the failed read, kept receipts and exact Retry.

Implemented product seam:

- Local Finished receipt reader, mounted only in Activity Records, calls existing
  `/api/desk/projections?kind=receipt&attention_state=resolved&offset=0&limit=50`.
  It never changes `useProjections` filters, selections or paging. Load more uses
  the returned page offset/limit; failed GET retains rows and its exact retry.
- Current Activity text filter also searches Finished. No count of zero; quiet
  empty token. Completed local work shows no default egress badge; a concrete
  outgoing actual destination uses the existing EgressChip.
- `/cadence` opens `configure-cadence`; exact `/history?meeting=<id>` opens
  `review-meetings` with `meeting:<id>` scope. These are canonical registered
  applications. Unsupported/blank/root/external or stale doors remain named
  unavailable. Use `openSurface`, whose false result can be shown, rather than
  silently queueing a missing surface or opening an unrelated primitive.
- Other source doors require an exact supported qualified source reference and
  a lawful existing opener. Do not repeat the parked shade's generic
  `openPrimitive(row.source_id)` fallthrough: a pipeline event id is not a
  primitive. Root settles any additional supported door before implementation.

Tuesday: Search Activity, read the finished sweep, press its own Open receipt,
and reach Rhythm while Activity stays available behind it.
