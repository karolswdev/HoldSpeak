// PHILO-13-05 (A4) — close means gone. An object window opened through a
// QUALIFIED ref (`meeting:m1`, `persona:r1`, `intelligence:desk`: the list
// row, the brief, the palette) must leave the store and the DOM when its
// Close gadget is pressed. Before the fix the card closed with the bare
// `o.id` while the store kept the qualified ref, so the card faded to
// opacity 0 and stayed, catching every tap at its old place.
// jsdom renders no opacity and no hit test: the rendered proof is the glass
// fence (story 05 evidence). This test proves the store + DOM half through
// the real render site (DeskListView) and the real DeskWindowFrame.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Meeting, Persona } from "../../lib/primitives";
import { EMPTY_ITEMS, type Items } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { useProjections } from "../projections";
import { DeskListView } from "../components/DeskListView";

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

function renderList() {
  return render(
    <MemoryRouter>
      <DeskListView />
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
});
