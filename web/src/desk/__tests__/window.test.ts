// The desk-window contract (Phase 93 UI remediation): panel rects persist
// beside the object layout, focus raises without destroying siblings, and
// the one Record verb reduces runtime frames in the store.
import { beforeEach, describe, expect, it } from "vitest";
import { useDesk } from "../store";

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
