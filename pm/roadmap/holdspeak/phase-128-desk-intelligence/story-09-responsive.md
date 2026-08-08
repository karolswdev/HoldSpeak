# HS-128-09 — Responsive and mobile behavior

- **Project:** holdspeak
- **Phase:** 128
- **Status:** done
- **Depends on:** HS-128-08
- **Unblocks:** HS-128-10
- **Owner:** unassigned

## The thesis (the bar)

Intelligence remains an OS surface at every width. It contracts through the
same material grammar instead of becoming a narrow desktop page.

### What changes

1. Add `@container` surface queries: column shift at 560px and stacked layout
   at 420px.
2. Render the Pullout as mobile sheet mode on narrow viewports.
3. Allow only one FoldGadget group expanded at a time on narrow screens.
4. Wrap focused-row verb bars into a deliberate second row when space requires.

## Acceptance criteria

1. The full pullout has no horizontal body overflow at 1440px or 393px.
2. 560px and 420px transitions preserve every view's content and controls.
3. Mobile sheet mode retains pullout navigation, focus, and back behavior.
4. Narrow group and verb behavior is deterministic and keyboard reachable.

## Test plan

- Web: exercise container breakpoints and single-expanded-group state.
- Playwright: assert width, sheet mode, wrapped verbs, and no horizontal overflow.
- Visual: record 1440px and 393px screenshots for the three views.
