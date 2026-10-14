import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSessionRow, useAgentFlights } from "../../agentFlights";
import { fromWireSteeringSession, useSteering } from "../../steering";
import { useDesk } from "../../store";

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

  it("Open shows a pending question once and one answer composer without starting capture", () => {
    open({ question: "Who owns rollback?", blocked: true, lifecycle: "awaiting_response" });
    expect(screen.getAllByText("Who owns rollback?")).toHaveLength(1);
    expect(screen.getAllByRole("textbox", { name: "Answer" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Answer" })).toBeDisabled();
    expect(screen.getByTestId("session-answer-well").textContent).toContain("Terminal unavailable");
  });
});
