// The desk-window contract (Phase 93 UI remediation): panel rects persist
// beside the object layout, focus raises without destroying siblings, and
// the one Record verb reduces runtime frames in the store.
import { beforeEach, describe, expect, it } from "vitest";
import { loadPanelLayout, useDesk } from "../store";

describe("desk windows", () => {
  beforeEach(() => {
    localStorage.clear();
    useDesk.setState({
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      pulloutId: null,
      pulloutBackId: null,
      editingId: null,
      askOpen: false,
      chatPersonaId: null,
      toolInspector: null,
    });
  });

  it("stores a rect ephemerally and persists only when arranged", () => {
    const rect = { x: 40, y: 80, w: 400, h: 480 };
    useDesk.getState().setPanelRect("ask", rect);
    expect(useDesk.getState().panelRects.ask).toEqual(rect);
    expect(localStorage.getItem("hs.desk.panels")).toBeNull();

    useDesk.getState().setPanelRect("ask", rect, true);
    expect(
      JSON.parse(localStorage.getItem("hs.desk.panels") || "{}").rects?.ask,
    ).toEqual(rect);
  });

  it("resetPanelRect forgets the rect and the saved mark", () => {
    useDesk.getState().setPanelRect("pullout", { x: 1, y: 2, w: 400, h: 300 });
    useDesk
      .getState()
      .setPanelRect("ask", { x: 9, y: 9, w: 400, h: 300 }, true);
    useDesk.getState().resetPanelRect("ask");
    expect(useDesk.getState().panelRects.ask).toBeUndefined();
    expect(
      JSON.parse(localStorage.getItem("hs.desk.panels") || "{}").rects?.ask,
    ).toBeUndefined();
    // The other panel's ephemeral rect is untouched.
    expect(useDesk.getState().panelRects.pullout).toBeDefined();
  });

  it("focusPanel moves the id to the front of the order", () => {
    useDesk.getState().focusPanel("ask");
    useDesk.getState().focusPanel("pullout");
    useDesk.getState().focusPanel("ask");
    expect(useDesk.getState().panelOrder).toEqual(["pullout", "ask"]);
  });

  it("the stacking order persists; minimize does not (HS-97-03)", () => {
    useDesk.getState().focusPanel("ask");
    useDesk.getState().focusPanel("pullout");
    useDesk.getState().minimizePanel("ask");
    const raw = JSON.parse(localStorage.getItem("hs.desk.panels") || "{}");
    expect(raw.order).toEqual(["ask", "pullout"]);
    expect(raw.min).toBeUndefined();
    expect(useDesk.getState().panelMin).toEqual(["ask"]);
  });

  it("presentPanel keeps a remembered plane; a new window goes on top", () => {
    useDesk.getState().focusPanel("ask");
    useDesk.getState().focusPanel("pullout");
    useDesk.getState().presentPanel("ask");
    expect(useDesk.getState().panelOrder).toEqual(["ask", "pullout"]);
    useDesk.getState().presentPanel("chat");
    expect(useDesk.getState().panelOrder).toEqual(["ask", "pullout", "chat"]);
  });

  it("retirePanel drops a closed window so a reopen presents on top", () => {
    useDesk.getState().focusPanel("ask");
    useDesk.getState().focusPanel("pullout");
    useDesk.getState().retirePanel("ask");
    expect(useDesk.getState().panelOrder).toEqual(["pullout"]);
    useDesk.getState().presentPanel("ask");
    expect(useDesk.getState().panelOrder).toEqual(["pullout", "ask"]);
  });

  it("a legacy layout payload (with min) loads and is tolerated", () => {
    localStorage.setItem(
      "hs.desk.panels",
      JSON.stringify({
        rects: { ask: { x: 1, y: 2, w: 300, h: 200 } },
        min: ["ask"],
        max: ["pullout"],
      }),
    );
    const loaded = loadPanelLayout();
    expect(loaded.rects.ask).toBeDefined();
    expect(loaded.order).toEqual([]);
    expect(loaded.max).toEqual(["pullout"]);
    expect("min" in loaded).toBe(false);
  });

  it("windows coexist: opening the composer keeps the pull-out open", () => {
    useDesk.getState().openPullout("note:n1");
    useDesk.getState().openAsk();
    expect(useDesk.getState().pulloutId).toBe("note:n1");
    expect(useDesk.getState().askOpen).toBe(true);

    useDesk.getState().openToolInspector("project", "orion");
    expect(useDesk.getState().askOpen).toBe(true);
    expect(useDesk.getState().pulloutId).toBe("note:n1");
    expect(useDesk.getState().toolInspector).toEqual({
      kind: "project",
      id: "orion",
    });
  });
});

describe("one Record verb", () => {
  beforeEach(() => {
    useDesk.setState({
      recording: "idle",
      recordingExternal: false,
      recordingStartedAt: null,
    });
  });

  it("a frame with no local start reads as live elsewhere", () => {
    useDesk.getState().applyRecordingActivity({ state: "meeting_live" });
    expect(useDesk.getState().recording).toBe("recording");
    expect(useDesk.getState().recordingExternal).toBe(true);
    useDesk.getState().applyRecordingActivity({ state: "complete" });
    expect(useDesk.getState().recording).toBe("idle");
    expect(useDesk.getState().recordingStartedAt).toBeNull();
  });

  it("a locally stamped start is not external when its frame lands", () => {
    useDesk.setState({ recording: "busy", recordingStartedAt: Date.now() });
    useDesk.getState().applyRecordingActivity({ state: "meeting_live" });
    expect(useDesk.getState().recording).toBe("recording");
    expect(useDesk.getState().recordingExternal).toBe(false);
  });
});
