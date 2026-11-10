import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { GuideNote, guideSeat } from "../GuideNote";
afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
});
it("places a note below or above a part without covering it", () => {
  const win = { left: 0, top: 0, width: 900, height: 600 },
    note = { width: 360, height: 110 };
  const row = { left: 4, top: 90, width: 892, height: 28 };
  const below = guideSeat(win, row, note, 580);
  expect(below.top).toBeGreaterThan(row.top + row.height);
  const bottom = { ...row, top: 500 };
  const above = guideSeat(win, bottom, note, 580);
  expect(above.top + note.height).toBeLessThan(bottom.top);
});
it("uses a free side when a tall part leaves no room above or below", () => {
  const win = { left: 0, top: 0, width: 900, height: 600 };
  for (const part of [
    { left: 50, top: 50, width: 200, height: 480 },
    { left: 600, top: 50, width: 250, height: 480 },
  ]) {
    const note = { width: 360, height: 110 };
    const seat = guideSeat(win, part, note, 580);
    expect(["left", "right"]).toContain(seat.side);
    expect(seat.left + note.width <= part.left || seat.left >= part.left + part.width).toBe(true);
    expect(seat.top).toBeGreaterThanOrEqual(36);
    expect(seat.top + note.height).toBeLessThan(580);
  }
});
it("docks inside a phone window above its status line", () => {
  const seat = guideSeat(
    { left: 0, top: 0, width: 393, height: 700 },
    { left: 4, top: 90, width: 385, height: 44 },
    { width: 377, height: 180 },
    670,
  );
  expect(seat.side).toBe("dock");
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
