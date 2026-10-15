// Conductor F2 (Astra round 1 on #906, finding 2): each Speak answer press is
// one request to record, bound to its session. Through the real store
// (`openSession`), the real SessionPullout and the real MicButton; only the
// browser capture (`micStreamSession`) is a double.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSteeringSession, useSteering } from "../../steering";

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

  it.each([false, true])("terminal cancels capture and Back does not replay the last press (question: %s)", async (question) => {
    render(<SessionPullout />);
    press("claude:a", true);
    if (question) act(() => {
      useSteering.setState({ session: fromWireSteeringSession({ key: "claude:a", agent: "claude", blocked: true, question: "Who owns rollback?" }) });
    });
    await waitFor(() => expect(listening()).toBeTruthy());
    const captures = cap.sessions.length;
    const current = cap.sessions.at(-1)!;
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    await waitFor(() => expect(current.cancel).toHaveBeenCalled());
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.getByTestId("session-answer-well")).toBeTruthy();
    expect(listening()).toBeNull();
    expect(cap.sessions).toHaveLength(captures);
    press("claude:a", true);
    await waitFor(() => expect(listening()).toBeTruthy());
    expect(cap.sessions).toHaveLength(captures + 1);
  });

  it.each([false, true])("a new Speak press while terminal is active reveals its composer (question: %s)", async (question) => {
    render(<SessionPullout />);
    press("claude:a", false);
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.getByTestId("session-terminal")).toBeTruthy();
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    act(() => {
      useSteering.getState().openSession("claude:a", { answer: true });
      if (question) useSteering.setState({ session: fromWireSteeringSession({ key: "claude:a", agent: "claude", blocked: true, question: "Who owns rollback?" }) });
    });
    await waitFor(() => expect(listening()).toBeTruthy());
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(screen.getByRole("textbox", { name: question ? "Answer" : "Direct" })).toBeTruthy();
    expect(cap.sessions).toHaveLength(1);

    fireEvent.click(screen.getByTestId("session-open-terminal"));
    await waitFor(() => expect(cap.sessions[0].cancel).toHaveBeenCalled());
    expect(screen.getByTestId("session-terminal")).toBeTruthy();
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(listening()).toBeNull();
    expect(cap.sessions).toHaveLength(1);
  });
});
