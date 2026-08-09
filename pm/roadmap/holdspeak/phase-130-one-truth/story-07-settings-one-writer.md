# HS-130-07 — Settings, one honest writer: versioned, transient retry

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** HS-130-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

`/api/settings` is last-writer-wins across four independent partial-tree
writers with no version guard (Readiness.tsx:45-48, useSpeakDeck.ts:265-273,
CommandsCore.tsx:63-67, the Prefs debounce) — two open surfaces silently
destroy each other's edits. `CommandsCore.persist` re-sends a whole stale
`items` array on a checkbox toggle (CommandsCore.tsx:60-70) — data loss, not
confusion. Sol pulled this into the truth wave because "Settings owns
persistent preferences" is unenforceable while tabs clobber each other.
Separately, Speak's "Run elsewhere" recovery (useSpeakDeck.ts:263-277)
**persists** the global dictation target before a one-off retry — a transient
recovery silently rewrites a standing preference.

### What changes

1. `/api/settings` writes carry a version/etag; a stale partial-tree PUT is
   rejected, not merged blindly. Concurrent surfaces reconcile rather than
   overwrite.
2. `CommandsCore` stops resending the full `items` array on an enablement
   toggle; the enablement bit is written without carrying stale content.
3. Each persistent preference has **one** writer. The duplicate enablement
   surfaces — Voice Commands (SettingsCore.tsx:495-499 vs CommandsCore.tsx
   :113-118) and dictation pipeline (SettingsCore.tsx:459 vs Readiness.tsx
   :42-53) — show **effective state** on the feature surface and open the
   exact Settings module; only Settings persists.
4. "Run elsewhere" recovery becomes a **transient one-run override** ("Retry
   on", HS-130-01's fourth label), not a persisted write to
   `dictation.runtime.profile_id`.
5. The one-writer guard is an **allowlist per settings subtree keyed on PUT
   callers**, not on controls — so legitimate menu/shortcut/context-menu
   projections of one verb are not false-positived (Sol, "Keep valid layers").

## Acceptance criteria

1. Two surfaces editing different settings subtrees concurrently do not lose
   each other's writes; a stale write is rejected with a reconcilable error.
2. Toggling Commands-enabled does not rewrite macro `items`.
3. Voice-commands and dictation-pipeline enablement each persist from one
   writer; the other surface reflects effective state and links to it.
4. "Run elsewhere" retries on the chosen target for that run only and does not
   change the standing dictation target.
5. The subtree-writer guard passes for verb projections and fails on a genuine
   second persistent writer.

## Test plan

- Web: concurrent-write reconciliation test; CommandsCore no-clobber test;
  effective-state-mirrors-Settings tests; transient-retry test (asserts no
  settings PUT of `runtime.profile_id`); the subtree-writer allowlist guard.
- Backend: `/api/settings` version-guard test.
- `npm --prefix web run test:web -- run` + full backend suite read from file
  before flip.

## Out of scope

- The full "Settings is the only persistent preference writer" sweep across
  every module (issue Wave 1 / Phase 132); this story fixes the data-loss and
  transient-retry defects and establishes the guard.
