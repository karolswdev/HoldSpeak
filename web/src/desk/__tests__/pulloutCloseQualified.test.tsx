// PHILO-13-05 (A4) — close means gone. An object window opened through a
// QUALIFIED ref (`meeting:m1`, `persona:r1`, `intelligence:desk`: the list
// row, the brief, the palette) must leave the store and the DOM when its
// Close gadget is pressed. Before the fix the card closed with the bare
// `o.id` while the store kept the qualified ref, so the card faded to
// opacity 0 and stayed, catching every tap at its old place.
// jsdom renders no opacity and no hit test: the rendered proof is the glass
// fence (story 05 evidence). This test proves the store + DOM half through
// the real render site (DeskApp's pullout mount, PHILO-17: the Floor's list
// view is parked) and the real DeskWindowFrame.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Meeting, Persona } from "../../lib/primitives";
import { EMPTY_ITEMS, type Items } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { useProjections } from "../projections";
import { Pullout } from "../components/Pullout";
import { objectByRef } from "../world";

// PHILO-13-05 fix round: the meeting's conflict recovery is the sibling that
// reports `deleted`; this stand-in presses its real onResolved callback.
vi.mock("../../meetings/MeetingConflictRecovery", () => ({
  MeetingConflictRecovery: ({ onResolved }: { onResolved: (r: { deleted: boolean }) => void }) => (
    <button type="button" onClick={() => onResolved({ deleted: true })}>Resolve as deleted</button>
  ),
}));

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const items: Items = {
  ...EMPTY_ITEMS,
  meeting: [{ kind: "meeting", id: "m1", title: "Q3 kickoff" } as Meeting],
  recipe: [{ kind: "recipe", id: "r1", name: "Scout" } as Persona],
};

beforeEach(() => {
  localStorage.clear();
  usePalette.setState({ open: false });
  useDesk.setState({
    items,
    selectedIds: [],
    divedZone: null,
    pullouts: [],
    editingId: null,
    askOpen: false,
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
  });
  useProjections.setState({ subject_counts: {} });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) })),
  );
});

/** DeskApp's pullout mount (`chairOpenCards`), the one render site. */
function Pullouts() {
  const items = useDesk((s) => s.items);
  const pullouts = useDesk((s) => s.pullouts);
  return (
    <>
      {pullouts.map((p) => {
        const o = objectByRef(items, p.id);
        return o ? <Pullout key={p.id} o={o} pulloutId={p.id} origin={p.origin} /> : null;
      })}
    </>
  );
}

function renderList() {
  return render(
    <MemoryRouter>
      <Pullouts />
    </MemoryRouter>,
  );
}

describe("PHILO-13-05 close means gone", () => {
  for (const [opener, title] of [
    ["meeting:m1", "Q3 kickoff"],
    ["persona:r1", "Scout"],
    ["m1", "Q3 kickoff"],
  ] as const) {
    it(`a window opened as "${opener}" leaves the store and the DOM on Close`, () => {
      renderList();
      act(() => useDesk.getState().openPullout(opener));
      const close = screen.getByRole("button", { name: `Close ${title}` });
      fireEvent.click(close);
      expect(useDesk.getState().pullouts).toEqual([]);
      expect(screen.queryByRole("button", { name: `Close ${title}` })).toBeNull();
    });
  }

  it("the store, the frame and the stacking order agree on one id", () => {
    renderList();
    act(() => useDesk.getState().openPullout("meeting:m1"));
    expect(screen.getByRole("button", { name: "Close Q3 kickoff" })).toBeTruthy();
    expect(useDesk.getState().panelOrder).toContain("pullout:meeting:m1");
    expect(useDesk.getState().panelOrder).not.toContain("pullout:m1");
    // Escape-style close (no id) closes the front card, which is this one.
    act(() => useDesk.getState().closePullout());
    expect(useDesk.getState().pullouts).toEqual([]);
    expect(screen.queryByRole("button", { name: "Close Q3 kickoff" })).toBeNull();
  });

  it("deleting an object opened by its qualified ref drops its card", async () => {
    useDesk.setState({
      items: { ...items, note: [{ kind: "note", id: "n1", title: "Plan" } as never] },
    });
    useDesk.getState().openPullout("note:n1");
    expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual(["note:n1"]);
    await useDesk.getState().deletePrimitive("n1", "note");
    expect(useDesk.getState().pullouts).toEqual([]);
  });

  // PHILO-13-05 fix round (Astra counsel, MISSED): two inherited close
  // callers inside the card bodies closed by the bare `o.id`.
  it("Watch live closes a coder card opened as coder:s1", () => {
    useDesk.setState({
      items: { ...items, coder: [{ kind: "coder", id: "s1", title: "Refactor run", agent: "claude", sessionId: "s1", state: "running" } as never] },
    });
    renderList();
    act(() => useDesk.getState().openPullout("coder:s1"));
    expect(screen.getByRole("button", { name: "Close Refactor run" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Watch live" }));
    expect(useDesk.getState().pullouts).toEqual([]);
    expect(screen.queryByRole("button", { name: "Close Refactor run" })).toBeNull();
  });

  it("a meeting resolved as deleted closes its card opened as meeting:m1", () => {
    renderList();
    act(() => useDesk.getState().openPullout("meeting:m1"));
    fireEvent.click(screen.getByRole("button", { name: "Resolve as deleted" }));
    expect(useDesk.getState().pullouts).toEqual([]);
    expect(screen.queryByRole("button", { name: "Close Q3 kickoff" })).toBeNull();
  });

  // Round three (Tenet 5, UX-CANON A.1): every verb on the coder card is the
  // library Button; a raw <button> is a bounce.
  it("static fence: CoderPullout has no raw <button>", async () => {
    const { readFileSync } = await import("node:fs");
    const { resolve } = await import("node:path");
    const src = readFileSync(resolve(__dirname, "../pullouts/CoderPullout.tsx"), "utf8");
    expect(src.match(/<button\b/g) ?? []).toEqual([]);
  });
});

