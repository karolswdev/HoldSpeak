// HS-129-06 — jsdom cannot evaluate CSS container queries, so this census
// proves the window-body contracts in source. The live browser walk verifies
// the resulting narrow layouts at runtime.
import { describe, expect, it } from "vitest";
import deliveryCss from "../components/delivery.css?raw";
import listViewCss from "../components/list-view.css?raw";
import repoWindowCss from "../components/RepoWindow.css?raw";
import roadmapWindowCss from "../components/RoadmapWindow.css?raw";
import windowChromeCss from "../components/window-chrome.css?raw";
import workbenchConfigCss from "../components/workbench-config.css?raw";
import intelligenceCss from "../pullouts/intelligence.css?raw";
import surfaceFooterCss from "../surface/surface-footer.css?raw";
import surfaceCss from "../surface/surface.css?raw";

const cssSources = import.meta.glob<string>("/src/**/*.css", {
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
]);

describe("HS-129-06 container-query law", () => {
  it("makes every migrated room query its named window body", () => {
    expect(deliveryCss).toContain("@container surface (max-width: 520px)");
    expect(intelligenceCss).toContain("@container surface (max-width: 560px)");
    expect(intelligenceCss).toContain("@container surface (max-width: 420px)");
    expect(roadmapWindowCss).toContain("@container surface (max-width: 720px)");
    expect(listViewCss.match(/@container surface \(max-width: 720px\)/g)).toHaveLength(2);

    // The audited Repo breakpoint was removed before this story landed.
    expect(repoWindowCss).not.toMatch(/@media\s*\(\s*(?:max|min)-width/);
  });

  it("uses surface as the sole public container name", () => {
    const migratedCss = [
      windowChromeCss,
      workbenchConfigCss,
      surfaceFooterCss,
      surfaceCss,
      intelligenceCss,
    ].join("\n");

    expect(windowChromeCss).toContain("container-name: surface;");
    expect(migratedCss).not.toContain("@container desk-surface");
    expect(migratedCss).not.toContain("container-name: surface desk-surface");
    expect(migratedCss).not.toMatch(/@container\s*\(/);
  });

  it("keeps viewport-width media limited to shell exceptions", () => {
    for (const [path, css] of Object.entries(cssSources)) {
      if (/@media\s*\(\s*(?:max|min)-width/.test(css)) {
        expect(viewportWidthMediaAllowlist).toContain(path);
      }
    }
  });
});
