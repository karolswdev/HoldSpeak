// Conductor F2 (ratified boards K5b, K5c): Speak answer opens the session
// window with the question, then an answer well IN THE BODY holding the steer
// composer, its mic already recording. Enter sends (Shift+Enter is a new
// line); the composer empties and shows `sent`. The question shows when only
// a permission Notification set it (the hub's `blocked`).
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSteeringSession, useSteering } from "../../steering";

const mic = vi.hoisted(() => ({ props: [] as Array<Record<string, unknown>> }));
vi.mock("../MicButton", () => ({
  MicButton: (props: Record<string, unknown>) => {
    mic.props.push(props);
    return <span data-testid="mic" data-auto={String(Boolean(props.startSignal))} />;
  },
}));

const QUESTION = "The runbook needs a rollback owner. Jordan or Avery?";

function open(answer: boolean, wire: Record<string, unknown> = {}) {
  const steer = vi.fn(async () => {
    useSteering.setState({ steerState: "sent", steerDetail: "" });
    return true;
  });
  act(() => {
    useSteering.setState({
      openKey: "claude:c1",
      answerOpen: answer,
      answerSeq: answer ? 1 : 0,
      session: fromWireSteeringSession({
        key: "claude:c1", agent: "claude", question: QUESTION,
        awaiting_response: false, blocked: true, ...wire,
      }),
      paneStatus: "no_pane",
      armed: false,
      postureAuthorized: false,
      steerState: "idle",
      steer,
    } as never);
  });
  return steer;
}

describe("Speak answer: the answer well (K5b, K5c)", () => {
  beforeEach(() => {
    mic.props = [];
    localStorage.clear();
  });

  it("shows the question a permission Notification set, then the well with its mic recording", () => {
    open(true);
    render(<SessionPullout />);
    // Phase 16: the question is the agent's words (AgentWords), not a <pre>.
    expect(document.querySelector(".desk-session-question.agent-words")?.textContent).toBe(QUESTION);
    const well = screen.getByTestId("session-answer-well");
    expect(well.querySelector(".desk-steer-input")).toBeTruthy();
    expect(well.querySelector("[data-testid=mic]")?.getAttribute("data-auto")).toBe("true");
    // The composer moved into the body: the window draws it once.
    expect(document.querySelectorAll(".desk-steer-input")).toHaveLength(1);
    // The question sits above the well.
    const pre = document.querySelector(".desk-session-question") as HTMLElement;
    expect(pre.compareDocumentPosition(well) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Enter sends; the composer empties and says sent; Shift+Enter does not send", async () => {
    const steer = open(true);
    render(<SessionPullout />);
    const input = screen.getByTestId("session-answer-well").querySelector(".desk-steer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Jordan owns the rollback." } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(steer).not.toHaveBeenCalled();
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(steer).toHaveBeenCalledWith("Jordan owns the rollback.", true, null));
    await waitFor(() => expect(input.value).toBe(""));
    expect(screen.getByText("sent")).toBeTruthy();
  });

  it("a delivered steer with a receipt says sent, then the receipt", () => {
    open(true);
    act(() => { useSteering.setState({ steerState: "sent", steerDetail: "Receipt steering:1 · %0" }); });
    render(<SessionPullout />);
    expect(screen.getByTestId("session-answer-well").querySelector(".desk-steer-sent")?.textContent).toContain("sent · Receipt steering:1 · %0");
  });

  it("Open (no answer) draws no answer well and no recording mic; a session that does not wait shows no question", () => {
    open(false, { blocked: false, awaiting_response: false });
    render(<SessionPullout />);
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    expect(screen.queryByText(QUESTION, { selector: "pre" })).toBeNull();
    expect(mic.props.some((p) => p.startSignal)).toBe(false);
  });

  it("openSession(key, {answer}) sets the well; closeSession clears it", () => {
    const poll = useSteering.getState().poll;
    useSteering.setState({ poll: vi.fn(async () => {}) } as never);
    useSteering.getState().openSession("claude:c1", { answer: true });
    expect(useSteering.getState().answerOpen).toBe(true);
    useSteering.getState().closeSession();
    expect(useSteering.getState().answerOpen).toBe(false);
    useSteering.getState().openSession("claude:c1");
    expect(useSteering.getState().answerOpen).toBe(false);
    useSteering.getState().closeSession();
    useSteering.setState({ poll } as never);
  });
});
