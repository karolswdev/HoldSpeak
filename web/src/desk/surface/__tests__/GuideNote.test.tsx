import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { GuideNote, guideSeat } from "../GuideNote";
afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
});
it("keeps one bottom seat as the guide changes parts, flipping only for an intersecting ring", () => {
  const win = {left: 0, top: 0, width: 900, height: 600}, note = {width: 360, height: 136};
  const first = guideSeat(win, {left: 4, top: 90, width: 892, height: 28}, note, 580);
  expect(guideSeat(win, {left: 4, top: 40, width: 100, height: 32}, note, 580)).toEqual(first);
  const obstructed = guideSeat(win, {left: 650, top: 500, width: 150, height: 32}, note, 580);
  expect(first.side).toBe("bottom");
  expect(obstructed.side).toBe("top");
  expect(obstructed.left).toBe(first.left);
  expect(obstructed.top + note.height).toBeLessThan(500);
});
it("keeps the seat within the visible part of a partly off-screen window", () => {
  const visible={left:0,top:36,width:600,height:544};
  const seat=guideSeat({left:0,top:0,width:900,height:600},null,{width:360,height:136},580,visible);
  expect(seat.left+seat.width).toBeLessThan(600);
  expect(seat.top+136).toBeLessThan(580);
});
it("docks inside a phone window above its status line", () => {
  const seat = guideSeat(
    { left: 0, top: 0, width: 393, height: 700 },
    { left: 4, top: 90, width: 385, height: 44 },
    { width: 377, height: 180 },
    670,
  );
  expect(seat.side).toBe("bottom");
  expect(seat.top + 180).toBeLessThan(670);
  expect(seat.left).toBeGreaterThanOrEqual(8);
});
it("portals its ring and wrapping note into the owner, with kit verbs", () => {
  const owner = document.createElement("div");
  document.body.appendChild(owner);
  const target = document.createElement("div");
  owner.appendChild(target);
  const next = vi.fn();
  render(
    <GuideNote
      owner={owner}
      target={target}
      words="Choose a decision. Its text shows below the list."
      count="2 of 3"
      onStop={vi.fn()}
      onNext={next}
    />,
  );
  expect(owner.querySelector("[data-guide-layer]")).toBeTruthy();
  expect(screen.getByTestId("walk-caption")).toHaveTextContent(
    "Its text shows below",
  );
  const button = screen.getByRole("button", { name: "Next" });
  expect(button).toHaveClass("btn");
  fireEvent.click(button);
  expect(next).toHaveBeenCalledOnce();
});
