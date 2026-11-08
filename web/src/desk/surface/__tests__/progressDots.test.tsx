// ProgressDots: the one row of progress dots (the Walk and the New program
// wizard share it). One dot a step, the current one the pill, done ones filled.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressDots } from "../patterns/ProgressDots";

function states(testId: string): (string | null)[] {
  return Array.from(screen.getByTestId(testId).querySelectorAll(".surface-progress-dot"))
    .map((dot) => dot.getAttribute("data-state"));
}

describe("ProgressDots", () => {
  it("draws one dot a step and the current step as the pill", () => {
    render(<ProgressDots count={4} at={2} data-testid="dots" />);
    expect(states("dots")).toEqual([null, null, "now", null]);
  });

  it("fills the done steps from a predicate or a set", () => {
    render(<>
      <ProgressDots count={4} at={2} done={(at) => at < 2} data-testid="by-predicate" />
      <ProgressDots count={4} at={0} done={new Set([1, 3])} data-testid="by-set" />
    </>);
    expect(states("by-predicate")).toEqual(["done", "done", "now", null]);
    expect(states("by-set")).toEqual(["now", "done", null, "done"]);
  });

  it("says its label as one image, and hides itself without one", () => {
    render(<>
      <ProgressDots count={3} at={0} label="Step 1 of 3" data-testid="named" />
      <ProgressDots count={3} at={0} data-testid="quiet" />
    </>);
    expect(screen.getByRole("img", { name: "Step 1 of 3" })).toBe(screen.getByTestId("named"));
    expect(screen.getByTestId("quiet").getAttribute("aria-hidden")).toBe("true");
  });

  it("passes the caller's class and data attributes through", () => {
    render(<ProgressDots count={2} at={1} className="pg-wiz-progress" data-keeps-title="" data-testid="dots" />);
    const dots = screen.getByTestId("dots");
    expect(dots.className).toBe("surface-progress-dots pg-wiz-progress");
    expect(dots.hasAttribute("data-keeps-title")).toBe(true);
  });
});
