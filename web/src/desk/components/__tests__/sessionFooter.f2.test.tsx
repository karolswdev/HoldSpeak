// Conductor F2 (coordinator ruling on PR #906): the session window's footer
// with a live pane is ONE wrapping row. The policy facts were a <dl> in the
// footer's max-content verbs column and printed one letter per line. jsdom
// does no layout, so the fence is the rendered species plus the CSS that
// holds it: tokens that never wrap inside, a flex footer that wraps between
// them, and the pane said once (the body's facts).
import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import css from "../session-pullout.css?raw";
import { SessionPullout } from "../SessionPullout";
import { fromWireSteeringSession, useSteering } from "../../steering";

vi.mock("../MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

function rule(selector: string): string {
  const at = css.indexOf(`${selector} {`);
  expect(at, `no rule for ${selector}`).toBeGreaterThanOrEqual(0);
  return css.slice(at, css.indexOf("}", at));
}

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
    expect(document.body.textContent!.match(/%0/g)?.length).toBe(2); // the body fact and the Arm pane verb
  });

  it("the CSS: a token never wraps inside; the footer row flows and wraps; the controls scroll on a phone", () => {
    expect(rule(".desk-next .desk-session-policy > .surface-token")).toContain("white-space: nowrap");
    const footer = rule(".desk-next .surface-footer-layout.desk-session-footer");
    expect(footer).toContain("display: flex");
    expect(footer).toContain("flex-wrap: wrap");
    expect(rule(".desk-next .desk-session-controls")).toContain("flex-wrap: wrap");
    expect(css).toMatch(/@media \(max-width: 720px\) \{\s*\/\*[^]*?\*\/\s*\.desk-next \.desk-session-controls \{\s*max-height: 30vh;\s*overflow-y: auto;/);
    // The steer field keeps a readable width in the answer well.
    expect(rule(".desk-next .desk-session-answer .desk-steer-input")).toContain("min-width: 160px");
  });
});
