// HS-111-08 — SurfaceWings walks with arrows (the grammar the retired
// in-body Tabs species carried, lifted into the ONE head control).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SurfaceWings } from "../wings";
import pulloutCss from "../../components/pullout.css?raw";

const WINGS = [
  { id: "outcomes", label: "Outcomes" },
  { id: "record", label: "Record" },
  { id: "artifacts", label: "Artifacts" },
];

describe("the wings strip", () => {
  it("is a tablist with a roving Tab stop on the active wing", () => {
    render(
      <SurfaceWings wings={WINGS} active="record" onChange={() => {}} />,
    );
    expect(screen.getByRole("tablist")).toBeInTheDocument();
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((tab) => tab.tabIndex)).toEqual([-1, 0, -1]);
  });

  it("ArrowRight/ArrowLeft/Home/End walk the wings", () => {
    const onChange = vi.fn();
    render(<SurfaceWings wings={WINGS} active="record" onChange={onChange} />);
    const record = screen.getByRole("tab", { name: "Record" });
    record.focus();
    fireEvent.keyDown(record, { key: "ArrowRight" });
    expect(onChange).toHaveBeenLastCalledWith("artifacts");
    fireEvent.keyDown(record, { key: "ArrowLeft" });
    expect(onChange).toHaveBeenLastCalledWith("outcomes");
    fireEvent.keyDown(record, { key: "Home" });
    expect(onChange).toHaveBeenLastCalledWith("outcomes");
    fireEvent.keyDown(record, { key: "End" });
    expect(onChange).toHaveBeenLastCalledWith("artifacts");
  });

  it("the gear door is a pressed-state gadget, not a tab", () => {
    const onDoor = vi.fn();
    render(
      <SurfaceWings
        wings={WINGS}
        active="outcomes"
        onChange={() => {}}
        door="Configure"
        doorOpen
        onDoor={onDoor}
      />,
    );
    const door = screen.getByRole("button", { name: "Configure" });
    expect(door).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(door);
    expect(onDoor).toHaveBeenCalled();
  });

  // HS-135-02 L7 — inactive wings read as controls: muted text + wash-1
  // background at rest, escalation to wash-2 on hover.
  it("inactive wing has is-on class only when active", () => {
    render(
      <SurfaceWings wings={WINGS} active="record" onChange={() => {}} />,
    );
    const outcomes = screen.getByRole("tab", { name: "Outcomes" });
    const record = screen.getByRole("tab", { name: "Record" });
    expect(outcomes.className).not.toContain("is-on");
    expect(record.className).toContain("is-on");
  });
});

// HS-135-02 L7 — wing affordance CSS contract: the raw pullout.css
// proves inactive wings have visible fill + muted text, and hover
// escalates to wash-2.
describe("HS-135-02 wing affordance CSS contract", () => {
  it("inactive wing rest state: --text-muted + --wash-1", () => {
    // Find the .desk-next .desk-wing rule (the base, not :hover or .is-on)
    const wingIdx = pulloutCss.indexOf(".desk-next .desk-wing {");
    expect(wingIdx).toBeGreaterThan(-1);
    const wingBlock = pulloutCss.slice(
      wingIdx,
      pulloutCss.indexOf("}", wingIdx) + 1,
    );
    expect(wingBlock).toContain("color: var(--text-muted)");
    expect(wingBlock).toContain("background: var(--wash-1)");
    // Must NOT use --text-faint (too faint for interactive affordance)
    expect(wingBlock).not.toContain("--text-faint");
    // Must NOT have background: none (tabs need a visible fill)
    expect(wingBlock).not.toContain("background: none");
  });

  it("inactive wing hover escalates to --wash-2", () => {
    const hoverIdx = pulloutCss.indexOf(".desk-next .desk-wing:hover");
    expect(hoverIdx).toBeGreaterThan(-1);
    const hoverBlock = pulloutCss.slice(
      hoverIdx,
      pulloutCss.indexOf("}", hoverIdx) + 1,
    );
    expect(hoverBlock).toContain("background: var(--wash-2)");
    expect(hoverBlock).toContain("color: var(--text)");
  });
});
