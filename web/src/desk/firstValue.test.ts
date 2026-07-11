import { describe, expect, it, vi } from "vitest";
import { FirstValueTracker } from "./firstValue";

describe("FirstValueTracker", () => {
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
