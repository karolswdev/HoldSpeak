/** PHILO-8-02 — one delete everywhere: the one listener, the selection
 * drop, and the commit on a face change. The glass half reads the real hub
 * (tests/e2e/test_philo8_one_delete_glass.py). */
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";
import { DeskDeleteHost, DeskDeleteSeat } from "../deleteReceipt";

const deletePrimitive = vi.fn(async () => undefined);

function request(ref: string) {
  act(() => {
    window.dispatchEvent(new CustomEvent(OBJECT_DELETE_REQUEST, { detail: { ref } }));
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  deletePrimitive.mockClear();
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      decision: [
        { kind: "decision", id: "a", title: "Probe A" },
        { kind: "decision", id: "b", title: "Probe B" },
      ] as never[],
    },
    selectedIds: ["decision:a"],
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

  it("the last seat leaving commits the pending delete (cause 3)", () => {
    const view = render(<><DeskDeleteHost /><DeskDeleteSeat /></>);
    request("decision:a");
    view.rerender(<DeskDeleteHost />);
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
  });

  it("a face swap commits too: the old seat leaves as the new one comes", () => {
    const view = render(<><DeskDeleteHost /><DeskDeleteSeat key="floor" /></>);
    request("decision:a");
    view.rerender(<><DeskDeleteHost /><DeskDeleteSeat key="list" /></>);
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
    expect(screen.getByText("Removal committed")).toBeTruthy();
  });

  it("with no seat mounted (the Chair) the delete commits at once", () => {
    render(<DeskDeleteHost />);
    request("decision:a");
    expect(deletePrimitive).toHaveBeenCalledWith("a", "decision");
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
