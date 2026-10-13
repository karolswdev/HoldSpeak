// Conductor F2 (coordinator ruling on PR #906): the session window's footer
// with a live pane is ONE wrapping row. The policy facts were a <dl> in the
// footer's max-content verbs column and printed one letter per line. The
// fence is the rendered species: tokens, never a facts column, and the pane
// said once (the body's facts).
import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSteeringSession, useSteering } from "../../steering";

vi.mock("../MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

describe("the session footer never squeezes the policy facts (Conductor F2)", () => {
  it.each(["yolo", "neutral"])("live pane, %s posture: tokens, not a facts column; pane once", (mode) => {
    act(() => {
      useSteering.setState({
        openKey: "claude:c1",
        answerOpen: true,
        session: fromWireSteeringSession({ key: "claude:c1", agent: "claude", question: "Q?", blocked: true }),
        paneStatus: "live",
        paneId: "%0",
        postureAuthorized: true,
        armed: false,
        operation: { destination: "%0" },
        policy: { outcome: "allowed", authority_basis: "control_posture", mode },
      } as never);
    });
    render(<SessionPullout />);
    const policy = screen.getByTestId("session-policy");
    expect(policy.querySelector("dl, dt, dd")).toBeNull();
    const tokens = [...policy.querySelectorAll(".surface-token")].map((t) => t.textContent);
    expect(tokens).toEqual([expect.stringMatching(/^AUTHORITY · .+ POSTURE$/), "RECEIPT · EVERY ATTEMPT"]);
    // The pane is said once: in the body's facts, never again in the footer.
    expect(policy.textContent).not.toMatch(/%0|pane/i);
    expect(document.body.textContent!.match(/%0/g)?.length).toBe(2); // the body fact and the arm verb's pane token
  });
});
