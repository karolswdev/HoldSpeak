/* PHILO-17 transcribe — the verb of a meeting saved with its audio only.
 *
 * Shown only when the meeting is audio-only (`speech_not_set_up`) AND speech
 * is ready (GET /api/setup/local-ai `speech`, the one truth). While speech is
 * not set up the record shows "Set up speech" instead and the list row keeps
 * its Open. A meeting with a transcript, or one being transcribed, shows
 * neither. The hub is faked; nothing is transcribed. */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

import { AudioOnlyVerb } from "../TranscribeVerb";
import { audioOnlyVerb, speechWasMissing } from "../../../../desk/firstrun/speechTruth";
import { meetingRowState, meetingsHeadline, stateToken } from "../helpers";

const MB = 1_000_000;
let ready = false;

function speech() {
  return {
    state: "not_started",
    files: [{ key: "whisper", label: "whisper-base-mlx", size_bytes: 144 * MB, on_device: ready }],
    bytes_total: 0,
    bytes_done: 0,
    egress: { destination: "huggingface.co" },
    speech: { model: "base", backend: "mlx", state: ready ? "on_device" : "will_download", ready, bytes: ready ? 0 : 144 * MB },
    error: "",
  };
}

const AUDIO_ONLY = {
  id: "m-1",
  title: "Standup",
  transcription_status: "record_only",
  transcription_status_detail: { reason_code: "speech_not_set_up", repair: "set_up_speech" },
  intel_status: "disabled",
};
const TRANSCRIBING = { ...AUDIO_ONLY, intel_status: "importing" };
const WITH_TRANSCRIPT = { id: "m-2", transcription_status: "complete", transcription_status_detail: null, intel_status: "disabled", transcriptWords: 120 };

beforeEach(() => {
  ready = false;
  mocks.apiFetch.mockReset().mockImplementation(async (path: string) => {
    if (path === "/api/setup/local-ai") return speech();
    throw new Error(`unexpected ${path}`);
  });
});

describe("audioOnlyVerb — the one rule", () => {
  it("Transcribe only when audio-only AND speech is ready", () => {
    expect(audioOnlyVerb(AUDIO_ONLY, { ready: true, notSetUp: false })).toBe("transcribe");
    expect(audioOnlyVerb(AUDIO_ONLY, { ready: false, notSetUp: true })).toBe("set_up_speech");
    expect(audioOnlyVerb(AUDIO_ONLY, { ready: false, notSetUp: false })).toBeNull(); // read pending
    expect(audioOnlyVerb(WITH_TRANSCRIPT, { ready: true, notSetUp: false })).toBeNull();
    expect(audioOnlyVerb(TRANSCRIBING, { ready: true, notSetUp: false })).toBeNull();
  });

  it("a meeting being transcribed says TRANSCRIBING, not SPEECH NOT SET UP", () => {
    expect(speechWasMissing(TRANSCRIBING)).toBe(false);
    expect(stateToken(TRANSCRIBING).label).toBe("TRANSCRIBING");
    expect(meetingRowState(TRANSCRIBING).verb).toBeNull();
    expect(meetingsHeadline([TRANSCRIBING], false).text).toBe("1 meeting transcribing");
  });
});

describe("AudioOnlyVerb — the rendered verb", () => {
  it("speech ready: ONE Transcribe verb, and a press starts it", async () => {
    ready = true;
    const onTranscribe = vi.fn().mockResolvedValue({ status: "transcribing" });
    render(<AudioOnlyVerb row={AUDIO_ONLY} onTranscribe={onTranscribe} setUpSpeech testId="t" />);
    const verb = await screen.findByTestId("t-verb");
    expect(verb.textContent).toBe("Transcribe");
    expect(screen.getAllByRole("button")).toHaveLength(1);
    fireEvent.click(verb);
    await waitFor(() => expect(onTranscribe).toHaveBeenCalledWith("m-1"));
  });

  it("speech not set up: the record shows Set up speech, never Transcribe", async () => {
    render(<AudioOnlyVerb row={AUDIO_ONLY} onTranscribe={vi.fn()} setUpSpeech testId="t" />);
    expect((await screen.findByTestId("t-speech-setup-verb")).textContent).toBe("Set up speech · 144 MB");
    expect(screen.queryByText("Transcribe")).toBeNull();
  });

  it("speech not set up: the list row keeps its own verb", async () => {
    render(<AudioOnlyVerb row={AUDIO_ONLY} onTranscribe={vi.fn()} otherwise={<span>Open</span>} testId="t" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/local-ai"));
    expect(await screen.findByText("Open")).toBeTruthy();
    expect(screen.queryByText("Transcribe")).toBeNull();
  });

  it("a meeting with its transcript: no verb and no speech read", () => {
    ready = true;
    render(<AudioOnlyVerb row={WITH_TRANSCRIPT} onTranscribe={vi.fn()} setUpSpeech testId="t" />);
    expect(screen.queryByText("Transcribe")).toBeNull();
    expect(mocks.apiFetch).not.toHaveBeenCalled();
  });

  it("route and Config disagree: the meeting's own readiness decides (route base ready, Config large missing)", async () => {
    ready = false; // the setup read (Config `large`) says speech is not set up
    const row = { ...AUDIO_ONLY, transcribe_speech: { model: "base", backend: "mlx", state: "on_device", ready: true } };
    render(<AudioOnlyVerb row={row} onTranscribe={vi.fn()} setUpSpeech testId="t" />);
    expect((await screen.findByTestId("t-verb")).textContent).toBe("Transcribe");
    expect(screen.queryByTestId("t-speech-setup-verb")).toBeNull();
  });

  it("route and Config disagree the other way: no Transcribe the operation would refuse", async () => {
    ready = true; // the setup read (Config) says ready
    const row = { ...AUDIO_ONLY, transcribe_speech: { model: "large", backend: "mlx", state: "will_download", ready: false } };
    render(<AudioOnlyVerb row={row} onTranscribe={vi.fn()} setUpSpeech testId="t" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/local-ai"));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByText("Transcribe")).toBeNull();
  });

  it("the last failed Transcribe says its cause beside the verb", async () => {
    ready = true;
    const failed = { ...AUDIO_ONLY, transcription_status_detail: { ...AUDIO_ONLY.transcription_status_detail, last_error: "NO SPEECH FOUND" } };
    render(<AudioOnlyVerb row={failed} onTranscribe={vi.fn()} setUpSpeech testId="t" />);
    expect((await screen.findByTestId("t-last-error")).textContent).toContain("LAST ERROR · NO SPEECH FOUND");
  });
});
