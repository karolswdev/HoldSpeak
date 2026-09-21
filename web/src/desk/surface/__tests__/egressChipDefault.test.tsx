/* HS-202-02 job 2 — a badge given nothing says NOT SET, never "This device".
 *
 * 03-interaction-walk.md Appendix B.2 records five prop-less `<EgressChip />`
 * printing "⌂ This device" unconditionally, on faces whose verbs reach
 * GitHub, Jira and remote models: "A wrong badge is worse than a missing
 * one: it is a reassurance." The species default is the source of all five.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EgressChip } from "../gadgets";

describe("EgressChip with no props (HS-202-02)", () => {
  it("renders a NOT SET token", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip?.textContent).toBe("NOT SET");
  });

  it("never claims this device", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip?.textContent).not.toMatch(/this device/i);
    expect(chip?.getAttribute("title") ?? "").not.toMatch(/stays on this device/i);
  });

  it("carries no local scope tone it did not read", () => {
    const { container } = render(<EgressChip />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip?.getAttribute("data-scope")).toBeNull();
  });

  it("still says exactly what a caller gives it", () => {
    render(<EgressChip label="192.168.1.43 · LAN" scope="local" />);
    expect(screen.getByText("192.168.1.43 · LAN")).toBeInTheDocument();
  });
});
