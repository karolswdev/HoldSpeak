# HS-119-02 — Integration regression sweep

- **Project:** holdspeak
- **Phase:** 119
- **Status:** backlog
- **Depends on:** --
- **Unblocks:** HS-119-01, HS-119-03, HS-119-04
- **Owner:** unassigned

## The thesis (the bar)

Phase 118 shipped nine stories of new capability. Each story was tested
in isolation. No integration regression was run against the combined
codebase. The presence window freezes on "RECONNECTING". Unknown
breakages may lurk in paths that were working before Phase 118 and
are now broken by side effects of the new code — refactored imports,
changed schemas, new middleware, event handler rewiring.

This story exercises every existing system path against the Phase 118
codebase, documents every regression found, fixes them, and proves the
fixes. It is the foundation for everything else in this phase: the mic
upgrade and seed revision land on a stable baseline, not on unknown
breakage.

**Articles served:** IX (proof over claim — nothing is done because its
code merged; it is done when it ran), VI (honest by construction — a
broken dependency produces a named failure, not a quiet degradation),
VIII (native-grade craft — physics are contracts; once shipped, they are
a floor no change may regress).

## The regression checklist

Every item below is a system path that existed before Phase 118. Each
must be exercised against the current codebase, with the result
documented.

### 1. WebSocket connection

- Auth handshake: connect to `/ws`, verify the connection is
  authenticated and event subscription works.
- Event subscription: subscribe to desk events, verify events arrive
  when desk objects change.
- Reconnection: kill the server, restart, verify the client reconnects
  and resubscribes without user intervention.
- The presence window must not freeze on "RECONNECTING" — it must
  either reconnect or show an honest failure state.

### 2. Presence detection

- Verify the presence system connects and shows activity.
- Verify it does not freeze on "RECONNECTING" indefinitely.
- If the presence system depends on a WebSocket path that changed,
  find the break and fix it.

### 3. Meeting recorder

- Verify start/stop/pause still work via the desk surface.
- Verify a recorded meeting produces a transcript.
- Verify the meeting primitive's sprite state (from HS-118-07)
  reflects recording/idle correctly.

### 4. Dictation hotkey

- Verify the system-level hotkey path still works after the
  `process_transcript` factoring in HS-118-08.
- Press the hotkey, speak, verify corrected text arrives via the
  desktop paste path.
- Verify the learning loop still journals hotkey transcriptions.

### 5. Workbench conductor

- Verify scheduled runs work with the new auto-mint path
  (HS-118-06).
- Verify a conductor run produces artifacts in `pending-review`
  state.
- Verify triage (accept/reject/rework from HS-118-09) still works
  on conductor-produced output.

### 6. Kernel operations

- Verify all registered codecs admit and receipt correctly:
  `workbench_mint`, `workbench_triage`, `voice_reference_resolve`,
  and any others registered in the effect ledger.
- Verify kernel admission produces terminal receipts.
- Verify refusal produces a named refusal receipt.

### 7. Seed and schema

- Verify the seed does not crash on the current schema (v37 or
  whatever the current version is after Phase 118 migrations).
- Verify a clean DB migration from a recent schema version
  (pre-Phase 118) to the current version completes without error.
- Verify the seed creates objects that are valid DeskPrimitives
  under the current schema.

### 8. Inlet and @-references

- Verify the inlet (HS-118-03) accepts typed input, dropped objects,
  and voice input.
- Verify @-autocomplete (HS-118-04) resolves zone names.
- Verify voice drawer resolution (HS-118-05) resolves spoken
  references.

## Deliverables

1. **Run every item on the checklist.** Document the result of each:
   pass, fail (with description of the failure), or degraded (works
   but with observable issues).

2. **Fix every regression found.** Each fix is a targeted repair, not
   a rewrite. The fix addresses the specific breakage without
   introducing new behavior.

3. **Prove every fix.** Each fixed regression is re-tested and the
   passing result is documented in evidence.

4. **Regression test additions.** For each regression found, add a
   test that would have caught it. These tests become part of the
   permanent suite — they prevent the same regression from recurring.

## What NOT to do

- Do NOT add new features during the regression sweep. This story
  fixes what broke; it does not improve what works.
- Do NOT rewrite systems that pass the regression check, even if
  they could be better. Refactoring is a different story.
- Do NOT skip a checklist item because "it probably works." Run it.
  (Article IX.)

## Test plan

- `uv run pytest -q` — full test suite passes (baseline).
- `npx vitest run` — full frontend test suite passes (baseline).
- Each checklist item above is exercised and documented in evidence.
- Each regression fix is re-tested and passes.
- New regression tests are added and pass.
- Evidence captures via DW for every checklist item.
