import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DictationCore } from "./cores/DictationCore";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  startStreamSession: vi.fn(),
}));

vi.mock("../lib/api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
      public payload: unknown = {},
    ) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    ApiError,
    apiFetch: mocks.apiFetch,
    newDeliveryId: () =>
      `speak:${Date.now()}-${Math.random().toString(36).slice(2)}`,
    readableError: (error: unknown) =>
      error instanceof Error ? error.message : "Request failed",
  };
});

vi.mock("../lib/pendingVoice", () => ({
  loadPendingVoice: vi.fn().mockResolvedValue(null),
  savePendingVoice: vi.fn(),
  clearPendingVoice: vi.fn(),
}));

vi.mock("../lib/speakToFill", () => ({
  cancelCapture: vi.fn(),
  closeMicInterval: vi.fn().mockResolvedValue(undefined),
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => null,
  startCapture: mocks.startCapture,
  stopAndTranscribe: mocks.stopAndTranscribe,
  retryPendingTranscription: vi.fn().mockResolvedValue(null),
  subscribeCaptureLevel: () => () => undefined,
}));

vi.mock("../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
}));

import { ApiError } from "../lib/api";

function mockRoutes(routes: Record<string, (init?: { method?: string; json?: unknown }) => Promise<unknown>> = {}) {
  mocks.apiFetch.mockImplementation(
    (path: string, init?: { method?: string; json?: unknown }) => {
      for (const [prefix, handler] of Object.entries(routes))
        if (path === prefix || path.startsWith(prefix)) return handler(init);
      return Promise.resolve({});
    },
  );
}

/** Click-to-toggle: click to start, then click to stop. */
async function clickToggle(talk: HTMLElement) {
  fireEvent.click(talk);
  await waitFor(() => expect(talk).toHaveAttribute("aria-pressed", "true"));
  fireEvent.click(talk);
}

// HS-170-04 — the old run row with Deliver/Rehearse/Retry/Copy/Keep-as-Note
// is replaced by the TALK-release + OK/Wrong + teach flow. These tests now
// exercise the deck's failure paths through the TALK release cycle, and
// verify that the DRY RUN toggle routes through the dry-run endpoint.

describe("DictationPage failure and rehearsal flows (HS-170-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mocks.startCapture.mockResolvedValue(undefined);
    mocks.stopAndTranscribe.mockResolvedValue("A draft that must not disappear.");
    const stopFn = vi.fn().mockResolvedValue("A draft that must not disappear.");
    mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
    mockRoutes();
  });

  it("rehearses through the dry-run when DRY RUN is toggled on", async () => {
    mockRoutes({
      "/api/dictation/dry-run": () =>
        Promise.resolve({ final_text: "ship it friday", total_ms: 120 }),
    });
    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    const talk = await screen.findByRole("button", { name: "Talk" });
    // Toggle DRY RUN on
    fireEvent.click(screen.getByRole("checkbox", { name: "DRY RUN" }));

    await clickToggle(talk);

    await waitFor(() => {
      const calls = mocks.apiFetch.mock.calls.filter(
        (c: unknown[]) => c[0] === "/api/dictation/dry-run",
      );
      expect(calls.length).toBe(1);
    });
    // No real delivery happened
    const remoteCalls = mocks.apiFetch.mock.calls.filter(
      (c: unknown[]) => c[0] === "/api/dictation/remote",
    );
    expect(remoteCalls.length).toBe(0);
    expect(await screen.findByText("REHEARSED · NOT DELIVERED")).toBeVisible();
  });

  it("announces a timeout failure in the receipt channel", async () => {
    mocks.stopAndTranscribe.mockRejectedValue(new ApiError(504, "timeout", {}));
    const stopFn = vi.fn().mockRejectedValue(new ApiError(504, "timeout", {}));
    mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    const talk = await screen.findByRole("button", { name: "Talk" });

    await clickToggle(talk);

    expect(await screen.findByText(/Transcription timed out/)).toBeVisible();
    // No dialog — failures land in-flow
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("announces a conflict failure in the receipt channel", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.reject(new ApiError(409, "conflict", {})),
    });
    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    const talk = await screen.findByRole("button", { name: "Talk" });

    await clickToggle(talk);

    await waitFor(() => {
      const receipts = screen.queryAllByRole("alert");
      const statuses = screen.queryAllByRole("status");
      const all = [...receipts, ...statuses];
      expect(all.length).toBeGreaterThan(0);
    });
  });

  it("announces a rejected token failure in the receipt channel", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.reject(new ApiError(401, "bad token", {})),
    });
    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    const talk = await screen.findByRole("button", { name: "Talk" });

    await clickToggle(talk);

    await waitFor(() => {
      const receipts = screen.queryAllByRole("alert");
      const statuses = screen.queryAllByRole("status");
      const all = [...receipts, ...statuses];
      expect(all.length).toBeGreaterThan(0);
    });
  });
});
