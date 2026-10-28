import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createFreshBuild,
  deskHasUnsavedEdit,
  RELOAD_STAMP,
  resetFreshBuildForTests,
  startFreshBuild,
  watchChunk,
  type FreshBuildPhase,
} from "../freshBuild";
import { useDesk } from "../../desk/store";
import { act, render, screen } from "@testing-library/react";
import { createElement } from "react";
import { FreshBuildBar } from "../FreshBuildBar";
import { noteChunkFailure } from "../freshBuild";

vi.mock("../../lib/api", () => ({ apiFetch: vi.fn() }));
import { apiFetch } from "../../lib/api";

function memoryStorage() {
  const map = new Map<string, string>();
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => void map.set(key, value),
  };
}

function rig(builds: string[], unsaved = false) {
  const queue = [...builds];
  const phases: FreshBuildPhase[] = [];
  const reload = vi.fn();
  const storage = memoryStorage();
  const fresh = createFreshBuild({
    readBuild: async () => queue.shift() ?? builds[builds.length - 1],
    reload,
    hasUnsavedEdit: () => unsaved,
    storage,
    onPhase: (phase) => phases.push(phase),
    delayMs: 10,
  });
  return { fresh, phases, reload, storage };
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  resetFreshBuildForTests();
});

describe("fresh build", () => {
  it("does nothing when the hub serves the same build", async () => {
    const { fresh, phases, reload } = rig(["aaa", "aaa"]);
    await fresh.start();
    await fresh.check();
    vi.advanceTimersByTime(1000);
    expect(fresh.known()).toBe("aaa");
    expect(phases).toEqual([]);
    expect(reload).not.toHaveBeenCalled();
  });

  it("reloads once on a new build, after the reloading word", async () => {
    const { fresh, phases, reload, storage } = rig(["aaa", "bbb", "bbb"]);
    await fresh.start();
    await fresh.check();
    expect(phases).toEqual(["reloading"]);
    expect(reload).not.toHaveBeenCalled();
    vi.advanceTimersByTime(10);
    expect(reload).toHaveBeenCalledTimes(1);
    expect(storage.getItem(RELOAD_STAMP)).toBe("bbb");
    await fresh.check();
    vi.advanceTimersByTime(1000);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("shows the bar and does not reload while an edit is unsaved", async () => {
    const { fresh, phases, reload, storage } = rig(["aaa", "bbb"], true);
    await fresh.start();
    await fresh.check();
    vi.advanceTimersByTime(1000);
    expect(phases).toEqual(["offer"]);
    expect(reload).not.toHaveBeenCalled();
    fresh.reloadNow();
    expect(reload).toHaveBeenCalledTimes(1);
    expect(storage.getItem(RELOAD_STAMP)).toBe("bbb");
  });

  it("refuses a second reload for the same build", async () => {
    const { fresh, phases, reload, storage } = rig(["aaa", "bbb"]);
    storage.setItem(RELOAD_STAMP, "bbb");
    await fresh.start();
    await fresh.check();
    vi.advanceTimersByTime(1000);
    expect(phases).toEqual([]);
    expect(reload).not.toHaveBeenCalled();
  });

  it("reads the build again on a preload error, then reloads", async () => {
    const answers = ["aaa", "bbb"];
    vi.mocked(apiFetch).mockImplementation(async () => ({ bundle_on_disk: answers.shift() ?? "bbb" }));
    const reload = vi.fn();
    window.sessionStorage.removeItem(RELOAD_STAMP);
    const phases: FreshBuildPhase[] = [];
    const fresh = startFreshBuild((phase) => phases.push(phase), { reload, delayMs: 10 });
    await vi.waitFor(() => expect(fresh.known()).toBe("aaa"));
    window.dispatchEvent(new Event("vite:preloadError"));
    await vi.waitFor(() => expect(phases).toEqual(["reloading"]));
    vi.advanceTimersByTime(1000);
    expect(reload).toHaveBeenCalledTimes(1);
    expect(apiFetch).toHaveBeenCalledWith("/api/system/identity");
  });

  it("a failed lazy load asks again and still throws", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ bundle_on_disk: "aaa" });
    const fresh = startFreshBuild(() => {});
    await vi.waitFor(() => expect(fresh.known()).toBe("aaa"));
    const check = vi.spyOn(fresh, "check");
    const load = watchChunk(() => Promise.reject(new Error("Failed to fetch dynamically imported module")));
    await expect(load()).rejects.toThrow("dynamically imported");
    expect(check).toHaveBeenCalledTimes(1);
  });

  it("a Note's unkept edit and a focused field with words count as unsaved", () => {
    expect(deskHasUnsavedEdit()).toBe(false);
    useDesk.getState().setDraft("editor/note/n1", "{\"body\":\"x\"}");
    expect(deskHasUnsavedEdit()).toBe(true);
    useDesk.getState().setDraft("editor/note/n1", null);
    const area = document.createElement("textarea");
    document.body.append(area);
    area.focus();
    expect(deskHasUnsavedEdit()).toBe(false);
    area.value = "a question for Ask";
    expect(deskHasUnsavedEdit()).toBe(true);
    area.remove();
  });

  it("draws the kit bar with the Reload Button when an edit holds the reload", async () => {
    vi.useRealTimers();
    window.sessionStorage.removeItem(RELOAD_STAMP);
    const answers = ["aaa", "bbb"];
    vi.mocked(apiFetch).mockImplementation(async () => ({ bundle_on_disk: answers.shift() ?? "bbb" }));
    render(createElement(FreshBuildBar));
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalled());
    const area = document.createElement("textarea");
    document.body.append(area);
    area.value = "unsaved words";
    area.focus();
    await act(async () => {
      noteChunkFailure();
      await Promise.resolve();
    });
    expect(await screen.findByText("New desk build")).toBeInTheDocument();
    expect(screen.getByTestId("fresh-build-reload")).toHaveTextContent("Reload");
    area.remove();
  });
});
