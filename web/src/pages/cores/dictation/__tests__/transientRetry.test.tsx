// HS-143-13 — Dictation uses the canonical assignment at admission. The former
// one-run target picker is intentionally absent: recovery never authorizes a
// browser-selected route or rewrites settings.
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

type Init = { method?: string; json?: Record<string, unknown> };

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

describe("Dictation recovery uses assignments", () => {
  it("posts an ordinary dry run without a raw profile override or settings write", async () => {
    const { result } = renderHook(() => useSpeakDeck(() => undefined));
    await act(async () => { await result.current.run("retry this"); });

    const dryRuns = calls("/api/dictation/dry-run");
    expect(dryRuns).toHaveLength(1);
    expect(dryRuns[0].method).toBe("POST");
    expect(dryRuns[0].json).toMatchObject({ utterance: "retry this" });
    expect(dryRuns[0].json).not.toHaveProperty("profile_id");
    expect(calls("/api/settings").filter((c) => c.method === "PUT")).toEqual([]);
  });

  it("does not expose a one-run route writer", () => {
    const { result } = renderHook(() => useSpeakDeck(() => undefined));
    expect(result.current).not.toHaveProperty("runElsewhere");
    expect(result.current).not.toHaveProperty("targetId");
    expect(result.current).not.toHaveProperty("targets");
  });
});
