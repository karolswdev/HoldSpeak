# Desk density direction

Populated samples use the actual library Button, DeskIcon, SurfaceWell and
standalone SurfaceFooter with actual shell, Screen and Dock CSS and sprites.
The Dock is a declared projection of its current Button markup rather than a
mounted runtime Dock: no live hub/provider reads run. Copy only exposes a
declared sample receipt; it does not access the clipboard. Window chrome and
positions are canvas specimens, not working move/resize controls.

Start from repository root:

```sh
web/node_modules/.bin/vite --config docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/canvas-density/vite.config.mjs
```

Port 4499. Default shows the settled short artifact over the desktop icons and
Dock. `?density=current` uses the current product styles with no candidate
overrides; it is not a frozen baseline. Archived before images are in
`.tmp/feedback/before1440/` and `.tmp/feedback/before393/`.
`?pose=stretched` shows a taller artifact; `?view=icons` exposes all desktop
objects. Combine parameters for layout samples at 1440 and 393.
The phone preserves 56 px Dock/54 px tiles and original art.

Settled direction: desktop Dock 60 px, tiles 52 px, picture row 28 px, sprite 24 px;
desktop Screen art 48 px, badge 24 px, minimum tile height 80 px, drawer rows
96 px and loose rows 100 px. Labels and 112 px tile/120 px column widths stay.
The canvas preserves the existing 24 px caption allowance in placed rows.

Footer: intrinsic grid with minimum 28 px, explicit 4 px vertical padding,
24 px trailing grip reserve and existing 6 px desktop bottom reserve. A local
canvas selector originally previewed the desk-surface-foot class on the actual
standalone SurfaceFooter fallback. The product now supplies that class.
Hosted frames retain one footer and one vertical inset.

Canvas was prepared without product edits or test/build/browser jobs, then
root read it before product implementation on 2026-10-16. It imports the
working product sources and therefore changes when those sources change.
This is declared direction, not proof of runtime behavior or owner acceptance.
