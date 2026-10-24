import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { bandFor, inside } from "../compositor/geometry";
import { workBand } from "../components/window/windowGeometry";

const KEY = "hs.desk.workspace.v1";
const saved = () => JSON.parse(localStorage.getItem(KEY) || "{}");
const reload = async () => {
  vi.resetModules();
  return (await import("../store")).useDesk;
};

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
});
afterEach(() => vi.unstubAllGlobals());

describe("repository window instances", () => {
  it("raises the default view on Open and closes only the named extra view", async () => {
    const desk = await reload();
    desk.getState().openRepositoryWindow("repo-1");
    const first = desk.getState().openNewRepositoryWindow("repo-1", undefined, "src");
    const second = desk.getState().openNewRepositoryWindow("repo-1", undefined, "docs");
    desk.getState().openRepositoryWindow("repo-1");

    expect(first).toMatch(/^view:[A-Za-z0-9_-]+$/);
    expect(second).not.toBe(first);
    expect(desk.getState().repositoryWindows.map((w) => w.id)).toEqual(["repo-1", first, second]);
    expect(desk.getState().panelOrder.at(-1)).toBe("repository:repo-1");
    expect(saved().windows.repository).toEqual(["repo-1", first, second]);
    expect(saved().repositoryViews[first]).toEqual({ resourceId: "repo-1", initialPath: "src" });

    desk.getState().closeRepositoryWindow(first);
    expect(desk.getState().repositoryWindows.map((w) => w.id)).toEqual(["repo-1", second]);
    expect(saved().repositoryViews[first]).toBeUndefined();
    const fresh = await reload();
    expect(fresh.getState().repositoryWindows).toEqual([
      { id: "repo-1", origin: null },
      { id: second, resourceId: "repo-1", initialPath: "docs", origin: null },
    ]);
  });

  it("restores a legacy string-list default repository without a resource map", async () => {
    const desk = await reload();
    desk.getState().openRepositoryWindow("repo-legacy");
    const document = saved();
    delete document.repositoryViews;
    localStorage.setItem(KEY, JSON.stringify(document));
    const fresh = await reload();
    expect(fresh.getState().repositoryWindows).toEqual([{ id: "repo-legacy", origin: null }]);
  });

  it("seats a sibling beside its source without moving the source", async () => {
    const desk = await reload();
    const source = { x: 80, y: 90, w: 700, h: 500 };
    desk.getState().openRepositoryWindow("repo-1");
    desk.getState().setPanelRect("repository:repo-1", source, true);
    const extra = desk.getState().openNewRepositoryWindow("repo-1", undefined, "docs", "repository:repo-1");

    expect(desk.getState().panelRects[`repository:${extra}`]).toEqual({ x: 112, y: 122, w: 700, h: 500 });
    expect(desk.getState().panelRects["repository:repo-1"]).toEqual(source);
    expect(saved().panel.rects[`repository:${extra}`]).toEqual({ x: 112, y: 122, w: 700, h: 500 });
  });

  it("uses the rendered source seat when it has no store rect yet", async () => {
    vi.stubGlobal("innerWidth", 1440);
    vi.stubGlobal("innerHeight", 900);
    const desk = await reload();
    desk.getState().openRepositoryWindow("repo-1");
    const frame = document.createElement("div");
    frame.id = "repository:repo-1";
    frame.getBoundingClientRect = () => ({
      x: 688, y: 36, left: 688, top: 36, width: 600, height: 804,
      right: 1288, bottom: 840, toJSON: () => ({}),
    });
    document.body.append(frame);
    try {
      const extra = desk.getState().openNewRepositoryWindow("repo-1", undefined, "src", frame.id);
      const sibling = desk.getState().panelRects[`repository:${extra}`];
      expect(sibling.x).toBeGreaterThanOrEqual(712);
      expect(desk.getState().panelRects[frame.id]).toBeUndefined();
    } finally {
      frame.remove();
    }
  });

  it("fits a sibling inside a narrow work area without changing its source", async () => {
    vi.stubGlobal("innerWidth", 393);
    vi.stubGlobal("innerHeight", 852);
    const desk = await reload();
    const source = { x: 800, y: 500, w: 720, h: 600 };
    desk.getState().openRepositoryWindow("repo-1");
    desk.getState().setPanelRect("repository:repo-1", source, true);
    const extra = desk.getState().openNewRepositoryWindow("repo-1", undefined, "docs", "repository:repo-1");

    const sibling = desk.getState().panelRects[`repository:${extra}`];
    expect(inside(sibling, bandFor(393, 852, workBand()))).toBe(true);
    expect(desk.getState().panelRects["repository:repo-1"]).toEqual(source);
  });
});
