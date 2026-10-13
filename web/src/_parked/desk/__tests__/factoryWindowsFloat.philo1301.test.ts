/** PHILO-13-01 B0-F3 + roadmap.window — every factory window floats.
 * The Roadmap and Repository windows wore no `desk-pullout`, so nothing
 * gave them `position: fixed`. Their inset was ignored, they flowed below
 * the Desk (y 860 at 1440 x 900) and the page grew past the screen.
 * Each window the store opens through windowFactory must wear the class
 * that positions it. */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(new URL(path, import.meta.url), "utf8");
}

const FACTORY_WINDOWS = {
  ZoneWindow: "desk-zone-window",
  InfoWindow: "desk-info-window",
  RoadmapWindow: "desk-roadmap-window",
  RepoWindow: "desk-repo-window",
  WorkbenchWindow: "desk-workbench-window",
};

describe("factory windows float", () => {
  it("the pullout class is the one that positions a window", () => {
    expect(source("../components/pullout.css")).toMatch(
      /\.desk-next \.desk-pullout \{\s*position: fixed;/,
    );
  });

  for (const [file, cls] of Object.entries(FACTORY_WINDOWS)) {
    it(`${file} wears desk-pullout`, () => {
      const host = source(`../components/${file}.tsx`).match(
        new RegExp(`className="([^"]*\\b${cls}\\b[^"]*)"`),
      );
      expect(host, `${file} has no ${cls} host`).not.toBeNull();
      expect(host![1].split(/\s+/)).toContain("desk-pullout");
    });
  }
});
