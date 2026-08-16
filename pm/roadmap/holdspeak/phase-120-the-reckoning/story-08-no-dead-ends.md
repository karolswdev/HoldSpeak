# HS-120-08 — No dead ends

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Three surfaces present dead-end states to the user:

1. **RepoWindow Issues tab** (`RepoWindow.tsx:198`): A wing tab that
   renders a bare `<h3>GitHub Issues</h3>` and a `<p>` saying "gh CLI
   issue integration is pending." This is a developer TODO exposed to
   the user. It should use `SurfaceState empty` or the tab should be
   removed until implemented.

2. **PrefStatusBar DEFAULTS button**
   (`settingsPrefs.tsx:395-400`): A permanently disabled button with
   `title="defaults source pending"`. Every Settings footer shows a
   greyed-out button advertising unfinished work. Remove it until
   implemented.

3. **KbPullout wrong empty label** (`KbPullout.tsx:60`): Says "Empty
   note" for a knowledge entry. Copy-paste from NotePullout.

When this ships, no surface in the app presents an unfinished TODO
as user-facing text, and empty state labels match their primitive kind.

## Acceptance criteria

- [ ] Repo Issues tab: uses `SurfaceState empty` with a meaningful
      label, OR the tab is removed until implemented.
- [ ] DEFAULTS button: removed from the footer entirely.
- [ ] KbPullout empty label: says "No entries" or "Empty knowledge
      entry", not "Empty note".

## Test plan

- Open a repo window, navigate to Issues tab, verify no bare TODO text.
- Open Settings, verify no disabled DEFAULTS button in footer.
- Open an empty knowledge entry, verify label matches kind.

## Files in scope

- `web/src/desk/components/RepoWindow.tsx`
- `web/src/pages/cores/settingsPrefs.tsx`
- `web/src/desk/pullouts/KbPullout.tsx`
