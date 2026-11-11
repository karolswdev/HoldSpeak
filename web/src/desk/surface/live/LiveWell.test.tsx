import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { LiveWell } from "../index";
import css from "./live-well.css?raw";
afterEach(cleanup);
it("keeps a fixed tail, redacts it, and does not announce each screen line", () => {
  const {rerender}=render(<LiveWell label="Screen" show={2} working lines={[{id:"1",text:"read"},{id:"2",text:"test"}]} data-feedback-redact="true" />);
  expect(screen.getByRole("log")).toHaveAttribute("aria-live","off");
  expect(screen.getByRole("log")).toHaveAttribute("data-feedback-redact","true");
  rerender(<LiveWell label="Screen" show={2} working lines={[{id:"1",text:"read"},{id:"2",text:"test"},{id:"3",text:"12 passed"}]} />);
  expect(screen.queryByText("read")).toBeNull();
  expect(screen.getByText("test")).not.toHaveAttribute("data-new");
  expect(screen.getByText("12 passed")).toHaveAttribute("data-new","true");
  expect(screen.getByText("12 passed")).toHaveAttribute("data-cursor","true");
  expect(screen.getByRole("log").style.getPropertyValue('--live-well-lines')).toBe("2");
});
it("shows no work motion or cursor when the producer is stopped", () => {
  const {container}=render(<LiveWell label="Screen" lines={[{id:"1",text:"done"}]} />);
  expect(container.querySelector('[data-new],[data-cursor]')).toBeNull();
  expect(css).toMatch(/prefers-reduced-motion: reduce[\s\S]*animation: none/);
});
