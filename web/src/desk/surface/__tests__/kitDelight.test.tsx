/** DELIGHT (2026-10-27, docs/internal/betterment/canvases/delight-2026-10-27.html):
 *  the kit's share of the delight system — the object empty state, the
 *  status-bar lamp that pulses once per save, and the list row that names
 *  its kind for its hue. */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { StatusBar, TickNumber } from "../kit";
import { SurfaceState } from "../Surface";
import { ObjectList } from "../objects/ObjectList";

describe("DELIGHT — the kit", () => {
  it("an empty state with a kind is an object, one line, one verb", () => {
    const onAction = vi.fn();
    const { container } = render(
      <SurfaceState empty emptyKind="meeting" emptyImage="/m.png" emptyLabel="Record or import a meeting" onAction={onAction} actionLabel="Import a recording" />,
    );
    const state = container.querySelector(".surface-state")!;
    expect(state.getAttribute("data-object")).toBe("meeting");
    expect(state.querySelector(".surface-state-object img")?.getAttribute("src")).toBe("/m.png");
    expect(state.querySelector(".surface-state-line")?.textContent).toBe("Record or import a meeting");
    fireEvent.click(screen.getByRole("button", { name: "Import a recording" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("an empty state without a kind keeps the plain form", () => {
    const { container } = render(<SurfaceState empty emptyImage="/m.png" emptyLabel="Nothing here" />);
    expect(container.querySelector(".surface-state-object")).toBeNull();
    expect(container.querySelector(".surface-state-sprite")).not.toBeNull();
  });

  it("the status-bar lamp pulses on a change after the first paint, never on the first paint", () => {
    const bar = (pulse: string | null) => (
      <StatusBar items={[{ key: "save", lamp: "ok", text: "Saved just now", pulse }]} />
    );
    const { container, rerender } = render(bar("2026-10-27T09:00:00Z"));
    const dot = () => container.querySelector(".kit-statusbar-item > .kit-dot")!;
    expect(dot().hasAttribute("data-pulse")).toBe(false);
    rerender(bar(null));
    expect(dot().hasAttribute("data-pulse")).toBe(false);
    rerender(bar("2026-10-27T09:00:05Z"));
    expect(dot().hasAttribute("data-pulse")).toBe(true);
    const first = dot();
    rerender(bar("2026-10-27T09:00:05Z"));
    expect(dot()).toBe(first);
    rerender(bar("2026-10-27T09:00:09Z"));
    expect(dot()).not.toBe(first);
    expect(dot().hasAttribute("data-pulse")).toBe(true);
  });

  it("slice 2: a count ticks (fades in once) when it changes after the first paint, never on the first paint", () => {
    const { container, rerender } = render(<TickNumber value={4} />);
    const tick = () => container.querySelector(".kit-tick")!;
    expect(tick().textContent).toBe("4");
    expect(tick().hasAttribute("data-tick")).toBe(false);
    rerender(<TickNumber value={4} />);
    expect(tick().hasAttribute("data-tick")).toBe(false);
    rerender(<TickNumber value={3} />);
    expect(tick().textContent).toBe("3");
    expect(tick().hasAttribute("data-tick")).toBe(true);
    const first = tick();
    rerender(<TickNumber value={2} />);
    expect(tick()).not.toBe(first);
    expect(tick().textContent).toBe("2");
  });

  it("slice 2: a status item with a tick fades its words in once when its number changes", () => {
    const bar = (n: number) => <StatusBar items={[{ key: "head", lamp: "ask", text: `${n} need you`, tick: n, testId: "head" }]} />;
    const { rerender } = render(bar(8));
    const head = () => screen.getByTestId("head");
    expect(head().textContent).toBe("8 need you");
    expect(screen.getByText("8 need you").hasAttribute("data-tick")).toBe(false);
    rerender(bar(7));
    expect(head().textContent).toBe("7 need you");
    expect(screen.getByText("7 need you").classList.contains("kit-tick")).toBe(true);
    expect(screen.getByText("7 need you").hasAttribute("data-tick")).toBe(true);
  });

  it("a dense list row names its kind (its hue reads from data-kind)", () => {
    const { container } = render(
      <ObjectList label="Mixed" density="dense" sort={{ key: "name", dir: "asc" }} rows={[
        { id: "m1", kind: "meeting", name: "Vendor sync" },
        { id: "d1", kind: "decision", name: "Freeze on Nov 12" },
      ]} />,
    );
    const kinds = [...container.querySelectorAll(".object-list-row")].map((row) => row.getAttribute("data-kind"));
    expect(kinds.sort()).toEqual(["decision", "meeting"]);
  });
});
