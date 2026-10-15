import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSessionRow, useAgentFlights } from "../../agentFlights";
import { fromWireSteeringSession, useSteering, type PaneStatus } from "../../steering";
import { useDesk } from "../../store";
import recording from "./fixtures/session-terminal.recorded.json";

vi.mock("../MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

function open(extra: Record<string, unknown> = {}) {
  act(() => {
    useAgentFlights.setState({ loaded: true, flights: [], sessions: [fromWireSessionRow({ session: {
      agent: "codex", session_id: "same-id", project_name: "payments-ledger", lifecycle: "working",
      last_assistant_text: "Added the rollback checkpoint. Checking the migration tests.",
      last_tool_name: "Bash", ...extra,
    } }), fromWireSessionRow({ session: { agent: "claude", session_id: "same-id", project_name: "other-project" } })] });
    useDesk.setState({ items: { ...useDesk.getState().items, coder: [] } });
    useSteering.setState({
      openKey: "codex:same-id", session: fromWireSteeringSession({ agent: "codex", key: "codex:same-id", ...extra }),
      paneStatus: "no_pane", paneDetail: "No registered terminal pane", paneId: null, answerOpen: false,
      armed: false, postureAuthorized: false, steerState: "idle", steerDetail: "", poll: vi.fn(async () => {}),
    });
  });
  render(<SessionPullout />);
}

beforeEach(() => localStorage.clear());

describe("work leads the plain session", () => {
  it("keeps the known project and report for a working session absent from awaiting coders, by compound key", () => {
    open();
    expect(document.querySelector(".is-session .desk-window-title")?.textContent).toContain("payments-ledger");
    expect(screen.getByText("Added the rollback checkpoint. Checking the migration tests.")).toBeTruthy();
    expect(document.querySelector(".desk-session-terminal")).toBeNull();
    expect(screen.getByTestId("session-controls").closest("details")?.open).toBe(false);
    expect(document.querySelector(".desk-session-footer")?.textContent).not.toMatch(/CLASSIFY|Keep as note|same-id|ARM/);
  });

  it("terminal absence retains the work, names the failure and offers Retry and Back without pane controls", () => {
    open();
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    const terminal = screen.getByTestId("session-terminal");
    expect(terminal.textContent).toContain("Terminal unavailable · no pane on this session");
    expect(terminal.textContent).toContain("No registered terminal pane");
    fireEvent.click(within(terminal).getByRole("button", { name: "Retry" }));
    expect(useSteering.getState().poll).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("session-arm-verb")).toBeNull();
    expect(screen.queryByText("ARM")).toBeNull();
    fireEvent.click(within(terminal).getByRole("button", { name: "Back to session" }));
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(screen.getByText("Added the rollback checkpoint. Checking the migration tests.")).toBeTruthy();
  });

  it("the recorded long plain report gives the body to terminal, then returns with the same identity and receipt", () => {
    const sessions = recording.gets["/api/coders/sessions?include_ended=false"];
    const peek = recording.gets["/api/coders/codex%3Asurface-working/peek?lines=200&raw=1"];
    const report = sessions.sessions[0].session.last_assistant_text;
    act(() => {
      useAgentFlights.setState({ loaded: true, flights: [], sessions: sessions.sessions.map(fromWireSessionRow) });
      useDesk.setState({ items: { ...useDesk.getState().items, coder: [] } });
      useSteering.setState({
        openKey: peek.key, session: fromWireSteeringSession(peek),
        paneStatus: peek.peek.status as PaneStatus, paneDetail: "", paneId: null, answerOpen: false,
        armed: peek.grant.armed, postureAuthorized: false,
        steerState: "refused", steerDetail: "Receipt steering:1", poll: vi.fn(async () => {}),
      });
    });
    render(<SessionPullout />);
    expect(report.length).toBeGreaterThan(2000);
    expect(screen.getByText(report)).toBeTruthy();
    const title = document.querySelector(".is-session .desk-window-title")!.textContent;
    const footer = document.querySelector(".desk-session-footer")!;
    expect(footer.textContent).toContain("Not sent · Receipt steering:1");

    fireEvent.click(screen.getByTestId("session-open-terminal"));
    const terminal = screen.getByTestId("session-terminal");
    expect(terminal.parentElement!.children).toHaveLength(1);
    expect(screen.queryByText(report)).toBeNull();
    expect(screen.queryByTestId("session-head")).toBeNull();
    expect(screen.queryByTestId("session-controls")).toBeNull();
    expect(screen.queryByTestId("session-answer-well")).toBeNull();
    expect(terminal.textContent).toContain("Terminal unavailable · no pane on this session");
    expect(document.querySelector(".is-session .desk-window-title")!.textContent).toBe(title);
    expect(footer.textContent).toContain("Not sent · Receipt steering:1");
    fireEvent.click(within(terminal).getByRole("button", { name: "Retry" }));
    expect(useSteering.getState().poll).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTestId("session-open-terminal"));
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(screen.getByText(report)).toBeTruthy();
    expect(screen.getByTestId("session-controls").closest("details")?.open).toBe(false);
    expect(useSteering.getState().openKey).toBe(peek.key);
    expect(footer.textContent).toContain("Not sent · Receipt steering:1");
  });

  it("opening another agent with the same session id resets the terminal view", () => {
    open();
    fireEvent.click(screen.getByTestId("session-open-terminal"));
    act(() => {
      useSteering.setState({ openKey: "claude:same-id", session: fromWireSteeringSession({ key: "claude:same-id", agent: "claude" }) });
    });
    expect(screen.queryByTestId("session-terminal")).toBeNull();
    expect(document.querySelector(".is-session .desk-window-title")?.textContent).toContain("other-project");
    expect(screen.getByTestId("session-open-terminal").textContent).toBe("Open terminal");
  });

  it("Open shows a pending question once and one answer composer without starting capture", () => {
    open({ question: "Who owns rollback?", blocked: true, lifecycle: "awaiting_response" });
    expect(screen.getAllByText("Who owns rollback?")).toHaveLength(1);
    expect(screen.getAllByRole("textbox", { name: "Answer" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Answer" })).toBeDisabled();
    expect(screen.getByTestId("session-answer-well").textContent).toContain("Terminal unavailable");
  });
});
