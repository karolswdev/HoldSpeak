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
      paneStatus: "live",
      paneId: "%0",
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
    expect(document.querySelector(".ask-well-question.agent-words")?.textContent).toBe(QUESTION);
    const well = screen.getByTestId("session-answer-well");
    expect(well.querySelector("input[aria-label=Answer]")).toBeTruthy();
    expect(well.querySelector("[data-testid=mic]")?.getAttribute("data-auto")).toBe("true");
    // The composer moved into the body: the window draws it once.
    expect(document.querySelectorAll("input[aria-label=Answer]")).toHaveLength(1);
    // The question sits above the well.
    const question = well.querySelector(".ask-well-question") as HTMLElement;
    expect(question.compareDocumentPosition(well.querySelector("input")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Enter sends through the existing route; the draft clears only on delivery and says sent", async () => {
    const steer = open(true);
    render(<SessionPullout />);
    const input = screen.getByTestId("session-answer-well").querySelector("input[aria-label=Answer]") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Jordan owns the rollback." } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(steer).toHaveBeenCalledWith("Jordan owns the rollback.", true, null));
    await waitFor(() => expect(input.value).toBe(""));
    expect(screen.getByText("sent")).toBeTruthy();
  });

  it("a delivered steer with a receipt says sent, then the receipt", () => {
    open(true);
    act(() => { useSteering.setState({ steerState: "sent", steerDetail: "Receipt steering:1 · %0" }); });
    render(<SessionPullout />);
    expect(screen.getByText("sent · Receipt steering:1 · %0")).toBeTruthy();
  });

  it("terminal unmounts the question and preserves its unsent answer on Back", () => {
    const steer = open(false);
    render(<SessionPullout />);
    const input = screen.getByRole("textbox", { name: "Answer" });
    fireEvent.change(input, { target: { value: "Jordan owns the rollback." } });
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    expect(screen.queryByText(QUESTION)).toBeNull();
    expect(screen.queryByTestId("session-controls")).toBeNull();
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.getByRole("textbox", { name: "Answer" })).toHaveValue("Jordan owns the rollback.");
    expect(document.querySelector(".ask-well-question")?.textContent).toBe(QUESTION);
    expect(steer).not.toHaveBeenCalled();
  });

  it("Direct returns from terminal with its unsent draft and send choice", async () => {
    const steer = open(false, { blocked: false, awaiting_response: false });
    render(<SessionPullout />);
    const direct = () => screen.getByRole("button", { name: "Direct" });
    fireEvent.click(direct());
    fireEvent.change(screen.getByRole("textbox", { name: "Direct" }), { target: { value: "Check the rollback owner." } });
    fireEvent.click(screen.getByTitle("Enter after send"));
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.queryByRole("textbox", { name: "Direct" })).toBeNull();
    fireEvent.click(direct());
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(screen.getByRole("textbox", { name: "Direct" })).toHaveValue("Check the rollback owner.");
    expect(screen.getByTitle("no Enter: text only")).toBeTruthy();
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.getByRole("textbox", { name: "Direct" })).toHaveValue("Check the rollback owner.");
    expect(screen.getByTitle("no Enter: text only")).toBeTruthy();
    fireEvent.click(direct());
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    fireEvent.click(direct());
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(screen.getByRole("textbox", { name: "Direct" })).toHaveValue("Check the rollback owner.");
    fireEvent.click(screen.getByRole("button", { name: "SEND" }));
    await waitFor(() => expect(steer).toHaveBeenCalledWith("Check the rollback owner.", false, null));
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
