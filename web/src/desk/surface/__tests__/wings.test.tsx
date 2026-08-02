// HS-111-08 — SurfaceWings walks with arrows (the grammar the retired
// in-body Tabs species carried, lifted into the ONE head control).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SurfaceWings } from "../wings";

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
});
