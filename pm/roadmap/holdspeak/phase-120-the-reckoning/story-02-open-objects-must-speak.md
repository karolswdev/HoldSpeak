# HS-120-02 — Open objects must speak

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Opening a Directory (zone) pullout renders a blank void — no name, no
member list, no empty state, no verbs. Opening an unsupported primitive
kind via FallbackPullout renders an equally empty window. These are the
two surfaces where clicking a real desk object produces no information
and no next action.

When this ships:

1. **DirectoryPullout** shows the zone's name, kind sprite, member
   count, a list of filed members (kind glyph + name, clickable to
   open), and standard footer verbs (Edit, Dictate about this). Empty
   zones show `SurfaceState empty` with "No members" and a guidance
   hint.

2. **FallbackPullout** renders `SurfaceState empty` with the text
   "No detail view for {kind}" and the primitive's kind glyph, so the
   user understands what happened rather than seeing a void.

## Acceptance criteria

- [ ] DirectoryPullout renders name, member count, and member list.
- [ ] DirectoryPullout empty state uses `SurfaceState empty`.
- [ ] DirectoryPullout footer has verbs matching other pullouts.
- [ ] FallbackPullout renders `SurfaceState empty` with kind label.
- [ ] Both render inside `DeskWindowFrame` with proper surface chrome.

## Test plan

- Open a populated directory; verify members render with kind glyphs.
- Open an empty directory; verify empty state.
- Open a primitive with no custom pullout; verify fallback message.

## Files in scope

- `web/src/desk/pullouts/DirectoryPullout.tsx`
- `web/src/desk/pullouts/FallbackPullout.tsx`
