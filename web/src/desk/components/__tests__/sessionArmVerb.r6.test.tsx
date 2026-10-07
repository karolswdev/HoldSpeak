// Conductor R6: the session footer's arm verb (the separate rename/kill
// grant in a posture that steers directly) is the library Button with the
// pane as a token, never a raw <button> carrying a sentence (UX-CANON A.1,
// A.3). The press makes the same arming call as before.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { fromWireSteeringSession, useSteering } from "../../steering";

vi.mock("../MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

function open(paneId: string | null, extra: Record<string, unknown> = {}) {
  const arm = vi.fn(async () => {});
  act(() => {
    useSteering.setState({
      openKey: "claude:c1",
      answerOpen: false,
      session: fromWireSteeringSession({ key: "claude:c1", agent: "claude" }),
      paneStatus: "live",
      paneId,
      postureAuthorized: true,
      armed: false,
      operation: { destination: paneId },
      policy: { outcome: "allowed", authority_basis: "control_posture", mode: "yolo" },
      arm,
      ...extra,
    } as never);
  });
  render(<SessionPullout />);
  return arm;
}

describe("the session footer's arm verb (Conductor R6)", () => {
  beforeEach(() => localStorage.clear());

  it("is the library Button with a verb label and the pane as a token", () => {
    open("%0");
    const verb = screen.getByTestId("session-arm-verb");
    expect(verb.tagName).toBe("BUTTON");
    expect(verb.classList.contains("btn")).toBe(true);
    expect(verb.classList.contains("btn--ghost")).toBe(true);
    expect(verb.classList.contains("btn--sm")).toBe(true);
    expect(verb.textContent).toBe("Arm rename/kill");
    expect(screen.getByTestId("session-arm-pane").textContent).toBe("PANE · %0");
    expect(screen.getByTestId("session-arm-pane").classList.contains("surface-token")).toBe(true);
  });

  it("the label carries no sentence", () => {
    open("%0");
    const label = screen.getByTestId("session-arm-verb").textContent!;
    expect(label.split(/\s+/).length).toBeLessThanOrEqual(2);
    expect(label).not.toMatch(/\bfor\b|\band\b|%0/);
    expect(document.body.textContent).not.toMatch(/Arm pane .* for rename and kill/);
  });

  it("an unresolved pane reads as a token", () => {
    open(null);
    expect(screen.getByTestId("session-arm-pane").textContent).toBe("PANE · UNRESOLVED");
  });

  it("the press makes the same arming call: useSteering.arm(), once, no arguments", () => {
    const arm = open("%0");
    fireEvent.click(screen.getByTestId("session-arm-verb"));
    expect(arm).toHaveBeenCalledTimes(1);
    expect(arm).toHaveBeenCalledWith();
  });

  it("armed, the verb gives way to RENAME and KILL", () => {
    open("%0", { armed: true });
    expect(screen.queryByTestId("session-arm-verb")).toBeNull();
    expect(screen.getByText("RENAME")).toBeTruthy();
    expect(screen.getByText("KILL")).toBeTruthy();
  });

  it("the session controls hold no raw <button>: every verb is a library species", () => {
    open("%0");
    const buttons = [...screen.getByTestId("session-controls").querySelectorAll("button")];
    expect(buttons.length).toBeGreaterThan(0);
    for (const b of buttons) {
      const species =
        b.classList.contains("btn") || b.classList.contains("btn--chrome") || b.classList.contains("gadget-transport-key");
      expect(species, `raw button: ${b.outerHTML.slice(0, 120)}`).toBe(true);
    }
  });
});
