import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MicButton } from "./MicButton";

const mocks = vi.hoisted(() => ({
  loadPendingVoice: vi.fn(),
  retryPendingTranscription: vi.fn(),
  startStreamSession: vi.fn(),
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
  subscribeCaptureLevel: () => () => undefined,
}));

vi.mock("../../lib/micStreamSession", () => ({
  micStreamSupported: () => support.supported,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
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
    const mic = screen.getByRole("button", { name: "Speak" });
    expect(mic).toBeEnabled();
    expect(mic.className).not.toContain("is-unsupported");
  });
});

describe("MicButton click-to-toggle (HS-119-01)", () => {
  beforeEach(() => {
    support.supported = true;
    support.reason = null;
    mocks.loadPendingVoice.mockResolvedValue(null);
  });

  it("click toggles between idle and listening", async () => {
    const stopFn = vi.fn().mockResolvedValue("hello world");
    const session = { stop: stopFn, cancel: vi.fn() };
    mocks.startStreamSession.mockResolvedValue(session);

    const onText = vi.fn();
    render(<MicButton onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));

    fireEvent.click(mic);
    await waitFor(() => expect(onText).toHaveBeenCalledWith("hello world"));
  });

  it("claims audio floor on start, releases on stop", async () => {
    const stopFn = vi.fn().mockResolvedValue("text");
    const session = { stop: stopFn, cancel: vi.fn() };
    mocks.startStreamSession.mockResolvedValue(session);

    const onText = vi.fn();
    render(<MicButton onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mocks.startStreamSession).toHaveBeenCalled());

    fireEvent.click(mic);
    await waitFor(() => expect(stopFn).toHaveBeenCalled());
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

    fireEvent.click(retry);

    await waitFor(() => expect(onText).toHaveBeenCalledWith("Recovered words"));
    // HS-132-04: retained audio is retried as the kind of utterance it was —
    // a field fill stays verbatim and unjournaled.
    expect(mocks.retryPendingTranscription).toHaveBeenCalledWith("desk-ask", {
      pipeline: false,
    });
  });
});

/* HS-132-04 — one utterance, one pipeline.
   A field mic is the user typing with their voice: it transcribes VERBATIM,
   with no intent routing, enrichment, rewriting or journal row. Only the
   Speak room's transport key (the dictate-for-delivery surface) asks for the
   pipeline, and that is the utterance's ONE pass. */
describe("MicButton pipeline declaration (HS-132-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    support.supported = true;
    support.reason = null;
    mocks.loadPendingVoice.mockResolvedValue(null);
    mocks.startStreamSession.mockResolvedValue({
      stop: vi.fn().mockResolvedValue("a note tag"),
      cancel: vi.fn(),
    });
  });

  it("a desk field mic asks for NO pipeline", async () => {
    render(<MicButton onText={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Speak" }));

    await waitFor(() => expect(mocks.startStreamSession).toHaveBeenCalled());
    expect(mocks.startStreamSession.mock.calls[0][1]).toEqual({
      pipeline: false,
    });
  });

  it("the Speak room's transport key keeps the pipeline", async () => {
    render(<MicButton variant="transport" onText={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Speak" }));

    await waitFor(() => expect(mocks.startStreamSession).toHaveBeenCalled());
    expect(mocks.startStreamSession.mock.calls[0][1]).toEqual({
      pipeline: true,
    });
  });

  it("an explicit pipeline prop overrides the surface default", async () => {
    render(<MicButton variant="transport" pipeline={false} onText={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Speak" }));

    await waitFor(() => expect(mocks.startStreamSession).toHaveBeenCalled());
    expect(mocks.startStreamSession.mock.calls[0][1]).toEqual({
      pipeline: false,
    });
  });

  /* A configured macro keyword fired on the server (the same contract the
     hotkey path has: the command consumed the utterance and NOTHING is typed
     as prose). */
  it("delivers no prose when a command consumed the utterance", async () => {
    const fired = {
      keyword: "standup",
      kind: "type_text",
      preview: "types: ## Standup",
      ok: true,
      error: "",
    };
    mocks.startStreamSession.mockImplementation(
      async (onEvent: (event: unknown) => void) => ({
        stop: vi.fn().mockImplementation(async () => {
          onEvent({ type: "final", text: "", fired });
          return "";
        }),
        cancel: vi.fn(),
      }),
    );
    const onText = vi.fn();
    const onCommand = vi.fn();
    const onFailure = vi.fn();
    render(
      <MicButton
        variant="transport"
        onText={onText}
        onCommand={onCommand}
        onFailure={onFailure}
      />,
    );
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);

    await waitFor(() => expect(onCommand).toHaveBeenCalledTimes(1));
    expect(onCommand).toHaveBeenCalledWith(fired);
    expect(onText).not.toHaveBeenCalled();
    // a command that RAN is not a "no speech" failure
    expect(onFailure).not.toHaveBeenCalled();
    await waitFor(() => expect(mic.className).toContain("is-idle"));
  });

  it("delivers the transcription verbatim to the field", async () => {
    const onText = vi.fn();
    render(<MicButton onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);

    await waitFor(() => expect(onText).toHaveBeenCalledWith("a note tag"));
  });
});
