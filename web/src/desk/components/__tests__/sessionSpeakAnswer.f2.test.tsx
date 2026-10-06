// Conductor F2 (Astra round 1 on #906, finding 2): each Speak answer press is
// one request to record, bound to its session. Through the real store
// (`openSession`), the real SessionPullout and the real MicButton; only the
// browser capture (`micStreamSession`) is a double.
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { useSteering } from "../../steering";

const cap = vi.hoisted(() => ({ sessions: [] as Array<{ stop: ReturnType<typeof vi.fn>; cancel: ReturnType<typeof vi.fn> }> }));

vi.mock("../../../lib/pendingVoice", () => ({ loadPendingVoice: async () => null }));
vi.mock("../../../lib/speakToFill", () => ({
  cancelCapture: vi.fn(),
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => null,
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  retryPendingTranscription: async () => null,
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  subscribeCaptureLevel: () => () => undefined,
  startStreamSession: vi.fn(async () => {
    const s = { stop: vi.fn(async () => ""), cancel: vi.fn() };
    cap.sessions.push(s);
    return s;
  }),
}));

const realPoll = useSteering.getState().poll;

function press(key: string, answer: boolean) {
  act(() => { useSteering.getState().openSession(key, answer ? { answer: true } : undefined); });
}
const listening = () => document.querySelector("[data-testid=session-answer-well] .desk-mic.is-listening");

describe("Speak answer: one capture per press, bound to its session", () => {
  beforeEach(() => {
    cap.sessions = [];
    useSteering.setState({ poll: vi.fn(async () => {}) } as never);
  });
  afterEach(() => {
    act(() => { useSteering.getState().closeSession(); });
    useSteering.setState({ poll: realPoll } as never);
  });

  it("repeated presses on one session: stop, press again, a second capture starts", async () => {
    render(<SessionPullout />);
    press("claude:a", true);
    await waitFor(() => expect(listening()).toBeTruthy());
    act(() => { (listening() as HTMLElement).click(); });          // stop A
    await waitFor(() => expect(cap.sessions[0].stop).toHaveBeenCalled());
    await waitFor(() => expect(listening()).toBeNull());
    press("claude:a", true);
    await waitFor(() => expect(listening()).toBeTruthy());
    expect(cap.sessions).toHaveLength(2);
  });

  it("switching to B while A records cancels A's capture; B records", async () => {
    render(<SessionPullout />);
    press("claude:a", true);
    await waitFor(() => expect(listening()).toBeTruthy());
    press("codex:b", true);
    await waitFor(() => expect(cap.sessions[0].cancel).toHaveBeenCalled());
    await waitFor(() => expect(cap.sessions).toHaveLength(2));
    expect(cap.sessions[1].cancel).not.toHaveBeenCalled();
  });

  it("an ordinary Open records nothing; Open on the recording session ends its capture", async () => {
    render(<SessionPullout />);
    press("claude:a", false);
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    expect(cap.sessions).toHaveLength(0);
    press("claude:a", true);
    await waitFor(() => expect(listening()).toBeTruthy());
    press("claude:a", false);
    await waitFor(() => expect(cap.sessions[0].cancel).toHaveBeenCalled());
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
  });
});
