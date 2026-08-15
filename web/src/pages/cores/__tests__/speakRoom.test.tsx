// HS-112-02 — the room named Speak performs the flagship act.
//
// Hold TALK, talk, release: the transcript goes through the REAL delivery
// contract (`POST /api/dictation/remote`) with one `delivery_id` per
// utterance, aimed by the deck's AIM row. THIS FIELD short-circuits to
// speak-to-fill; REHEARSE is the explicit dry run and delivers nothing.
// Every refusal lands in the footer receipt bar and the STATE register —
// never a toast, never an overlay.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DictationCore } from "../DictationCore";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  startStreamSession: vi.fn(),
}));

vi.mock("../../../lib/api", () => {
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

vi.mock("../../../lib/pendingVoice", () => ({
  loadPendingVoice: vi.fn().mockResolvedValue(null),
  savePendingVoice: vi.fn(),
  clearPendingVoice: vi.fn(),
}));

vi.mock("../../../lib/speakToFill", () => ({
  cancelCapture: vi.fn(),
  closeMicInterval: vi.fn().mockResolvedValue(undefined),
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => null,
  startCapture: mocks.startCapture,
  stopAndTranscribe: mocks.stopAndTranscribe,
  retryPendingTranscription: vi.fn().mockResolvedValue(null),
  subscribeCaptureLevel: () => () => undefined,
}));

vi.mock("../../../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
}));

import { ApiError } from "../../../lib/api";

type Route = (init?: { method?: string; json?: unknown }) => Promise<unknown>;

function mockRoutes(routes: Record<string, Route> = {}) {
  mocks.apiFetch.mockImplementation(
    (path: string, init?: { method?: string; json?: unknown }) => {
      for (const [prefix, handler] of Object.entries(routes))
        if (path === prefix || path.startsWith(prefix)) return handler(init);
      return Promise.resolve({});
    },
  );
}

/** Every call the deck made to one route, newest last. */
function callsTo(path: string): { method?: string; json?: any }[] {
  return mocks.apiFetch.mock.calls
    .filter((call: unknown[]) => String(call[0]).startsWith(path))
    .map((call: unknown[]) => (call[1] ?? {}) as { method?: string; json?: any });
}

async function openDeck() {
  render(
    <MemoryRouter>
      <DictationCore />
    </MemoryRouter>,
  );
  return screen.findByRole("button", { name: "Speak" });
}

/** Click-to-toggle: click to start, then click to stop. */
async function clickToggle(talk: HTMLElement) {
  fireEvent.click(talk);
  await waitFor(() => expect(talk).toHaveAttribute("aria-pressed", "true"));
  fireEvent.click(talk);
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  mocks.startCapture.mockResolvedValue(undefined);
  mocks.stopAndTranscribe.mockResolvedValue("ship it friday");
  const stopFn = vi.fn().mockResolvedValue("ship it friday");
  mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
  mockRoutes();
});

describe("Speak delivers for real (HS-112-02)", () => {
  it("posts a released utterance through the delivery contract with one delivery id", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: true, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(1));
    const [call] = callsTo("/api/dictation/remote");
    expect(call.method).toBe("POST");
    expect(call.json.text).toBe("ship it friday");
    expect(call.json.target_mode).toBe("focused");
    expect(String(call.json.delivery_id)).toMatch(/^speak:/);
    // FOCUSED APP is not an aimed-agent send: no agent requirement rides along.
    expect(call.json.require_agent).toBeUndefined();
    // the dry run is NOT what a release does any more
    expect(callsTo("/api/dictation/dry-run")).toHaveLength(0);
  });

  it("shows release-to-landed latency on the footer receipt and the register", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: true, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    const receipt = await screen.findByText(/^LANDED \d+ MS -> FOCUSED APP$/);
    expect(receipt).toBeVisible();
    const register = screen.getByLabelText("Dictation state");
    const landed = Array.from(
      register.querySelectorAll(".speak-register-token"),
    ).find((token) => token.textContent === "Landed");
    expect(landed).toHaveAttribute("data-active");
    expect(screen.getByLabelText("Landed latency").textContent).toMatch(/ MS$/);
  });

  it("mints a fresh delivery id for each utterance", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: true, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);
    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(1));
    await clickToggle(talk);
    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(2));

    const [first, second] = callsTo("/api/dictation/remote");
    expect(first.json.delivery_id).not.toBe(second.json.delivery_id);
  });
});

