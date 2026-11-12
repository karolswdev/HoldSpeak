import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { LiveLevel } from "./LiveLevel";
it("keeps the producer level accessible and clamps invalid values", () => {
  const view = render(<LiveLevel label="Audio level" level={0.6} />);
  expect(screen.getByRole("meter", {name:"Audio level"})).toHaveAttribute("aria-valuenow","0.6");
  expect(document.querySelector("[data-lit]")).toBeTruthy();
  view.rerender(<LiveLevel label="Audio level" level={NaN} expanded />);
  expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow","0");
  expect(document.querySelector("[data-lit]")).toBeNull();
  view.rerender(<LiveLevel label="Audio level" level={2} />);
  expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow","1");
});
