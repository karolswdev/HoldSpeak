// Phase 16 — the interior kit: IconGrid `well` (objects inside a window sit
// in a sunken paper well, five across at 900 px and wider, the icon at 40 px
// over a two-line sans name). The Floor's grid has no well.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DeskIcon, IconGrid } from "..";

describe("IconGrid well (Phase 16 kit)", () => {
  it("`well` marks the grid; the icons are the same DeskIcon species the Floor draws", () => {
    render(
      <IconGrid well label="Payments ledger cutover" data-testid="grid">
        <DeskIcon id="m1" kind="meeting" name="Ledger cutover sync" />
        <DeskIcon id="d1" kind="decision" name="Freeze the old ledger on Nov 5" />
      </IconGrid>,
    );
    const grid = screen.getByTestId("grid");
    expect(grid.getAttribute("data-well")).toBe("true");
    expect(grid.getAttribute("role")).toBe("group");
    expect(grid.querySelectorAll(".desk-icon")).toHaveLength(2);
    expect(grid.querySelector(".desk-icon img")?.getAttribute("src")).toBeTruthy();
  });

  it("the Floor's grid draws no well", () => {
    render(<IconGrid label="Floor" data-testid="floor"><DeskIcon id="n1" kind="note" name="Note" /></IconGrid>);
    expect(screen.getByTestId("floor").hasAttribute("data-well")).toBe(false);
  });
});
