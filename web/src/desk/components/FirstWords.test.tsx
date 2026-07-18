import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FirstWords } from "./FirstWords";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  cancelCapture: vi.fn(),
  retryPendingTranscription: vi.fn(),
}));

vi.mock("../../lib/api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
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
  speakToFillSupported: () => true,
  startCapture: mocks.startCapture,
  stopAndTranscribe: mocks.stopAndTranscribe,
  cancelCapture: mocks.cancelCapture,
  retryPendingTranscription: mocks.retryPendingTranscription,
}));

describe("FirstWords", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path.endsWith("/start"))
        return Promise.resolve({ attempt: { id: "a1" } });
      return Promise.resolve({ success: true });
    });
    mocks.startCapture.mockResolvedValue(undefined);
    mocks.stopAndTranscribe.mockResolvedValue(
      "A sentence that stays editable.",
    );
    mocks.retryPendingTranscription.mockResolvedValue(null);
  });

  it("captures one local step, retains editable text, and records no phrase", async () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const talk = screen.getByRole("button", { name: "Hold to dictate" });
    fireEvent.pointerDown(talk);
    await screen.findByText("Listening… release when done");
    fireEvent.pointerUp(talk);

    const editor = await screen.findByRole("textbox", {
      name: "Your dictated text",
    });
    expect(editor).toHaveValue("A sentence that stays editable.");
    fireEvent.change(editor, { target: { value: "Edited after dictation." } });
    expect(editor).toHaveValue("Edited after dictation.");

    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith(
        "/api/setup/first-value/a1/finish",
        expect.objectContaining({
          json: {
            outcome: "success",
            destination: "this_machine",
          },
        }),
      ),
    );
    const finish = mocks.apiFetch.mock.calls.find(([path]) =>
      String(path).includes("/finish"),
    );
    expect(JSON.stringify(finish?.[1])).not.toContain(
      "A sentence that stays editable",
    );
  });

  it("keeps recovery actions visible after permission denial", async () => {
    mocks.startCapture.mockRejectedValue(
      new DOMException("denied", "NotAllowedError"),
    );
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    fireEvent.pointerDown(
      screen.getByRole("button", { name: "Hold to dictate" }),
    );
    expect(
      await screen.findByText(/Microphone access is off/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Dictation unavailable until setup is fixed",
      }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Copy" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Keep as Note" })).toBeDisabled();
    // HS-95-07: Setup opens in-world through the shell dispatcher.
    expect(screen.getByRole("button", { name: "Setup" })).toBeInTheDocument();
  });

  it("transcribes one capture exactly once when release is repeated", async () => {
    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );
    const talk = screen.getByRole("button", { name: "Hold to dictate" });
    fireEvent.pointerDown(talk);
    await screen.findByText("Listening… release when done");

    fireEvent.pointerUp(talk);
    fireEvent.pointerUp(talk);

    await screen.findByDisplayValue("A sentence that stays editable.");
    expect(mocks.stopAndTranscribe).toHaveBeenCalledOnce();
    await waitFor(() =>
      expect(
        mocks.apiFetch.mock.calls.filter(([path]) =>
          String(path).endsWith("/finish"),
        ),
      ).toHaveLength(1),
    );
  });

  it("persists Continue later independently of first success", async () => {
    const dismissed = vi.fn();
    render(
      <MemoryRouter>
        <FirstWords onDismiss={dismissed} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Continue later" }));
    await waitFor(() => expect(dismissed).toHaveBeenCalledOnce());
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/onboarding", {
      method: "PUT",
      json: { disposition: "dismissed" },
    });
  });

  it("recovers an editable local draft after remount without sending it to metrics", async () => {
    localStorage.setItem(
      "hs.draft.v1.first-words",
      JSON.stringify({
        version: 1,
        text: "A draft retained through relaunch.",
        updatedAt: "2026-07-11T00:00:00Z",
      }),
    );

    render(
      <MemoryRouter>
        <FirstWords />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("textbox", { name: "Your dictated text" }),
    ).toHaveValue("A draft retained through relaunch.");
    expect(screen.getByText(/Recovered your local draft/)).toBeInTheDocument();
    expect(JSON.stringify(mocks.apiFetch.mock.calls)).not.toContain(
      "A draft retained through relaunch",
    );
  });
});
