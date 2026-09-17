/** HS-200-45 R4, the client half: one debounced refresh per burst of frames.
 *
 * The hub emits one `desk_changed` frame per successful desk write, whoever
 * made it. Before this the desk only learned about its OWN writes (each
 * mutator calls `refresh()` after its own fetch), so a write from a second
 * tab, the iPad, or an agent over MCP was invisible until someone pressed
 * "Refresh from hub".
 */
import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const listeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
const refresh = vi.fn(async () => {});

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    subscribe: (type: string, listener: (frame: { data: unknown }) => void) => {
      const set = listeners.get(type) ?? new Set();
      set.add(listener);
      listeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
}));

vi.mock("../store", () => ({
  useDesk: { getState: () => ({ refresh }) },
}));

import { DeskChangedRefresh, DESK_CHANGED_DEBOUNCE_MS } from "../useDeskChangedRefresh";

function emit(kind: string, id: string, op: string) {
  for (const listener of listeners.get("desk_changed") ?? []) {
    listener({ data: { kind, id, op, origin: "agent" } });
  }
}

describe("desk_changed -> refresh", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    listeners.clear();
    refresh.mockClear();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("re-reads the desk when a frame arrives from another caller", () => {
    render(<DeskChangedRefresh />);
    expect(refresh).not.toHaveBeenCalled();

    act(() => emit("note", "note_1", "create"));
    expect(refresh).not.toHaveBeenCalled(); // trailing edge, not leading

    act(() => {
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS);
    });
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("collapses a burst into ONE re-read", () => {
    render(<DeskChangedRefresh />);

    act(() => {
      for (let i = 0; i < 12; i += 1) emit("note", `note_${i}`, "create");
    });
    act(() => {
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS);
    });

    // A steward run publishing an update, or a zone of notes filed at once,
    // arrives as many frames in a few hundred ms. The desk needs the state
    // AFTER the burst, not one re-read per frame.
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("extends the window when a frame lands during the wait", () => {
    render(<DeskChangedRefresh />);

    act(() => emit("note", "note_1", "create"));
    act(() => {
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS - 50);
    });
    act(() => emit("note", "note_2", "update"));
    act(() => {
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS - 50);
    });
    expect(refresh).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(50);
    });
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("ignores every other frame type", () => {
    render(<DeskChangedRefresh />);

    act(() => {
      for (const listener of listeners.get("state") ?? []) {
        listener({ data: {} });
      }
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS * 2);
    });
    expect(refresh).not.toHaveBeenCalled();
  });

  it("does not re-read after unmount", () => {
    const view = render(<DeskChangedRefresh />);
    act(() => emit("note", "note_1", "create"));
    view.unmount();
    act(() => {
      vi.advanceTimersByTime(DESK_CHANGED_DEBOUNCE_MS * 2);
    });
    expect(refresh).not.toHaveBeenCalled();
  });
});
