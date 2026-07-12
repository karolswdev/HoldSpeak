# HS-93-06 progress record — A meeting survives real life

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `ebcf8da7`<br>
**Second-slice baseline:** `aaad1af1` (`HS-93-06: make Meeting sync
conflicts an explicit choice`)<br>
**After build:** current `agent/hs-93-06-meeting-survives-real-life` working
tree; no commit identity claimed<br>
**Acceptance status:** in progress — owner-visible Web/Hub conflict recovery
and truthful partial-intelligence Retry/Skip are implemented, production-Web
captured, and automatically verified. Long captures, real faults, offline sync,
native parity, owner observation, and physical iPhone/iPad evidence remain open.

## First vertical slice: a conflict becomes a decision

Phase 92 retained both sides of an equal-clock Meeting conflict in
`meeting_sync_conflicts`, but the record was read-only: History and the Desk did
not show either version, and there was no API that could resolve it. The product
could therefore claim a conflict was recoverable without giving the owner a
recovery action.

HS-93-06 now carries that retained state through one explicit path:

1. `GET /api/meetings/{meeting_id}/sync-conflicts` returns both still-open
   versions.
2. The shared React recovery surface appears inside History and the Meeting's
   Desk pull-out.
3. It names the current desktop and incoming synced-device versions with title,
   capture state, transcript count/latest text, tags, and provenance.
4. The owner chooses `Keep current Meeting` or `Use synced Meeting`; an incoming
   tombstone instead names `Delete this Meeting from this device`.
5. `POST /api/meetings/{meeting_id}/sync-conflicts/{conflict_id}/resolve`
   applies that exact choice. Incoming content replaces the same Meeting
   identity and the resolution record in one SQLite transaction. A tombstone
   deletes only after the destructive choice.

Both non-deletion choices advance the Meeting's sync clock strictly beyond the
contested timestamp, even when that timestamp is ahead of the host clock. The
next sync therefore converges on the owner's decision instead of presenting the
same equal-clock conflict again.

There is no merge-by-guessing and no `Keep both` label. A substituted,
unreadable, already-resolved, or unknown choice refuses while the original
Meeting and retained conflict remain available.

## Second vertical slice: partial intelligence stays partial

Deferred Meeting processing previously had a false-completion branch: base
summary/topics/actions could save successfully, one or more routed plugins could
then block, time out, or fail, and the queue still deleted the job while the
Meeting remained `ready`. The owner saw neither the missing work nor a recovery
choice.

HS-93-06 now keeps the stages distinct:

1. Base analysis persists under an honest running state while routed work is
   unresolved; no transient Ready state is published.
2. Any unresolved plugin leaves the Meeting `partial`, retains transcript,
   base analysis, and artifacts from successful plugins, retains a failed queue
   row, records `partial_failure`, leaves `intel_completed_at` empty, and does
   not broadcast aftercare-ready.
3. A retry recognizes already-successful idempotency keys and executes only the
   failed, timed-out, blocked, or otherwise unresolved plugin keys.
4. `GET /api/meetings/{meeting_id}/intel-recovery` projects saved Meeting,
   transcript, analysis, and artifact facts separately from exact remaining
   work. The same component renders this contract in History and the Meeting's
   Desk pull-out.
5. `POST .../retry` atomically refuses a running worker, recomputes the current
   transcript hash, reuses the same Meeting identity, resets a fresh bounded
   attempt budget, and advances the Meeting sync clock.
6. `POST .../skip` atomically refuses a running worker, deletes only the queue
   remainder, records an idempotent `skipped` audit event, advances the sync
   clock, retains every completed projection, and never writes an intelligence
   completion timestamp.

The legacy queue retry endpoint delegates to the same guarded transition. A
direct repeat of Skip is idempotent and does not create duplicate audit events.
No schema migration or second recovery/receipt system was added.

## Files and contracts

- [`holdspeak/db/meetings.py`](../../../../holdspeak/db/meetings.py) — exact
  conflict read, content-parity verification, and atomic current/incoming
  resolution.
- [`crud.py`](../../../../holdspeak/web/routes/meetings/crud.py) — the typed
  resolution route and fail-closed responses.
- [`MeetingConflictRecovery.tsx`](../../../../web/src/meetings/MeetingConflictRecovery.tsx)
  — one decision surface reused by History and the Desk.
- [`HistoryPage.tsx`](../../../../web/src/pages/HistoryPage.tsx) and
  [`Pullout.tsx`](../../../../web/src/desk/components/Pullout.tsx) — the focused
  archive and source-Meeting entry points.
