// HS-144-04 — compact chrome preserves the existing Go registry menu.
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { __resetSurfaces, registerSurface } from "../shell";
import { DeskMenuBar } from "./DeskMenuBar";

beforeEach(__resetSurfaces);
afterEach(__resetSurfaces);

describe("DeskMenuBar", () => {
  it("marks the registry-derived Go title and launches Meetings through its real menu", () => {
    const opened: Array<string | undefined> = [];
    const off = registerSurface("review-meetings", (scope) => opened.push(scope));
    const { container } = render(<DeskMenuBar />);

    expect(
      container.querySelector('[data-menu-id="go"]'),
    ).toContainElement(screen.getByRole("button", { name: "Go", exact: true }));
    expect(container.querySelectorAll("[data-menu-id]")).toHaveLength(4);

    // A keyboard click exercises the title's existing Enter/Space path.
    fireEvent.click(screen.getByRole("button", { name: "Go", exact: true }));
    const menu = screen.getByRole("menu", { name: "Go menu" });
    expect(menu).toBeVisible();
    fireEvent.click(screen.getByRole("menuitem", { name: /Meetings/ }));

    expect(opened).toEqual([undefined]);
    off();
  });
});
