import { describe, expect, it, vi } from "vitest";
import {
  FirstValueTracker,
  takeFirstValueNoteOpen,
} from "./firstValue";

describe("FirstValueTracker", () => {
  it("keeps the one note id in local storage through an ambiguous response or relaunch", async () => {
    localStorage.removeItem("hs.first-value.keep-note-id");
    vi.resetModules();
    const firstValueBeforeReload = await import("./firstValue");
    const first = firstValueBeforeReload.firstValueKeepNoteId();
    expect(localStorage.getItem("hs.first-value.keep-note-id")).toBe(first);
    vi.resetModules();
    const firstValueAfterReload = await import("./firstValue");
    const afterReload = firstValueAfterReload.firstValueKeepNoteId();
    expect(first).toMatch(/^note_/);
    expect(afterReload).toBe(first);
    firstValueAfterReload.clearFirstValueKeepNoteId();
  });

  it("consumes a staged first-value note only once", () => {
    sessionStorage.setItem("hs.first-value.pending-note-open", "note:n1");
    expect(takeFirstValueNoteOpen()).toBe("note:n1");
    expect(takeFirstValueNoteOpen()).toBeNull();
  });

  it("derives mechanics from bounded events and never posts fixed counters or phrase content", async () => {
    const fetcher = vi.fn(async (path: string, _init?: unknown) =>
      path.endsWith("/start")
        ? { attempt: { id: "attempt-1" } }
        : { success: true },
    );
    const tracker = new FirstValueTracker(fetcher as never);

    await tracker.start("this_machine");
    await tracker.event("capture_started");
    await tracker.event("capture_released");
    await tracker.event("transcript_received");
    await tracker.finish("success");

    const finish = fetcher.mock.calls.find(([path]) =>
      String(path).endsWith("/finish"),
    );
    expect(finish?.[1]).toEqual({
      method: "POST",
      json: { outcome: "success", destination: "this_machine" },
    });
    const wire = JSON.stringify(fetcher.mock.calls);
    expect(wire).not.toContain("steps");
    expect(wire).not.toContain("decisions");
    expect(wire).not.toContain("phrase");
    expect(wire).not.toContain('transcript"');
  });
});
