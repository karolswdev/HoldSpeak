// HS-130-07 — "Run elsewhere" is a TRANSIENT one-run override. It retries the
// dry run on the chosen target for THAT run only and NEVER PUTs
// `dictation.runtime.profile_id` to settings (a recovery must not silently
// rewrite the desk's standing target — Settings is that setting's one writer).
import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSpeakDeck } from "../useSpeakDeck";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../../../lib/micSession", () => ({
  subscribeMicPhase: () => () => undefined,
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
}));
vi.mock("../../../../lib/openMic", () => ({
  openMicDrop: vi.fn(),
  openMicListen: vi.fn(),
}));
vi.mock("../../../../desk/shell", () => ({ openSurfaceOr: vi.fn() }));

type Init = { method?: string; json?: any };

function calls(path: string): Init[] {
  return mocks.apiFetch.mock.calls
    .filter((c: unknown[]) => String(c[0]) === path)
    .map((c: unknown[]) => (c[1] ?? {}) as Init);
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mocks.apiFetch.mockResolvedValue({});
});

describe("Run elsewhere is transient (HS-130-07)", () => {
  it("retries the dry run on the chosen target and does NOT PUT settings", async () => {
    const { result } = renderHook(() => useSpeakDeck(() => undefined));
    await act(async () => {
      await result.current.runElsewhere("p-lan");
    });
    // The retry rode the dry-run request carrying the transient target…
    const dryRuns = calls("/api/dictation/dry-run");
    expect(dryRuns).toHaveLength(1);
    expect(dryRuns[0].method).toBe("POST");
    expect(dryRuns[0].json.profile_id).toBe("p-lan");
    // …and the standing target in settings was never rewritten.
    expect(calls("/api/settings").filter((c) => c.method === "PUT")).toEqual([]);
  });

  it("'this_machine' clears the per-run override (null), still no settings PUT", async () => {
    const { result } = renderHook(() => useSpeakDeck(() => undefined));
    await act(async () => {
      await result.current.runElsewhere("this_machine");
    });
    const dryRuns = calls("/api/dictation/dry-run");
    expect(dryRuns).toHaveLength(1);
    expect(dryRuns[0].json.profile_id).toBeNull();
    expect(calls("/api/settings").filter((c) => c.method === "PUT")).toEqual([]);
  });
});
