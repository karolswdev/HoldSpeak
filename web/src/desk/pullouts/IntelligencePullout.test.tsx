import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { IntelligencePullout } from "./IntelligencePullout";
import { PULLOUT_CONTENT } from "./registry";

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

describe("HS-128-01 Intelligence pullout", () => {
  beforeEach(() => localStorage.clear());

  it("registers the Intelligence primitive in the pullout registry", () => {
    expect(PULLOUT_CONTENT.intelligence).toBe(IntelligencePullout);
  });

  it("opens on Brief and changes the active view", () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.getByText("Brief view")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Brief" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(screen.getByText("Follow-Through view")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Follow-through" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("restores the last selected view after reopening", () => {
    const first = render(
      <IntelligencePullout object={object} onClose={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.getByText("Receipts view")).toBeInTheDocument();
  });
});