- [`intel.py`](../../../../holdspeak/db/intel.py),
  [`intel_queue.py`](../../../../holdspeak/intel_queue.py), and
  [`meeting_plugins.py`](../../../../holdspeak/meeting_plugins.py) — atomic
  Retry/Skip, truthful partial lifecycle, sync-clock advancement, and
  unresolved-key-only plugin retry.
- [`meetings/intel.py`](../../../../holdspeak/web/routes/meetings/intel.py) — the
  Meeting-scoped recovery projection and guarded action routes.
- [`MeetingIntelRecovery.tsx`](../../../../web/src/meetings/MeetingIntelRecovery.tsx)
  — one completed/remaining/action surface shared by History and the Desk.
- [`docs/api-surface.json`](../../../../docs/api-surface.json) and
  [`docs/API_SURFACE.md`](../../../../docs/API_SURFACE.md) — regenerated route
  contract, with Web as the declared consumer.

## Production Web implementation evidence

[`phase93_meeting_recovery_evidence.py`](../../../../scripts/phase93_meeting_recovery_evidence.py)
boots a real isolated `MeetingWebServer`, database, and production React bundle.
It seeds a deterministic partial Meeting with two transcript segments, completed
base analysis, one retained artifact, and a timed-out routed plugin. The browser
uses ordinary History/Desk entry and the real GET/POST recovery routes; any
failed API response aborts the run.

| State | Evidence | What it establishes |
|---|---|---|
| History partial state | [completed versus remaining](./evidence/hs-93-06/after-web-history-partial-intelligence.png) | saved transcript/analysis/artifact facts, exact timeout, Retry remaining, and Skip remaining without Ready |
| Desk partial state | [Meeting subject recovery](./evidence/hs-93-06/after-web-desk-partial-intelligence.png) | the same recovery contract is attached to the source Meeting while summary/artifact remain available |
| Owner skips remainder | [skipped state](./evidence/hs-93-06/after-web-desk-intelligence-skipped.png) | completed work remains visible, Skip disappears, Retry remains, and no completed claim appears |
| Owner retries remainder | [queued state](./evidence/hs-93-06/after-web-desk-intelligence-retry.png) | the same Meeting returns to an explicit queued state; duplicate Retry disappears while Skip remains available |

These captures are deterministic production-Web implementation evidence. They
are not a real model-fault walk, owner verdict, native-client proof, or physical
device evidence, so the related acceptance checkbox remains open.

## Verification completed

| Lane | Result |
|---|---|
| Conflict API + meeting durability + DB/sync/projection/API-surface regression lane (first slice) | 116 passed |
| Partial-intelligence DB/queue/plugin/egress/aftercare/API affected lane | 99 passed |
| Full Web `npm --prefix web run check` | architecture guard passed for 113 source files; typecheck passed; 31 files / 161 tests passed; production build passed |
| Declared API-surface snapshot | 310 routes; 5 tests passed; all three new recovery routes are Web-consumed |
| Production recovery evidence runner | History partial, Desk partial, Skip, and Retry passed with zero failed API responses |
| Product-copy census | 3,937 candidates; 0 violations |
| Ruff on changed Python and integration proof | passed |
| Prettier on shared React surfaces and tests | passed |
| Patch hygiene | `git diff --check` passed |

The Vite build retains the existing mixed static/dynamic `ask.ts` chunk
warning. One direct `npm run check` from the `web/` working directory selected a
broken Homebrew Node 25 binary whose removed `libllhttp.9.3` dependency prevents
startup; the documented root invocation selected the working toolchain and
completed the full gate above. This is a host-toolchain issue, not a skipped
product check.

## Acceptance still required

No HS-93-06 acceptance checkbox changes in this slice. Still required:

- owner choices through both production Web entry points; scripted production
  captures now exist but do not replace owner observation;
- the same conflict decision on physical iPhone and iPad, followed by an
  exactly-once cross-device reconciliation;
- 5/30/60-minute native and 5/30/120-minute desktop RSS/checkpoint traces;
- disk-full, permission, route, call/Siri, lock/suspension, kill, relaunch, and
  real partial-model fault walks with visible Recover/Retry/Discard or
  Retry/Skip on Web and native;
- airplane-mode capture and exactly-once sync with transcript timing,
  provenance, partial state, artifacts, and aftercare intact;
- concise failure/capture/sync copy review and owner verdicts with exact
  device/build/audio-route/network provenance.

The next autonomous development slice should add deterministic capture/model
fault hooks and the bounded long-run protocol needed for repeatable physical
Web/iPhone/iPad execution. Simulator, deterministic seed, or synthetic evidence
will not be used to close physical or real-fault acceptance.
