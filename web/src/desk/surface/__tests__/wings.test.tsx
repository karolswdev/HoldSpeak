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

  it("folds into the shared strip menu when its head allocation is too small", () => {
    const clientWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth");
    const scrollWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollWidth");
    Object.defineProperty(HTMLElement.prototype, "clientWidth", {
      configurable: true,
      get: () => 220,
    });
    Object.defineProperty(HTMLElement.prototype, "scrollWidth", {
      configurable: true,
      get: () => 700,
    });
    try {
      render(
        <SurfaceWings
          wings={[
            { id: "speak", label: "Speak" },
            { id: "journal", label: "Journal" },
            { id: "blocks", label: "Blocks" },
            { id: "learned", label: "Learned" },
            { id: "commands", label: "Voice commands" },
          ]}
          active="speak"
          onChange={() => {}}
          door="Configure"
        />,
      );
      expect(screen.getByTestId("surface-strip-menu")).toBeInTheDocument();
      expect(screen.queryByRole("tablist")).toBeNull();
    } finally {
      if (clientWidth) Object.defineProperty(HTMLElement.prototype, "clientWidth", clientWidth);
      if (scrollWidth) Object.defineProperty(HTMLElement.prototype, "scrollWidth", scrollWidth);
    }
  });
});

