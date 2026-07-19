import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MicButton } from "./MicButton";

const mocks = vi.hoisted(() => ({
  loadPendingVoice: vi.fn(),
  retryPendingTranscription: vi.fn(),
}));

vi.mock("../../lib/pendingVoice", () => ({
  loadPendingVoice: mocks.loadPendingVoice,
}));

const support = vi.hoisted(() => ({
  supported: false,
  reason: null as string | null,
}));

vi.mock("../../lib/speakToFill", () => ({
  cancelCapture: vi.fn(),
  speakToFillSupported: () => support.supported,
  speakToFillUnsupportedReason: () => support.reason,
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  retryPendingTranscription: mocks.retryPendingTranscription,
}));

describe("MicButton honest states (HS-100-06)", () => {
  beforeEach(() => {
    mocks.loadPendingVoice.mockResolvedValue(null);
    support.supported = false;
    support.reason = null;
  });

  it("renders disabled with the insecure-origin reason instead of vanishing", () => {
    support.reason =
      "Mic capture needs a secure origin. Open this hub via localhost or HTTPS to speak.";
    render(<MicButton onText={vi.fn()} />);
    const mic = screen.getByRole("button", { name: /unavailable:.*secure origin/i });
    expect(mic).toBeDisabled();
    expect(mic.className).toContain("is-unsupported");
    expect(mic.title).toMatch(/secure origin/);
  });

  it("renders disabled with the browser reason when capture APIs are missing", () => {
    support.reason = "This browser cannot capture microphone audio.";
    render(<MicButton onText={vi.fn()} />);
    const mic = screen.getByRole("button", { name: /unavailable:.*browser/i });
    expect(mic).toBeDisabled();
  });

  it("renders the live mic when capture is supported", () => {
    support.supported = true;
    render(<MicButton onText={vi.fn()} />);
    const mic = screen.getByRole("button", { name: "Hold to talk" });
    expect(mic).toBeEnabled();
    expect(mic.className).not.toContain("is-unsupported");
  });
});

describe("MicButton retained audio", () => {
  beforeEach(() => {
    support.supported = false;
    support.reason = "This browser cannot capture microphone audio.";
    mocks.loadPendingVoice.mockResolvedValue(new ArrayBuffer(8));
    mocks.retryPendingTranscription.mockResolvedValue("Recovered words");
  });

  it("retries a retained capture when new microphone capture is unavailable", async () => {
    const onText = vi.fn();
    render(<MicButton draftScope="desk-ask" onText={onText} />);

    const retry = await screen.findByRole("button", {
      name: "Retry retained audio",
    });
    expect(
      screen.getByText(/Captured audio is retained locally/),
    ).toBeVisible();

    fireEvent.pointerDown(retry);

    await waitFor(() => expect(onText).toHaveBeenCalledWith("Recovered words"));
    expect(mocks.retryPendingTranscription).toHaveBeenCalledWith("desk-ask");
  });
});
