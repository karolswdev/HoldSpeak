# HS-103-01 - Session restoration — the desk remembers it was open

- **Project:** holdspeak
- **Phase:** 103
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The research finding (the bar)

An independent, hands-on audit of the Desk (Opus 4.8, headed-equivalent
Playwright drive against a real staged instance, 2026-07-22) rated it
7/10 "OS-ness" and named this the single highest-leverage gap: *"the
desk remembers where a window goes but not that it was open."*
Verified live — `useSurfaceWindows` (`web/src/desk/components/SurfaceWindows.tsx:199`)
is a plain zustand store with `open: {}` and no persist middleware; after
arranging and reloading, `document.querySelectorAll('.desk-surface-window').length === 0`
even though `hs.desk.panels` (the separate rect/order store,
`web/src/desk/store.ts:35,82,107`) still held the layout. Every reload is
a blank desk the user must manually repopulate — directly contradicting
Constitution Art. VII.3 ("the user's arrangement is sacred and
persists"), which today is honored for pixels and broken for sessions.

A second, related defect from the same audit: `resetLayout()`
(`web/src/desk/store.ts:871`) wipes the rect/order/max maps, but a
currently-open window immediately re-measures and re-persists its own
rect — so Reset Layout is only effective on CLOSED windows, a quiet
trust inconsistency in a system whose whole premise is "your
arrangement is sacred."

## Problem

The window manager persists geometry but not existence. A reload — the
single most common thing that happens to a long-lived local web app —
silently discards the user's entire session. This is the one fix that
converts "a web app that remembers window sizes" into "a desktop that
restores your session."

## Scope

- In: add persistence + rehydration to the open-window set
  (`useSurfaceWindows` in `SurfaceWindows.tsx`, or fold it into the
  existing `hs.desk.panels` blob in `store.ts` — whichever is the
  smaller, more consistent change once the actual store shapes are
  read) so a reload restores exactly the windows that were open, at
  their persisted rects and stacking order. Fix `resetLayout()` so it
  also resets any currently-open window's rect (re-seed to default, or
  close+reopen) instead of leaving it to re-persist stale geometry.
- Out: cross-device or cross-browser sync (the audit correctly notes
  localStorage-only persistence is defensible for a local-first
  posture — not in scope here); minimize-state persistence (already
  deliberately session-scoped, per existing code comments — leave
  alone unless investigation finds it's actually the same bug).

## Acceptance criteria

- [ ] Open 2+ windows, arrange them, reload the page: the same windows
      reopen at the same rects and stacking order, with no manual
      repopulation.
- [ ] Minimize/maximize state either persists or is confirmed
      deliberately session-scoped (name the reason in evidence if it's
      the latter — don't silently change existing intended behavior).
- [ ] With a window open, click Reset Layout: the open window's rect
      resets too (no stale geometry surviving the reset).
- [ ] A regression test (vitest or the existing `shell.test.tsx`/
      window-grammar test suite) pins both behaviors so a future change
      can't silently reintroduce either defect.
- [ ] Driven live on a staged hub, headed, both viewports (1440 + 393):
      screenshot before-reload and after-reload showing identical
      window state.

## Test plan

- Unit: web vitest, extending `web/src/desk/__tests__/window.test.ts`
  (or sibling) with reload-rehydration and reset-with-open-window
  cases.
- Integration: n/a — covered by the vitest store-level tests plus the
  manual/live drive below.
- Manual / device: headed drive on a staged instance
  (`uv run python -m uat.stage --recipe seeded-desk`), both viewports,
  screenshots before/after reload and before/after Reset Layout.

## Notes / open questions

Two plausible implementation shapes exist — (a) add zustand `persist`
middleware directly to `useSurfaceWindows`, or (b) fold `open` into the
`hs.desk.panels` blob `store.ts` already persists, so there's one
source of truth for "what's open and where" instead of two stores that
can drift. Read both files before choosing; prefer (b) if it doesn't
require a disruptive refactor — one persisted blob is easier to keep
honest than two. Record whichever is chosen and why in evidence.
