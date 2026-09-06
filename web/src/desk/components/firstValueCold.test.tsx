/* HS-200-04 — first value is cold-safe.
 *
 * The product's first promise is a sentence you can type, edit, Copy and Keep.
 * On a machine with no model and no LLM configured that promise must still
 * hold, so this face may not consult readiness at all: it must never ask for
 * `/api/dictation/readiness` or `/api/setup/status`, and its two verbs must
 * turn on the moment there is text — nothing else. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FirstWords } from "./FirstWords";
import { clearFirstValueKeepNoteId, takeFirstValueNoteOpen } from "../firstValue";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  refresh: vi.fn(),
  loadPendingVoice: vi.fn(),
  openSurfaceOr: vi.fn(),
  writeText: vi.fn(),
}));

vi.mock("../store", () => ({
  useDesk: (selector: (state: { refresh: typeof mocks.refresh }) => unknown) =>
    selector({ refresh: mocks.refresh }),
}));

vi.mock("../../lib/api", () => {
  class ApiError extends Error {
    constructor(public status: number, message: string) {
      super(message);
    }
  }
  return {
    ApiError,
    apiFetch: mocks.apiFetch,
    readableError: (error: unknown) =>
      error instanceof Error ? error.message : "Request failed",
  };
});

vi.mock("../../lib/speakToFill", () => ({
  // The cold machine this face has to work on: no capture at all.
  speakToFillSupported: () => false,
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  cancelCapture: vi.fn(),
  retryPendingTranscription: vi.fn().mockResolvedValue(null),
  subscribeCaptureLevel: () => () => undefined,
  speakToFillUnsupportedReason: () => "This browser cannot capture microphone audio.",
}));

vi.mock("../../lib/micStreamSession", () => ({
  micStreamSupported: () => false,
  startStreamSession: vi.fn(),
  subscribeCaptureLevel: () => () => undefined,
  speakToFillUnsupportedReason: () => "This browser cannot capture microphone audio.",
}));

vi.mock("../../lib/pendingVoice", () => ({
  loadPendingVoice: mocks.loadPendingVoice,
}));

vi.mock("../shell", () => ({
  openSurfaceOr: mocks.openSurfaceOr,
}));

const SENTENCE = "the postgres migration lands on friday";

describe("first value on a cold install (HS-200-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    clearFirstValueKeepNoteId();
    takeFirstValueNoteOpen();
    mocks.apiFetch.mockImplementation((path: string) => {
      if (String(path).endsWith("/start"))
        return Promise.resolve({ attempt: { id: "a1" } });
      if (String(path) === "/api/notes")
        return Promise.resolve({ note: { id: "note_1" } });
      return Promise.resolve({ success: true });
    });
    mocks.loadPendingVoice.mockResolvedValue(null);
    mocks.refresh.mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: mocks.writeText.mockResolvedValue(undefined) },
    });
  });

  it("types, edits, copies and keeps with no model and no readiness read", async () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );

    const editor = await screen.findByRole("textbox", {
      name: "Your dictated text",
    });
    const copy = screen.getByRole("button", { name: "Copy" });
    const keep = screen.getByRole("button", { name: "Keep as Note" });

    // Nothing typed yet: the verbs wait on TEXT, not on a model.
    expect(editor).toBeEnabled();
    expect(copy).toBeDisabled();
    expect(keep).toBeDisabled();

    fireEvent.change(editor, { target: { value: SENTENCE } });
    expect(editor).toHaveValue(SENTENCE);
    expect(copy).toBeEnabled();
    expect(keep).toBeEnabled();

    // Edit it — still the owner's text, still keepable.
    fireEvent.change(editor, { target: { value: `${SENTENCE}.` } });
    expect(keep).toBeEnabled();

    fireEvent.click(copy);
    await waitFor(() => expect(mocks.writeText).toHaveBeenCalledWith(`${SENTENCE}.`));

    fireEvent.click(keep);
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith(
        "/api/notes",
        expect.objectContaining({ method: "POST" }),
      ),
    );

    // The fence: this face never asked whether a model was ready.
    const asked = mocks.apiFetch.mock.calls.map(([path]) => String(path));
    expect(asked.some((path) => path.includes("/api/dictation/readiness"))).toBe(false);
    expect(asked.some((path) => path.includes("/api/setup/status"))).toBe(false);
    expect(asked.some((path) => path.includes("/api/concierge/"))).toBe(false);
    expect(asked.some((path) => path.includes("/api/inference"))).toBe(false);
  });

  it("keeps the composer usable when the browser cannot capture at all", async () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const editor = await screen.findByRole("textbox", {
      name: "Your dictated text",
    });
    expect(editor).toBeEnabled();
    fireEvent.change(editor, { target: { value: SENTENCE } });
    expect(screen.getByRole("button", { name: "Keep as Note" })).toBeEnabled();
  });
});
