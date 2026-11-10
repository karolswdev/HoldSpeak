import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { RailReference } from "./RailReference";

afterEach(cleanup);
it("picks an item and shows its Mast and Spine in the local specimen", () => {
  render(<RailReference />);
  expect(screen.getByRole("heading", { name: "Release review" })).toBeTruthy();
  const row = screen.getByRole("button", { name: /Read the sources/ });
  fireEvent.click(row);
  expect(row.getAttribute("aria-current")).toBe("true");
  expect(screen.getByRole("heading", { name: "Read the sources" })).toBeTruthy();
  expect(screen.queryByText("0")).toBeNull();
});
