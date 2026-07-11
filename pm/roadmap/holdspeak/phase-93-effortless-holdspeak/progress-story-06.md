# HS-93-06 progress record — A meeting survives real life

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `ebcf8da7`<br>
**After build:** current `agent/hs-93-06-meeting-survives-real-life` working
tree; no commit identity claimed<br>
**Acceptance status:** in progress — the owner-visible Web/Hub conflict
recovery slice is implemented and automatically verified. Long captures,
faults, partial intelligence, offline sync, owner observation, and physical
iPhone/iPad evidence remain open.

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
- [`docs/api-surface.json`](../../../../docs/api-surface.json) and
  [`docs/API_SURFACE.md`](../../../../docs/API_SURFACE.md) — regenerated route
  contract, with Web as the declared consumer.

## Verification completed

| Lane | Result |
|---|---|
| Conflict API + meeting durability + DB/sync/projection/API-surface regression lane | 116 passed |
| Full Web `npm --prefix web run check` | architecture guard passed for 111 source files; typecheck passed; 30 files / 158 tests passed; production build passed |
| Product-copy census | 3,930 candidates; 0 violations |
| Ruff on changed Python and integration proof | passed |
| Prettier on the new shared React component and tests | passed |
| Patch hygiene | `git diff --check` passed |

The Vite build retains the existing mixed static/dynamic `ask.ts` chunk
warning. One direct `npm run check` from the `web/` working directory selected a
broken Homebrew Node 25 binary whose removed `libllhttp.9.3` dependency prevents
startup; the documented root invocation selected the working toolchain and
completed the full gate above. This is a host-toolchain issue, not a skipped
product check.

## Acceptance still required

No HS-93-06 acceptance checkbox changes in this slice. Still required:

- production captures and an owner choice through both Web entry points;
- the same conflict decision on physical iPhone and iPad, followed by an
  exactly-once cross-device reconciliation;
- 5/30/60-minute native and 5/30/120-minute desktop RSS/checkpoint traces;
- disk-full, permission, route, call/Siri, lock/suspension, kill, relaunch, and
  partial-model fault walks with visible Recover/Retry/Discard or Retry/Skip;
- airplane-mode capture and exactly-once sync with transcript timing,
  provenance, partial state, artifacts, and aftercare intact;
- concise failure/capture/sync copy review and owner verdicts with exact
  device/build/audio-route/network provenance.

The next autonomous development slice should make partial intelligence state
and Retry remaining/Skip explicit on the Meeting subject, then add deterministic
fault hooks for the physical fault protocol. Simulator or synthetic evidence
will not be used to close the story.
