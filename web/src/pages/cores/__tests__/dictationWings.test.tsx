/* HS-176-05 — the Speak window's wings and its footer verb.
   Four wings, always present: SPEAK · JOURNAL · BLOCKS · LEARNED (design
   D2(c)); `Review` reviews — it crosses to the Journal wing, where the
   utterances are, instead of opening the Configure door (design D2(b).9).
   The gear stays the way to Configure. */
import { useState, type ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { DictationCore } from "../DictationCore";
import { WingSlotContext } from "../../../desk/surface/wings";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", () => ({
  ApiError: class ApiError extends Error {},
  apiFetch: mocks.apiFetch,
  newDeliveryId: () => "speak:test",
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../../lib/micSession", () => ({
  subscribeMicPhase: () => () => undefined,
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
}));
vi.mock("../../../lib/openMic", () => ({
  openMicDrop: vi.fn(),
  openMicListen: vi.fn(),
}));
vi.mock("../../../lib/speakToFill", () => ({
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => "",
  retryPendingTranscription: vi.fn(),
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../assignmentExperience", () => ({
  getAssignmentEditor: () => Promise.resolve(null),
}));
vi.mock("../../../features/concierge/api", () => ({
  conciergeDetect: () => Promise.resolve({ engines: [] }),
}));
// `useRuntimeBus` throws outside its provider; both the Journal and the
// Learned wings subscribe (LiveCore.test.tsx's mocking pattern).
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const CORRECTION = {
  id: 3,
  kind: "text",
  key: "queue for",
  value: "Q4",
  applied: 1,
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mocks.apiFetch.mockImplementation((url: string) => {
    const path = String(url);
    if (path.startsWith("/api/dictation/journal"))
      return Promise.resolve({ count: 0, items: [] });
    if (path.startsWith("/api/dictation/corrections"))
      return Promise.resolve({ items: [CORRECTION] });
    if (path.startsWith("/api/dictation/readiness"))
      return Promise.resolve({ target: { overrides: [] } });
    if (path.startsWith("/api/dictation/blocks"))
      return Promise.resolve({ document: { blocks: [] } });
    if (path.startsWith("/api/dictation/learning-digest"))
      return Promise.resolve({ totals: {} });
    return Promise.resolve({});
  });
});

/** Render the core AND the wing bar it publishes into the window head. */
function mount() {
  function Host() {
    // The window frame owns the head; `useWindowWings` bridges the two.
    const [slot, setSlot] = useState<ReactNode>(null);
    return (
      <WingSlotContext.Provider value={setSlot}>
        <div data-testid="window-head">{slot}</div>
        <DictationCore />
      </WingSlotContext.Provider>
    );
  }
  return render(
    <MemoryRouter>
      <Host />
    </MemoryRouter>,
  );
}

describe("the Speak window's wings", () => {
  it("carries FOUR wings — Speak, Journal, Blocks, Learned", async () => {
    mount();
    await waitFor(() =>
      expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
        "Speak",
        "Journal",
        "Blocks",
        "Learned",
      ]),
    );
  });

  it("the Learned wing owns the corrections the door used to hide", async () => {
    mount();
    await userEvent.click(await screen.findByRole("tab", { name: "Learned" }));
    await waitFor(() =>
      expect(document.querySelector(".speak-learned")).toBeTruthy(),
    );
    expect(await screen.findByText("queue for")).toBeTruthy();
    expect(screen.getByText("1 APPLIED")).toBeTruthy();
  });
});

describe("the footer's Review", () => {
  it("crosses to the Journal wing, not the Configure door", async () => {
    mount();
    await screen.findByRole("tab", { name: "Speak" });
    await userEvent.click(screen.getByRole("button", { name: "Review" }));

    await waitFor(() =>
      expect(document.querySelector(".speak-journal")).toBeTruthy(),
    );
    // the door face is NOT what Review opens
    expect(document.querySelector(".surface-door")).toBeNull();
    expect(screen.getByRole("tab", { name: "Journal" }).getAttribute("aria-selected")).toBe(
      "true",
    );
  });

  it("the gear is still the way to Configure", async () => {
    mount();
    await userEvent.click(
      await screen.findByRole("button", { name: "Configure dictation" }),
    );
    await waitFor(() =>
      expect(document.querySelector(".surface-door")).toBeTruthy(),
    );
    // the digest stayed behind the gear; the corrections table did not
    expect(await screen.findByText(/WEEK/)).toBeTruthy();
    expect(document.querySelector(".speak-learned")).toBeNull();
  });
});
