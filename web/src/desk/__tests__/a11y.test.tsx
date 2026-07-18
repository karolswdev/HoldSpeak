// HS-96-05 — the accessibility contract: focus moves into an opening
// window and returns to its opener on close; Escape inside a window
// closes that window (no modal trap — windows are regions); the shell
// furniture passes an axe sweep at the serious/critical gate.
import { fireEvent, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame, Dock } from "../components/DeskWindow";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
  });
});

function Host({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      <button type="button">opener</button>
      <DeskWindowFrame id="fa" title="Focus test" open={open} onClose={onClose}>
        <button type="button">inside</button>
      </DeskWindowFrame>
      <Dock />
    </>
  );
}

describe("window focus management (no traps)", () => {
  it("opening moves focus into the window; closing returns it", () => {
    const { rerender } = render(<Host open={false} onClose={() => {}} />);
    const opener = screen.getByRole("button", { name: "opener" });
    opener.focus();
    rerender(<Host open onClose={() => {}} />);
    const shell = screen.getByRole("region", { name: "Focus test" });
    expect(document.activeElement).toBe(shell);
    // No trap: focus can leave the window freely.
    screen.getByRole("button", { name: "inside" }).focus();
    opener.focus();
    expect(document.activeElement).toBe(opener);
    rerender(<Host open={false} onClose={() => {}} />);
    expect(document.activeElement).toBe(opener);
  });

  it("Escape inside the window closes it", () => {
    const onClose = vi.fn();
    render(<Host open onClose={onClose} />);
    const shell = screen.getByRole("region", { name: "Focus test" });
    fireEvent.keyDown(shell, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe("the shell furniture passes axe", () => {
  it("window + dock: no serious or critical violations", async () => {
    const { container } = render(<Host open onClose={() => {}} />);
    const results = await axe.run(container, {
      resultTypes: ["violations"],
    });
    const gated = results.violations.filter((v) =>
      ["serious", "critical"].includes(v.impact ?? ""),
    );
    expect(
      gated.map((v) => `${v.id}: ${v.help}`),
    ).toEqual([]);
  });
});
