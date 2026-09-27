/** PHILO-8-02 — one delete everywhere: the one listener, the selection
 * drop, and the commit on a face change. The glass half reads the real hub
 * (tests/e2e/test_philo8_one_delete_glass.py). */
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { useChairState } from "../chairState";
import { OBJECT_DELETE_REQUEST, verbById } from "../verbRegistry";
import { DeskDeleteHost, DeskDeleteSeat } from "../deleteReceipt";

const deletePrimitive = vi.fn(async () => true);

function request(ref: string) {
  act(() => {
    window.dispatchEvent(new CustomEvent(OBJECT_DELETE_REQUEST, { detail: { ref } }));
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  deletePrimitive.mockClear();
  useChairState.setState({ surface: "floor" });
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      decision: [
        { kind: "decision", id: "a", title: "Probe A" },
        { kind: "decision", id: "b", title: "Probe B" },
      ] as never[],
    },
    selectedIds: ["decision:a"],
    viewMode: "list",
    deletePrimitive: deletePrimitive as never,
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("DeskDeleteHost", () => {
  it("takes the queued object out of the selection (cause 1)", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    expect(useDesk.getState().selectedIds).toEqual([]);
    expect(screen.getByText("Removed Probe A")).toBeTruthy();
    expect(deletePrimitive).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(8500));
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
  });

  it("a second delete commits the first (cause 2)", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    request("decision:b");
    expect(deletePrimitive).toHaveBeenCalledTimes(1);
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
    expect(screen.getByText("Removed Probe B")).toBeTruthy();
    act(() => vi.advanceTimersByTime(8500));
    expect(deletePrimitive).toHaveBeenCalledWith("b", "decision");
  });

  it("a face change commits the pending delete (cause 3)", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    act(() => useChairState.setState({ surface: "chair" }));
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
  });

  it("list to spatial is a face change too", async () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    act(() => useDesk.setState({ viewMode: "spatial" }));
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
    // Round four: "Removal committed" only once the delete has landed.
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    expect(screen.getByText("Removal committed")).toBeTruthy();
  });

  it("a seat that unmounts without a face change keeps the Undo", () => {
    const view = render(<><DeskDeleteHost /><DeskDeleteSeat key="one" /></>);
    request("decision:a");
    view.rerender(<DeskDeleteHost />);
    view.rerender(<><DeskDeleteHost /><DeskDeleteSeat key="two" /></>);
    expect(deletePrimitive).not.toHaveBeenCalled();
    expect(screen.getByText("Removed Probe A")).toBeTruthy();
    act(() => vi.advanceTimersByTime(8500));
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
  });

  it("with no seat mounted (the Chair) the delete is withheld", () => {
    render(<DeskDeleteHost />);
    request("decision:a");
    act(() => vi.advanceTimersByTime(20_000));
    expect(deletePrimitive).not.toHaveBeenCalled();
    expect(useDesk.getState().selectedIds).toEqual(["decision:a"]);
  });

  it("the verb is greyed with its reason where no seat is mounted", () => {
    const del = verbById("object.delete")!;
    const ctx = { selectedRef: "decision:a" };
    expect(del.ghost(ctx)).toBe("Open the Floor or the list");
    const seat = render(<DeskDeleteSeat />);
    expect(del.ghost(ctx)).toBeNull();
    seat.unmount();
    expect(del.ghost(ctx)).toBe("Open the Floor or the list");
  });

  it("a repeated request for one object keeps one Undo that restores it (P1-a)", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    useDesk.setState({ selectedIds: ["decision:a"] });
    request("decision:a");
    expect(deletePrimitive).not.toHaveBeenCalled();
    act(() => screen.getByRole("button", { name: "Undo" }).click());
    act(() => vi.advanceTimersByTime(20_000));
    expect(deletePrimitive).not.toHaveBeenCalled();
  });

  it("a resize that turns the list into the spatial Floor commits", () => {
    const wide = window.innerWidth;
    const many = Array.from({ length: 20 }, (_, n) => ({ kind: "decision", id: `d${n}`, title: `D${n}` }));
    useDesk.setState({
      items: { ...EMPTY_ITEMS, decision: [{ kind: "decision", id: "a", title: "Probe A" }, ...many] as never[] },
      viewMode: "unset" as never,
    });
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 393 });
    try {
      render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
      request("decision:a");
      expect(deletePrimitive).not.toHaveBeenCalled();
      act(() => {
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
        window.dispatchEvent(new Event("resize"));
      });
      expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
    } finally {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: wide });
    }
  });

  it("undo keeps the object", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    act(() => screen.getByRole("button", { name: "Undo" }).click());
    act(() => vi.advanceTimersByTime(20_000));
    expect(deletePrimitive).not.toHaveBeenCalled();
  });

  it("an unknown ref queues nothing", () => {
    render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:missing");
    expect(screen.queryByText(/Removed/)).toBeNull();
    expect(useDesk.getState().selectedIds).toEqual(["decision:a"]);
  });
});
