import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ControlsGallery } from "./ControlsGallery";

afterEach(cleanup);

it("the gallery Delete specimen keeps its question through a render and answers once", () => {
  const { rerender } = render(<ControlsGallery />);
  const row = screen.getByText("An honest row").closest(".surface-row") as HTMLElement;
  fireEvent.click(within(row).getByRole("button", { name: "Delete" }));
  rerender(<ControlsGallery />);
  expect(within(row).getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  expect(screen.queryByText(/TWO-STEP FIRED/)).toBeNull();
  fireEvent.click(within(row).getByRole("button", { name: "Delete" }));
  expect(screen.getByText("TWO-STEP FIRED ×1")).toBeInTheDocument();
  expect(within(row).queryByRole("button", { name: "Cancel" })).toBeNull();
});
