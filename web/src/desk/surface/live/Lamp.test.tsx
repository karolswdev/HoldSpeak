import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { Lamp, type LampState } from "../index";
import css from "./lamp.css?raw";
afterEach(cleanup);
it.each<LampState>(["working","waiting","done","tonight","off"])("names its %s state beside a visible word", state => {
  render(<span data-selected="true"><Lamp state={state} label={`Work: ${state}`} />{state}</span>);
  expect(screen.getByRole("img", {name:`Work: ${state}`})).toHaveAttribute("data-state",state);
  expect(screen.getByText(state)).toBeVisible();
});
it("keeps the light visible on a selected row and steady under reduced motion", () => {
  expect(css).toMatch(/\[data-selected="true"\] \.surface-lamp/);
  expect(css).toMatch(/prefers-reduced-motion: reduce[\s\S]*animation: none/);
  expect(css).not.toMatch(/data-state="waiting"[^}]*animation:/);
});
