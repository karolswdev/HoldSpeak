/* PHILO-17 — a badge given nothing says nothing, never "This device".
 *
 * 03-interaction-walk.md Appendix B.2 records five prop-less `<EgressChip />`
 * printing "⌂ This device" unconditionally, on faces whose verbs reach
 * GitHub, Jira and remote models: "A wrong badge is worse than a missing
 * one: it is a reassurance." The species default is the source of all five.
 */
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { EgressChip } from "../gadgets";

describe("EgressChip with no props (HS-202-02)", () => {
  it("renders nothing", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip).toBeNull();
  });

  it("never claims this device", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip).toBeNull();
  });

  it("carries no local scope tone it did not read", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip).toBeNull();
  });

  it("still says exactly what a caller gives it", () => {
    render(<EgressChip label="192.168.1.43 · LAN" scope="local" />);
    expect(screen.getByText("192.168.1.43 · LAN")).toBeInTheDocument();
  });

  it("keeps a clickable local chrome chip functional", () => {
    const onClick = vi.fn();
    render(<EgressChip label="THIS DEVICE" scope="local" onClick={onClick} />);
    fireEvent.click(screen.getByRole("button", { name: "THIS DEVICE" }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
