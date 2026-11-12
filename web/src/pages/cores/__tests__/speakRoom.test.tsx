// HS-112-02 — the room named Speak performs the flagship act.
//
// HS-170-04 — adapted to the settled face: the register strip now
// lives behind > Details; the footer shows EgressChip THIS DEVICE +
// receipt; the REHEARSE checkbox became "DRY RUN", then (betterment C8)
// the visible verb "Try it here" on the Types into row;
// the Deliver/Rehearse button in the well is gone (the well is a
// PadGadget with Talk, or type here — delivery happens on TALK release).
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
  return screen.findByRole("button", { name: "Talk" });
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

  it("shows delivery latency in the plain receipt", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: true, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    const receipt = await screen.findByText(/^Sent to the app in front · \d+ ms$/);
    expect(receipt).toBeVisible();
    // The receipt retains the measured delivery latency.
    await waitFor(() => {
      const latencyTokens = screen.getAllByText(/\d+ ms/);
      expect(latencyTokens.length).toBeGreaterThan(0);
    });
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
    localStorage.setItem("holdspeak.speakAim", "agent");
    const talk = await openDeck();

    await clickToggle(talk);

    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(1));
    const [call] = callsTo("/api/dictation/remote");
    expect(call.json.target_mode).toBe("agent");
    expect(call.json.require_agent).toBe(true);
  });

  it("a kept field aim reads as the app in front", async () => {
    localStorage.setItem("holdspeak.speakAim", "field");
    await openDeck();
    expect(screen.getByTestId("speak-types-into")).toHaveTextContent("To the app in front");
  });

  it("remembers the aim across a remount", async () => {
    localStorage.setItem("holdspeak.speakAim", "agent");
    const first = render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    first.unmount();

    render(
      <MemoryRouter>
        <DictationCore />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("speak-types-into")).toHaveTextContent("To the agent");
  });
});

describe("Speak delivers one pipeline pass (HS-132-04)", () => {
  it("delivers a spoken utterance raw — it was already piped once", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({
          success: true,
          delivered: true,
          final_text: "ship it friday",
        }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    await waitFor(() =>
      expect(callsTo("/api/dictation/remote")).toHaveLength(1),
    );
    const [call] = callsTo("/api/dictation/remote");
    expect(call.json.raw).toBe(true);
    expect(call.json.text).toBe("ship it friday");
  });

  it("names a fired command in the receipt bar and delivers no prose", async () => {
    mocks.startStreamSession.mockImplementation(
      async (onEvent: (event: unknown) => void) => ({
        stop: vi.fn().mockImplementation(async () => {
          onEvent({
            type: "final",
            text: "",
            fired: {
              keyword: "standup",
              kind: "type_text",
              preview: "types: ## Standup",
              ok: true,
              error: "",
            },
          });
          return "";
        }),
        cancel: vi.fn(),
      }),
    );
    const talk = await openDeck();

    await clickToggle(talk);

    expect(await screen.findByText("Command ran · types: ## Standup")).toBeVisible();
    // nothing was dictated: no delivery, no rehearsal, and the well is clean
    expect(callsTo("/api/dictation/remote")).toHaveLength(0);
    expect(callsTo("/api/dictation/dry-run")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", {name:"Type"}));
    expect(screen.getByLabelText("Utterance")).toHaveValue("");
  });

  it("pipes text the user TYPED into the well exactly once, on delivery", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({
          success: true,
          delivered: true,
          final_text: "[corrected] typed words",
        }),
    });
    await openDeck();
    fireEvent.click(screen.getByRole("button", {name:"Type"}));
    fireEvent.change(await screen.findByLabelText("Utterance"), {
      target: { value: "typed words" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Put words back" }));
    await waitFor(() => expect(callsTo("/api/dictation/remote")).toHaveLength(1));
    expect(callsTo("/api/dictation/remote")[0].json.raw).toBeUndefined();
    expect(await screen.findByRole("log",{name:"Sent words"})).toHaveTextContent("[corrected] typed words");
  });
});


describe("Speak refusals land in-flow", () => {
  it("names an unresolved desktop focus in the receipt bar", async () => {
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

    const receipt = await screen.findByText(/^No app in front/);
    expect(receipt).toBeVisible();
    // in-flow, in the ONE receipt channel — no dialog, no toast species
    expect(screen.queryByRole("dialog")).toBeNull();
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
    localStorage.setItem("holdspeak.speakAim", "agent");
    const talk = await openDeck();

    await clickToggle(talk);

    expect(
      await screen.findByText(/^No agent waits for words/),
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
  });

  it("refuses honestly when the hub has nothing to deliver into", async () => {
    mockRoutes({
      "/api/dictation/remote": () =>
        Promise.resolve({ success: true, delivered: false, final_text: "ship it friday" }),
    });
    const talk = await openDeck();

    await clickToggle(talk);

    expect(
      await screen.findByText(/^No place to deliver to/),
    ).toBeVisible();
  });
});
