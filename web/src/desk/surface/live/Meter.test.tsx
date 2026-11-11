import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { Meter } from "../index";
import css from "./meter.css?raw";
afterEach(cleanup);
it.each(["working","waiting","parked"])("shows completed and %s segments with step words", state => {
  const {container} = render(<Meter current={2} total={6} state={state} />);
  expect(screen.getByRole("img",{name:"Step 3 of 6"})).toHaveAttribute("data-mode","segments");
  expect([...container.querySelectorAll('i')].map(el=>el.dataset.state)).toEqual(["done","done",state,"planned","planned","planned"]);
});
it("fits long programs into one bar and represents all-done and not-started", () => {
  const {rerender} = render(<Meter current={13} total={20} state="working" />);
  expect(screen.getByRole("img")).toHaveAttribute("data-mode","bar");
  expect(screen.getByRole("img").firstElementChild).toHaveStyle({width:"65%"});
  rerender(<Meter current={-1} total={6} state="planned" />);
  expect(screen.getByRole("img")).toHaveAccessibleName("6 steps, not started");
  rerender(<Meter current={6} total={6} state="merged" />);
  expect(screen.getByRole("img")).toHaveAccessibleName("6 steps done");
});
it("keeps each state visible on selection without moving a row", () => {
  expect(css).toContain('[data-selected="true"] .surface-meter');
  expect(css).toContain('--hs-moss: var(--hs-moss-tint)');
  expect(css).not.toContain('animation:');
});