describe("Speak aim selector", () => {
  it("aims at the awaiting agent and requires one to be awaiting", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: true, final_text: "ship it friday" }),
    });
    const talk = await openDeck();
    fireEvent.change(screen.getByRole("combobox", { name: "Aim" }), {
      target: { value: "agent" },
    });

    await clickToggle(talk);

    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(1));
    const [call] = callsTo("/api/dictation/remote");
    expect(call.json.target_mode).toBe("agent");
    expect(call.json.require_agent).toBe(true);
  });

  it("THIS FIELD fills the well and delivers nothing", async () => {
    const talk = await openDeck();
    fireEvent.change(screen.getByRole("combobox", { name: "Aim" }), {
      target: { value: "field" },
    });

    await clickToggle(talk);

    await waitFor(() =>
      expect(screen.getByLabelText("Utterance")).toHaveValue("ship it friday"),
    );
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
    expect(callsTo("/api/dictation/dry-run")).toHaveLength(0);
  });

  it("remembers the aim across a remount", async () => {
    const first = render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    fireEvent.change(await screen.findByRole("combobox", { name: "Aim" }), {
      target: { value: "agent" },
    });
    expect(localStorage.getItem("holdspeak.speakAim")).toBe("agent");
    first.unmount();

    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("combobox", { name: "Aim" })).toHaveValue(
      "agent",
    );
  });
});

describe("Speak REHEARSE stays explicit", () => {
  it("previews through the dry run and delivers nothing when armed", async () => {
    mockRoutes({
      "/api/dictation/dry-run": () =>
        Promise.resolve({ final_text: "ship it friday", total_ms: 120 }),
    });
    const talk = await openDeck();
    fireEvent.click(screen.getByRole("checkbox", { name: "Rehearse" }));

    await clickToggle(talk);

    await waitFor(() => expect(callsTo("/api/dictation/dry-run")).toHaveLength(1));
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
    expect(await screen.findByText("REHEARSED · NOT DELIVERED")).toBeVisible();
  });

  it("names the well's verb after the mode it is in", async () => {
    await openDeck();
    expect(screen.getByRole("button", { name: "Deliver" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "Rehearse" }));
    expect(screen.getByRole("button", { name: "Rehearse" })).toBeInTheDocument();
  });
});

describe("Speak refusals land in-flow", () => {
  it("names an unresolved desktop focus in the receipt bar and the register", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.reject(
          new ApiError(422, "desktop_focus_unresolved", {
            refusal: "desktop_focus_unresolved",
            failure_category: "delivery_refused",
            delivered: false,
          }),
        ),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    const receipt = await screen.findByText("⚠ REFUSED · NO FOCUSED APP");
    expect(receipt).toBeVisible();
    expect(receipt).toHaveAttribute("role", "alert");
    // in-flow, in the ONE receipt channel — no dialog, no toast species
    expect(screen.queryByRole("dialog")).toBeNull();
    const register = screen.getByLabelText("Dictation state");
    const refused = Array.from(
      register.querySelectorAll(".speak-register-token"),
    ).find((token) => token.textContent === "Refused");
    expect(refused).toHaveAttribute("data-active");
    expect(screen.getByLabelText("Landed latency")).toHaveTextContent(
      "NO FOCUSED APP",
    );
  });

  it("names an aimed agent with nothing awaiting", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.reject(
          new ApiError(422, "no_awaiting_agent", {
            refusal: "no_awaiting_agent",
            failure_category: "delivery_refused",
          }),
        ),
    });
    const talk = await openDeck();
    fireEvent.change(screen.getByRole("combobox", { name: "Aim" }), {
      target: { value: "agent" },
    });

    await clickToggle(talk);

    expect(
      await screen.findByText("⚠ REFUSED · NO AGENT AWAITING"),
    ).toBeVisible();
  });

  it("names a transcription failure without losing the deck", async () => {
    mocks.stopAndTranscribe.mockRejectedValue(new ApiError(504, "timeout", {}));
    const stopFn = vi.fn().mockRejectedValue(new ApiError(504, "timeout", {}));
    mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
    const talk = await openDeck();

    await clickToggle(talk);

    expect(await screen.findByText(/Transcription timed out/)).toBeVisible();
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
    const register = screen.getByLabelText("Dictation state");
    const refused = Array.from(
      register.querySelectorAll(".speak-register-token"),
    ).find((token) => token.textContent === "Refused");
    expect(refused).toHaveAttribute("data-active");
  });

  it("refuses honestly when the hub has nothing to deliver into", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: false, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    expect(
      await screen.findByText("⚠ REFUSED · NO DELIVERY TARGET"),
    ).toBeVisible();
  });
});

describe("HS-129-05 Speak footer composition", () => {
  it("publishes readiness, Review, and Export through one foot", async () => {
    mockRoutes({
      "/api/dictation/readiness": () =>
        Promise.resolve({
          config: { pipeline_enabled: false },
          target: {},
          warnings: [{ code: "pipeline_disabled" }],
        }),
    });
    const { container } = render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );

    await screen.findAllByText("PIPELINE OFF");
    expect(container.querySelectorAll(".surface-footer")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Review" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Export" })).toBeVisible();
    expect(container.querySelector(".speak-status")).toBeNull();
  });
});
