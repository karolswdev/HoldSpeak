// HS-129-06 — the container-query law (docs/internal/UX-CANON.md §D): 393
// stacks under the `surface` container, never viewport media. This ratchet
// keeps viewport-width media to the named shell exceptions; the desk sweep
// (tests/e2e/test_desk_sweep.py, fit and clipped at 393) proves the layouts.
import { describe, expect, it } from "vitest";

// Parked faces are retained history, as in the canon scanner. Their old
// viewport rules do not grant an exception to an active window body.
const cssSources = import.meta.glob<string>(["/src/**/*.css", "!/src/**/_parked/**/*.css"], {
  eager: true,
  import: "default",
  query: "?raw",
});

const viewportWidthMediaAllowlist = new Set([
  "/src/design/atmosphere-preview.css", // standalone Vite-only viewport shell, never a Desk window body
  "/src/desk/chair/chair.css", // Chair is shell furniture around its lanes
  "/src/desk/components/attention.css",
  "/src/desk/components/chrome-menus.css",
  "/src/desk/components/dock.css",
  "/src/desk/components/list-view.css", // desk-floor shell chip
  "/src/desk/components/pullout.css", // fixed mobile thought-context sheet
  "/src/desk/components/session-pullout.css",
  "/src/desk/pullouts/intelligence.css", // phone sheet shell
  "/src/desk/thought-workspace/thought-workspace.css", // full-viewport mobile workspace shell
  "/src/styles/react-app.css", // route shell
  // HS-202-05 (the type-scale ruling, §3 rule 4): the ONE viewport block
  // in global.css gives every library Button a 44px hit area at the
  // narrow desk. The area belongs to the device, not to a window body,
  // and most Buttons at 393 (the dock, the menu bar, the Chair shell,
  // the first-use pages) sit outside every named `surface` container, so
  // a container query cannot reach them. chair.css carries the same
  // exception for the same reason (chair.css:566).
  "/src/styles/global.css",
]);

describe("HS-129-06 container-query law", () => {
  it("keeps viewport-width media limited to shell exceptions", () => {
    expect(cssSources).toHaveProperty("/src/styles/global.css");
    for (const [path, css] of Object.entries(cssSources)) {
      if (/@media\s*\(\s*(?:max|min)-width/.test(css)) {
        expect(viewportWidthMediaAllowlist).toContain(path);
      }
    }
  });
});
