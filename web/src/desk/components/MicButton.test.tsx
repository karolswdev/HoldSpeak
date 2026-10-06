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
    // PHILO-13-04 round three: the branch names the fact, never a sentence,
    // in the accessible name and the title alike.
    const mic = screen.getByRole("button", { name: "Speak · NEEDS LOCALHOST OR HTTPS" });
    expect(mic).toBeDisabled();
    expect(mic.className).toContain("is-unsupported");
    expect(mic.title).toBe("NEEDS LOCALHOST OR HTTPS");
    expect(document.body.innerHTML).not.toMatch(/secure origin|Open this hub/);
  });

  it("renders disabled with the browser reason when capture APIs are missing", () => {
    support.reason = "This browser cannot capture microphone audio.";
    render(<MicButton onText={vi.fn()} />);
    const mic = screen.getByRole("button", { name: "Speak · NO MICROPHONE IN THIS BROWSER" });
    expect(mic).toBeDisabled();
    expect(mic.title).toBe("NO MICROPHONE IN THIS BROWSER");
    expect(document.body.innerHTML).not.toMatch(/cannot capture/);
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

describe("MicButton startSignal (Conductor F2, K5b)", () => {
  beforeEach(() => {
    support.supported = true;
    support.reason = null;
    mocks.loadPendingVoice.mockResolvedValue(null);
    mocks.startStreamSession.mockReset();
  });

  it("each new signal is one start; a re-render does not start again; a click stops it", async () => {
    const stopFn = vi.fn().mockResolvedValue("Jordan owns it");
    mocks.startStreamSession.mockResolvedValue({ stop: stopFn, cancel: vi.fn() });
    const onText = vi.fn();
    const { rerender } = render(<MicButton onText={onText} startSignal={1} />);
    const mic = await screen.findByRole("button", { name: "Stop listening" });
    rerender(<MicButton onText={onText} startSignal={1} />);
    expect(mocks.startStreamSession).toHaveBeenCalledTimes(1);
    fireEvent.click(mic);
    await waitFor(() => expect(onText).toHaveBeenCalledWith("Jordan owns it"));
    // A second press (a new signal) on the same field starts again.
    rerender(<MicButton onText={onText} startSignal={2} />);
    await screen.findByRole("button", { name: "Stop listening" });
    expect(mocks.startStreamSession).toHaveBeenCalledTimes(2);
  });

  it("a new signal while a capture runs leaves it running (no second capture)", async () => {
    mocks.startStreamSession.mockResolvedValue({ stop: vi.fn().mockResolvedValue(""), cancel: vi.fn() });
    const { rerender } = render(<MicButton onText={vi.fn()} startSignal={1} />);
    await screen.findByRole("button", { name: "Stop listening" });
    rerender(<MicButton onText={vi.fn()} startSignal={2} />);
    expect(mocks.startStreamSession).toHaveBeenCalledTimes(1);
  });

  it("unmounted while the capture opens: the capture is cancelled, never left recording", async () => {
    const cancel = vi.fn();
    let resolve!: (s: unknown) => void;
    mocks.startStreamSession.mockReturnValue(new Promise((r) => { resolve = r; }));
    const { unmount } = render(<MicButton onText={vi.fn()} startSignal={1} />);
    await waitFor(() => expect(mocks.startStreamSession).toHaveBeenCalledTimes(1));
    unmount();
    resolve({ stop: vi.fn(), cancel });
    await waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
  });

  it("without a signal nothing listens until a click", () => {
    render(<MicButton onText={vi.fn()} />);
    expect(mocks.startStreamSession).not.toHaveBeenCalled();
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
    // PHILO-13-04 (A3): the retention fact is a name on the face, not a sentence.
    expect(screen.getByText(/AUDIO KEPT/)).toBeVisible();

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

/* HS-176 C1 (the SPOKEN half) — the run's facts ride the `final` frame.

   The spoken leg is the one that runs the pipeline and writes the journal row;
   the delivery that follows sends `raw: true` and computes nothing. Unless the
   transport carries `raw_text`, `corrections_applied` and `journal_id` out of
   the frame, the Speak face has no APPLIED chip, pre-fills its TEXT teach from
   the LANDED text, and teaches on the corrections fallback. */
describe("MicButton carries the spoken run's facts (HS-176 C1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    support.supported = true;
    support.reason = null;
    mocks.loadPendingVoice.mockResolvedValue(null);
  });

  const streamingFinal = (frame: Record<string, unknown>, text: string) =>
    mocks.startStreamSession.mockImplementation(
      async (onEvent: (event: unknown) => void) => ({
        stop: vi.fn().mockImplementation(async () => {
          onEvent(frame);
          return text;
        }),
        cancel: vi.fn(),
      }),
    );

  it("hands the three facts to onText beside the landed text", async () => {
    streamingFinal(
      {
        type: "final",
        text: "PostgreSQL needs a bump",
        raw_text: "postgress needs a bump",
        corrections_applied: [5],
        journal_id: 41,
      },
      "PostgreSQL needs a bump",
    );
    const onText = vi.fn();
    render(<MicButton variant="transport" onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);

    await waitFor(() => expect(onText).toHaveBeenCalledTimes(1));
    expect(onText).toHaveBeenCalledWith("PostgreSQL needs a bump", {
      raw_text: "postgress needs a bump",
      corrections_applied: [5],
      journal_id: 41,
    });
  });

  it("passes nothing when the frame carried no facts", async () => {
    streamingFinal({ type: "final", text: "a note tag" }, "a note tag");
    const onText = vi.fn();
    render(<MicButton variant="transport" onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);

    // exactly the one-argument call every caller has always seen
    await waitFor(() => expect(onText).toHaveBeenCalledWith("a note tag"));
  });

  it("never carries one utterance's facts into the next", async () => {
    streamingFinal(
      {
        type: "final",
        text: "PostgreSQL needs a bump",
        raw_text: "postgress needs a bump",
        corrections_applied: [5],
        journal_id: 41,
      },
      "PostgreSQL needs a bump",
    );
    const onText = vi.fn();
    render(<MicButton variant="transport" onText={onText} />);
    const mic = screen.getByRole("button", { name: "Speak" });

    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);
    await waitFor(() => expect(onText).toHaveBeenCalledTimes(1));

    streamingFinal({ type: "final", text: "ship it friday" }, "ship it friday");
    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);

    await waitFor(() => expect(onText).toHaveBeenCalledTimes(2));
    expect(onText).toHaveBeenLastCalledWith("ship it friday");
  });
});

/* HS-132-05 — the streaming mic is honest.
   Every server refusal reaches the user BY NAME; the empty final that follows
   an error is never re-labelled "no words"; and when the session retained the
   audio, the retained-audio copy and its Retry are real. */
describe("MicButton surfaces named refusals (HS-132-05)", () => {
  /** A session whose stop() delivers `event` first, then an empty final —
   *  exactly what the socket does: the server errors, then closes. */
  const refusingSession = (
    event: Record<string, unknown>,
    { retained = false }: { retained?: boolean } = {},
  ) =>
    mocks.startStreamSession.mockImplementation(
      async (onEvent: (e: unknown) => void) => ({
        stop: vi.fn().mockImplementation(async () => {
          onEvent(event);
          return "";
        }),
        cancel: vi.fn(),
        retained: vi.fn().mockResolvedValue(retained),
      }),
    );

  beforeEach(() => {
    vi.clearAllMocks();
    support.supported = true;
    support.reason = null;
    mocks.loadPendingVoice.mockResolvedValue(null);
    // nothing retained from an earlier utterance: this click captures
    mocks.retryPendingTranscription.mockResolvedValue(null);
  });

  const speakAndStop = async () => {
    const mic = screen.getByRole("button", { name: "Speak" });
    fireEvent.click(mic);
    await waitFor(() => expect(mic.className).toContain("is-listening"));
    fireEvent.click(mic);
    return mic;
  };

  it("names a closed interval instead of reporting no_speech", async () => {
    refusingSession({
      type: "error",
      error: "The microphone session closed.",
      reason: "speech_child_budget_exhausted",
      failure_category: "speech_session_refused",
      mic_interval: "closed",
    });
    const onFailure = vi.fn();
    render(<MicButton onText={vi.fn()} onFailure={onFailure} />);

    await speakAndStop();

    await waitFor(() =>
      expect(onFailure).toHaveBeenCalledWith("mic_interval_closed"),
    );
    // the empty final behind the error must not overwrite it
    expect(onFailure).not.toHaveBeenCalledWith("no_speech");
    // PHILO-13-04 (A3 + fix round): the face shows the server's NAME and the
    // verb that continues (Retry); the contract sentence is nowhere on it,
    // its tooltips included.
    expect(screen.getByRole("status")).not.toHaveAttribute("title");
    expect(document.body.innerHTML).not.toMatch(/Click the mic again to continue/);
    expect(screen.getByRole("button", { name: "Retry" })).toBeVisible();
    expect(screen.getByText("SPEECH CHILD BUDGET EXHAUSTED")).toBeVisible();
  });

  it("names a provider failure and offers another Runs-on", async () => {
    refusingSession({
      type: "error",
      error: "endpoint:model_unreachable",
      reason: "model_unreachable",
      failure_category: "speech_provider_failure",
    });
    const onFailure = vi.fn();
    render(<MicButton onText={vi.fn()} onFailure={onFailure} />);

    await speakAndStop();

    await waitFor(() =>
      expect(onFailure).toHaveBeenCalledWith("provider_failure"),
    );
    expect(screen.getByText("MODEL UNREACHABLE")).toBeVisible();
  });

  it("names a lost audio floor", async () => {
    refusingSession({
      type: "error",
      error: "The microphone floor was taken by another source.",
      reason: "audio_floor_lost",
      failure_category: "audio_floor_lost",
      mic_interval: "closed",
    });
    const onFailure = vi.fn();
    render(<MicButton onText={vi.fn()} onFailure={onFailure} />);

    await speakAndStop();

    await waitFor(() =>
      expect(onFailure).toHaveBeenCalledWith("audio_floor_held"),
    );
  });

  it("still reports no_speech when the server heard nothing", async () => {
    mocks.startStreamSession.mockResolvedValue({
      stop: vi.fn().mockResolvedValue(""),
      cancel: vi.fn(),
      retained: vi.fn().mockResolvedValue(false),
    });
    const onFailure = vi.fn();
    render(<MicButton onText={vi.fn()} onFailure={onFailure} />);

    await speakAndStop();

    await waitFor(() => expect(onFailure).toHaveBeenCalledWith("no_speech"));
  });

  it("says the audio is retained only when the session really kept it", async () => {
    refusingSession(
      {
        type: "error",
        error: "Transcription failed.",
        reason: "transcription_failed",
        failure_category: "transcription_failed",
      },
      { retained: true },
    );
    render(<MicButton draftScope="desk-ask" onText={vi.fn()} />);

    await speakAndStop();

    await waitFor(() => expect(screen.getByText(/AUDIO KEPT/)).toBeVisible());
    expect(
      screen.getByRole("button", { name: "Retry retained audio" }),
    ).toBeVisible();
    // the capture is retained under the field's own scope
    expect(mocks.startStreamSession.mock.calls[0][1]).toEqual({
      pipeline: false,
      retainScope: "desk-ask",
    });
  });

  it("never claims retention the session cannot prove", async () => {
    refusingSession(
      {
        type: "error",
        error: "Transcription failed.",
        failure_category: "transcription_failed",
      },
      { retained: false },
    );
    render(<MicButton draftScope="desk-ask" onText={vi.fn()} />);

    await speakAndStop();

    await waitFor(() => expect(screen.getByText("TRANSCRIPTION FAILED")).toBeVisible());
    expect(document.body.innerHTML).not.toMatch(/Retry or type below/);
    expect(screen.queryByText(/AUDIO KEPT/)).toBeNull();
  });
});
