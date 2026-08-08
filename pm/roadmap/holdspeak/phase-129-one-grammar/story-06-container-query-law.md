# HS-129-06 — The container-query law

- **Project:** holdspeak
- **Phase:** 129
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

The window is the viewport (HS-98-01). Room content must reflow against its
window's width (`@container surface`), never the browser's — a narrow window
in a wide browser must lay out narrow. Audit D §4 found six rooms breaking
the law with viewport media queries, and an undocumented `desk-surface`
container alias.

### What changes

1. Migrate to `@container surface`: delivery.css:337 (520px),
   pullouts/intelligence.css:263,568 (420/560px), RepoWindow.css:25,
   RoadmapWindow.css:28, and the content portions of
   list-view.css:85,147,290 (720px).
2. Legitimate viewport media stays: all `prefers-reduced-motion`,
   `pointer: coarse`, and the 720px SHELL/sheet rules (dock.css,
   chrome-menus.css:766, attention.css:186,263, session-pullout.css:146).
3. Standardize the container name: `surface` everywhere;
   the `desk-surface` alias (window-chrome.css:338-350) is removed after
   its two consumers (surface-footer.css:45, workbench-config.css:572)
   migrate; the three anonymous `@container` queries get the name.

## Acceptance criteria

1. A 460 px-wide window in a 1440 px browser renders the narrow layout for
   each migrated room; the same window maximized renders wide.
2. `grep "@media" web/src` shows only reduced-motion, coarse-pointer,
   shell/sheet, and route-shell (react-app.css) queries.
3. `grep "desk-surface" web/src/**/*.css` returns nothing; every named
   `@container` reference resolves to `surface`.

## Test plan

- Web: container-reflow test per migrated room (narrow window, wide
  viewport); typecheck + build.
- Walk: each migrated room shot twice at 1440 viewport — once at minimum
  window width, once maximized — layouts visibly differ correctly.
