// HS-167-03 — SurfaceIdentity vitest: name, chips, purpose fold, outcome, trailing.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SurfaceIdentity } from "../Surface";
import { StateChip } from "../patterns";

describe("SurfaceIdentity", () => {
  it("renders name at the Primary type step", () => {
    render(
      <SurfaceIdentity
        name="payments-platform"
        chips={<StateChip state="active" label="Active" />}
      />,
    );
    expect(screen.getByText("payments-platform")).toBeInTheDocument();
    // The name element carries the primary type step class.
    const name = screen.getByText("payments-platform");
    expect(name.className).toBe("surface-identity-name");
  });

  it("renders chips and trailing", () => {
    render(
      <SurfaceIdentity
        name="test"
        chips={
          <>
            <StateChip state="success" label="Active" />
            <span>REV 9</span>
          </>
        }
        trailing={<span data-testid="trailing">JUST NOW</span>}
      />,
    );
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("REV 9")).toBeInTheDocument();
    expect(screen.getByTestId("trailing")).toBeInTheDocument();
  });

  it("renders purpose inside a Disclosure (folded by default)", () => {
    render(
      <SurfaceIdentity
        name="test"
        chips={<StateChip state="idle" />}
        purpose="Migrate the payment gateway to the new vendor without downtime."
      />,
    );
    // The Disclosure trigger says "more" and is collapsed by default.
    const trigger = screen.getByRole("button", { name: /more/i });
    expect(trigger).toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    // Expand it.
    fireEvent.click(trigger);
    expect(screen.getByText(/Migrate the payment gateway/)).toBeInTheDocument();
  });

  it("renders outcome as a target token row with the target mark", () => {
    render(
      <SurfaceIdentity
        name="test"
        chips={<StateChip state="idle" />}
        outcome="zero-downtime cutover by Q1"
      />,
    );
    const outcome = screen.getByText("zero-downtime cutover by Q1");
    expect(outcome).toBeInTheDocument();
    // The target mark is aria-hidden.
    const mark = outcome.parentElement?.querySelector(
      ".surface-identity-outcome-mark",
    );
    expect(mark).toBeInTheDocument();
    expect(mark?.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders fold content when provided", () => {
    render(
      <SurfaceIdentity
        name="test"
        chips={<StateChip state="idle" />}
        fold={<div data-testid="fold-body">Extra content</div>}
      />,
    );
    expect(screen.getByTestId("fold-body")).toBeInTheDocument();
  });

  it("has the data-testid for the glass rig", () => {
    const { container } = render(
      <SurfaceIdentity name="test" chips={<StateChip state="idle" />} />,
    );
    expect(container.querySelector('[data-testid="surface-identity"]')).toBeTruthy();
  });
});
