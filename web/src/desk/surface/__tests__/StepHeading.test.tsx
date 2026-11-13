/* StepHeading: one numbered step of a setup. The number is in a circle; a done
 * step shows a check; a later step is dimmed and names what it waits for. */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { StepHeading } from "..";

afterEach(cleanup);

describe("StepHeading", () => {
  it("names the step, its state and what a later step waits for", () => {
    render(
      <>
        <StepHeading number={1} title="Make a bot" state="done" testId="one" />
        <StepHeading number={2} title="Paste its token" testId="two" />
        <StepHeading number={3} title="Connect your chat" state="later" after="After step 2" testId="three" />
      </>,
    );
    expect(screen.getByRole("heading", { name: "Step 1, done: Make a bot" })).toHaveAttribute("data-state", "done");
    expect(screen.getByRole("heading", { name: "Step 2: Paste its token" })).toHaveAttribute("data-state", "current");
    expect(screen.getByRole("heading", { name: "Step 3, later: Connect your chat" })).toHaveAttribute("data-state", "later");
    expect(screen.getByTestId("one").textContent).toBe("✓Make a bot");
    expect(screen.getByTestId("two").textContent).toBe("2Paste its token");
    expect(screen.getByTestId("three").textContent).toBe("3Connect your chatAfter step 2");
  });

  it("shows no pill for a step that is not later", () => {
    render(<StepHeading number={2} title="Paste its token" after="After step 1" testId="two" />);
    expect(screen.getByTestId("two").textContent).toBe("2Paste its token");
  });
});
