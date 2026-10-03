/* PHILO-13-07 (B2, slice two) — the families outside the compositor's
 * arrays, and the remaining draft fields, return after a reload.
 *
 * Same law as slice one: each fence opens the family through its own store
 * (the app writes `hs.desk.workspace.v1`), reloads the module graph, and
 * mounts the real <ReturningWindows /> (or the real face). No fence writes a
 * hand-built document. Red on the slice-one head 22287ab1.
 */
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const KEY = "hs.desk.workspace.v1";
const stored = () => JSON.parse(localStorage.getItem(KEY) || "{}");

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}
const calls: string[] = [];
function stubHub() {
  calls.length = 0;
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    calls.push(`${init?.method ?? "GET"} ${String(input)}`);
    if (String(input).includes("/dossier")) {
      return json({ kind: "story", source_id: "src-1", project: "atlas-desk", story_id: "ATLAS-1-01", phase: 1, members: [] });
    }
    return json({});
  }));
}
const writes = () => calls.filter((c) => !c.startsWith("GET ") && !c.includes("/subscriptions") && !c.includes("/peek"));

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
  stubHub();
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const TARGET = {
  targetId: "t-1", targetGeneration: "g-1", nodeId: "node-1", label: "agent pane",
  sessionLabel: "atlas", worktreeId: null, agent: "claude",
};

/** The tool inspector and the inline editor are one seat (opening one
 * closes the other, deskSlice.ts:107/:162), so a run opens one of them. */
async function openEverything(seat: "inspector" | "editor" = "inspector") {
  const { useDesk } = await import("../store");
  await import("../returningWindows"); // the watchers
  const { useDeliveryDossier } = await import("../deliveryDossier");
  const { useDeliveryTerminal } = await import("../deliveryTerminal");
  const { useMissionControl } = await import("../missioncontrol");
  const { useSteering } = await import("../steering");
  const { useTrustWindow } = await import("../components/TrustWindow");
  await act(async () => { await useDeliveryDossier.getState().openStory("atlas-desk", "ATLAS-1-01", "src-1"); });
  useDeliveryTerminal.getState().open(TARGET);
  useMissionControl.getState().toggle();
  useSteering.getState().openSession("session-1");
  useTrustWindow.getState().setOpen(true);
  useDesk.getState().openScheduleCreate();
  useDesk.getState().openAsk();
  if (seat === "inspector") useDesk.getState().openToolInspector("project", "p-1");
  else useDesk.getState().openEditor("note:n1");
  return { useDeliveryTerminal, useSteering };
}

async function reloadAndReturn(items?: Record<string, unknown>) {
  vi.resetModules();
  const desk = await import("../store");
  const returning = await import("../returningWindows");
  const stores = {
    desk: desk.useDesk,
    dossier: (await import("../deliveryDossier")).useDeliveryDossier,
    terminal: (await import("../deliveryTerminal")).useDeliveryTerminal,
    mission: (await import("../missioncontrol")).useMissionControl,
    steering: (await import("../steering")).useSteering,
    trust: (await import("../components/TrustWindow")).useTrustWindow,
  };
  const view = render(<returning.ReturningWindows />);
  if (items) await act(async () => { desk.useDesk.setState({ items: items as never, status: {}, updatedAt: Date.now() }); });
  return { ...stores, view };
}

const NOTE = { id: "n1", title: "Ledger risks", bodyMarkdown: "body", tags: [] };

describe("B2 slice two: every remaining family returns after a reload", () => {
  it("dossier, terminal, Mission Control, session, Trust, tool inspector, Schedule, Ask and the editor come back; restore sends no write", async () => {
    const opened = await openEverything();
    const places = stored().places;
    expect(Object.keys(places).filter((k) => k.startsWith("window/")).sort()).toEqual([
      "window/ask", "window/delivery-dossier", "window/delivery-terminal",
      "window/mission-control", "window/schedule-create", "window/session", "window/tool-inspector", "window/trust",
    ]);
    calls.length = 0;

    const after = await reloadAndReturn({ note: [NOTE] });
    await waitFor(() => expect(after.dossier.getState().dossier?.kind).toBe("story"));
    expect(after.dossier.getState().dossier).toMatchObject({ project: "atlas-desk", storyId: "ATLAS-1-01" });
    expect(after.terminal.getState().openTarget).toEqual(TARGET);
    expect(after.mission.getState().open).toBe(true);
    expect(after.steering.getState().openKey).toBe("session-1");
    expect(after.trust.getState().open).toBe(true);
    const s = after.desk.getState();
    expect(s.toolInspector).toEqual({ kind: "project", id: "p-1" });
    expect(s.scheduleCreateWindow).not.toBeNull();
    expect(s.askOpen).toBe(true);
    expect(writes()).toEqual([]);
    after.terminal.getState().close();
    after.steering.getState().closeSession();
    after.view.unmount();
  });

  it("a closed family stays gone after a reload", async () => {
    const opened = await openEverything("editor");
    const { useDesk } = await import("../store");
    const { useDeliveryDossier } = await import("../deliveryDossier");
    const { useMissionControl } = await import("../missioncontrol");
    const { useTrustWindow } = await import("../components/TrustWindow");
    useDeliveryDossier.getState().close();
    opened.useDeliveryTerminal.getState().close();
    useMissionControl.getState().toggle();
    opened.useSteering.getState().closeSession();
    useTrustWindow.getState().setOpen(false);
    useDesk.getState().openToolInspector("project", "p-1");
    expect(stored().places["window/tool-inspector"]).toBeTruthy();
    useDesk.getState().closeToolInspector();
    useDesk.getState().closeScheduleCreate();
    useDesk.getState().closeAsk();
    useDesk.getState().closeEditor();
    expect(Object.keys(stored().places).filter((k) => k.startsWith("window/"))).toEqual([]);

    const after = await reloadAndReturn({ note: [NOTE] });
    expect(after.dossier.getState().dossier).toBeNull();
    expect(after.terminal.getState().openTarget).toBeNull();
    expect(after.mission.getState().open).toBe(false);
    expect(after.steering.getState().openKey).toBeNull();
    expect(after.trust.getState().open).toBe(false);
    expect(after.desk.getState().toolInspector).toBeNull();
    expect(after.desk.getState().scheduleCreateWindow).toBeNull();
    expect(after.desk.getState().askOpen).toBe(false);
    expect(after.desk.getState().editingId).toBeNull();
    after.view.unmount();
  });

  it("the inline editor returns on its object after the first Desk read", async () => {
    await openEverything("editor");
    expect(stored().places["window/editor"]).toBe('"note:n1"');
    const after = await reloadAndReturn({ note: [NOTE] });
    expect(after.desk.getState().editingId).toBe("note:n1");
    expect(after.desk.getState().askOpen).toBe(true);
    after.terminal.getState().close();
    after.steering.getState().closeSession();
    after.view.unmount();
  });

  it("the editor of a record that is gone is not reopened, and its record is forgotten", async () => {
    await openEverything("editor");
    const after = await reloadAndReturn({ note: [] });
    expect(after.desk.getState().editingId).toBeNull();
    expect(stored().places["window/editor"]).toBeUndefined();
    after.terminal.getState().close();
    after.steering.getState().closeSession();
    after.view.unmount();
  });

  it("the Delivery board returns after a reload; Close forgets it", async () => {
    let { DeliveryBoard } = await import("../components/DeliveryBoard");
    let { activateLauncher } = await import("../components/window/launcherRegistry");
    const first = render(<DeliveryBoard />);
    act(() => { expect(activateLauncher("delivery-board")).toBe(true); }); // the Dock's Delivery
    expect(document.querySelector(".desk-dlv-board")).not.toBeNull();
    first.unmount();
    expect(stored().places["window/delivery-board"]).toBe("true");

    vi.resetModules();
    ({ DeliveryBoard } = await import("../components/DeliveryBoard"));
    const second = render(<DeliveryBoard />);
    expect(document.querySelector(".desk-dlv-board")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /^Close/ }));
    await waitFor(() => expect(document.querySelector(".desk-dlv-board")).toBeNull());
    second.unmount();
    expect(stored().places["window/delivery-board"]).toBeUndefined();

    vi.resetModules();
    ({ DeliveryBoard } = await import("../components/DeliveryBoard"));
    ({ activateLauncher } = await import("../components/window/launcherRegistry"));
    const third = render(<DeliveryBoard />);
    expect(document.querySelector(".desk-dlv-board")).toBeNull();
    third.unmount();
  });
});

describe("B2 slice two: the remaining drafts return, per object, and clear on save", () => {
  it("Decide: the unfinished decision title returns per meeting after a reload; it never shows under another meeting", async () => {
    let { MeetingDecideWell } = await import("../../meetings/MeetingDecideWell");
    const first = render(<MeetingDecideWell meetingId="m1" title="Ledger sync" />);
    fireEvent.click(screen.getByRole("button", { name: /Decide/ }));
    fireEvent.change(screen.getByLabelText("Decision title"), { target: { value: "Freeze the old ledger" } });
    first.unmount();
    expect(stored().drafts).toEqual({ "meeting/decide/m1": "Freeze the old ledger" });

    vi.resetModules();
    ({ MeetingDecideWell } = await import("../../meetings/MeetingDecideWell"));
    const second = render(<MeetingDecideWell meetingId="m1" title="Ledger sync" />);
    expect(screen.getByLabelText("Decision title")).toHaveValue("Freeze the old ledger");
    second.unmount();
    const other = render(<MeetingDecideWell meetingId="m2" title="Tracing review" />);
    expect(screen.queryByLabelText("Decision title")).toBeNull();
    other.unmount();
    expect(writes()).toEqual([]);
  });

  it("Decide: a title cleared to empty keeps the well open and empty after a reload (Astra's B2 condition)", async () => {
    let { MeetingDecideWell } = await import("../../meetings/MeetingDecideWell");
    const first = render(<MeetingDecideWell meetingId="m1" title="Ledger sync" />);
    fireEvent.click(screen.getByRole("button", { name: /Decide/ }));
    fireEvent.change(screen.getByLabelText("Decision title"), { target: { value: "Freeze" } });
    fireEvent.change(screen.getByLabelText("Decision title"), { target: { value: "" } });
    first.unmount();
    expect(stored().drafts).toEqual({ "meeting/decide/m1": "" });
    vi.resetModules();
    ({ MeetingDecideWell } = await import("../../meetings/MeetingDecideWell"));
    const second = render(<MeetingDecideWell meetingId="m1" title="Ledger sync" />);
    expect(screen.getByLabelText("Decision title")).toHaveValue("");
    second.unmount();
  });

  it("Schedule recording: the unsaved title and time return after a close and a reload; a landed save clears them", async () => {
    let { useDesk } = await import("../store");
    let { ScheduleCreateWindow } = await import("../components/ScheduleCreateWindow");
    useDesk.getState().openScheduleCreate();
    const first = render(<ScheduleCreateWindow />);
    fireEvent.change(screen.getByRole("textbox", { name: "Title" }), { target: { value: "Ledger dry run" } });
    fireEvent.change(screen.getByLabelText("When"), { target: { value: "2031-01-02T09:30" } });
    act(() => useDesk.getState().closeScheduleCreate());
    first.unmount();
    expect(stored().drafts).toEqual({ "schedule/new/title": "Ledger dry run", "schedule/new/time": "2031-01-02T09:30" });

    vi.resetModules();
    ({ useDesk } = await import("../store"));
    ({ ScheduleCreateWindow } = await import("../components/ScheduleCreateWindow"));
    useDesk.getState().openScheduleCreate();
    const second = render(<ScheduleCreateWindow />);
    expect(screen.getByRole("textbox", { name: "Title" })).toHaveValue("Ledger dry run");
    expect(screen.getByLabelText("When")).toHaveValue("2031-01-02T09:30");
    expect(writes()).toEqual([]);

    useDesk.setState({ createSchedule: vi.fn(async () => true) } as never);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: /^Schedule$/ })); });
    await waitFor(() => expect(stored().drafts).toEqual({}));
    second.unmount();
  });

  it("the meeting SEND form pick returns per meeting after a reload", async () => {
    let { MeetingSendWell } = await import("../../meetings/MeetingSendWell");
    const first = render(<MeetingSendWell meetingId="m1" title="Ledger sync" />);
    fireEvent.change(screen.getByLabelText("Document"), { target: { value: "meeting_digest" } });
    first.unmount();
    expect(stored().places["meeting/form/m1"]).toBe("meeting_digest");

    vi.resetModules();
    ({ MeetingSendWell } = await import("../../meetings/MeetingSendWell"));
    const second = render(<MeetingSendWell meetingId="m1" title="Ledger sync" />);
    expect(screen.getByLabelText("Document")).toHaveValue("meeting_digest");
    second.unmount();
    const other = render(<MeetingSendWell meetingId="m2" title="Tracing review" />);
    expect(screen.getByLabelText("Document")).toHaveValue("meeting_summary");
    other.unmount();
  });

  it("the inline editor: an edit the hub has not kept returns after a reload; restore never saves; a kept save clears it", async () => {
    vi.useFakeTimers();
    let { useDebouncedSave } = await import("../pullouts/editors/useDebouncedSave");
    let { keptEditorPatch } = await import("../pullouts/editors/editorDraft");
    let { useDesk } = await import("../store");
    const update = vi.fn(async () => undefined);
    useDesk.setState({ updatePrimitive: update } as never);
    const first = renderHook(() => useDebouncedSave("note", "n1"));
    act(() => first.result.current({ body_markdown: "Shard backup: ask Priya" }));
    first.unmount(); // reload inside the 450 ms wait
    expect(update).not.toHaveBeenCalled();
    expect(JSON.parse(stored().drafts["editor/note/n1"])).toEqual({ body_markdown: "Shard backup: ask Priya" });

    vi.resetModules();
    ({ useDebouncedSave } = await import("../pullouts/editors/useDebouncedSave"));
    ({ keptEditorPatch } = await import("../pullouts/editors/editorDraft"));
    ({ useDesk } = await import("../store"));
    expect(keptEditorPatch("note", "n1")).toEqual({ body_markdown: "Shard backup: ask Priya" });
    const kept = vi.fn(async (_k: string, id: string) => { useDesk.setState({ keptAt: { [id]: Date.now() + 1 } }); return true; });
    useDesk.setState({ updatePrimitive: kept } as never);
    const second = renderHook(() => useDebouncedSave("note", "n1"));
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(kept).not.toHaveBeenCalled(); // restore never saves
    act(() => second.result.current({ title: "Ledger risks" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(kept).toHaveBeenCalledWith("note", "n1", { body_markdown: "Shard backup: ask Priya", title: "Ledger risks" });
    expect(stored().drafts).toEqual({});
    second.unmount();
  });

  // Astra's P1 on #747. Red on 06116f5c: the landed role write cleared
  // every kept field, so the refused name was lost on reload.
  it("the inline editor: a refused field stays kept when a later write of another field lands", async () => {
    vi.useFakeTimers();
    let { useDebouncedSave } = await import("../pullouts/editors/useDebouncedSave");
    let { useDesk } = await import("../store");
    const answers = [false, true]; // the name write is refused, the role write lands
    const write = vi.fn(async () => answers.shift() ?? true);
    useDesk.setState({ updatePrimitive: write } as never);
    const first = renderHook(() => useDebouncedSave("recipe", "r1"));
    act(() => first.result.current({ name: "Unsaved name" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    act(() => first.result.current({ role: "Saved role" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(write).toHaveBeenNthCalledWith(1, "recipe", "r1", { name: "Unsaved name" });
    expect(write).toHaveBeenNthCalledWith(2, "recipe", "r1", { role: "Saved role" });
    expect(JSON.parse(stored().drafts["editor/recipe/r1"])).toEqual({ name: "Unsaved name" });
    first.unmount();

    vi.resetModules(); // reload: the refused name comes back
    ({ useDebouncedSave } = await import("../pullouts/editors/useDebouncedSave"));
    ({ useDesk } = await import("../store"));
    const { keptEditorPatch } = await import("../pullouts/editors/editorDraft");
    expect(keptEditorPatch("recipe", "r1")).toEqual({ name: "Unsaved name" });
    void useDebouncedSave; void useDesk;
  });

  // Astra's P2 on #747. Red on 06116f5c: `keptTime || defaultTime`.
  it("Schedule recording: an emptied time stays empty after a reload, never the default", async () => {
    let { useDesk } = await import("../store");
    let { ScheduleCreateWindow } = await import("../components/ScheduleCreateWindow");
    useDesk.getState().openScheduleCreate();
    const first = render(<ScheduleCreateWindow />);
    fireEvent.change(screen.getByLabelText("When"), { target: { value: "" } });
    first.unmount();
    expect(stored().drafts).toEqual({ "schedule/new/time": "" });
    vi.resetModules();
    ({ useDesk } = await import("../store"));
    ({ ScheduleCreateWindow } = await import("../components/ScheduleCreateWindow"));
    useDesk.getState().openScheduleCreate();
    const second = render(<ScheduleCreateWindow />);
    expect(screen.getByLabelText("When")).toHaveValue("");
    second.unmount();
  });

  it("the NoteEditor shows the kept edit after a reload", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().setDraft("editor/note/n1", JSON.stringify({ body_markdown: "kept words", tags: ["a", "b"] }));
    vi.resetModules();
    const { useDesk: fresh } = await import("../store");
    fresh.setState({ items: { note: [NOTE] } as never });
    const { NoteEditor } = await import("../pullouts/editors/NoteEditor");
    const view = render(<NoteEditor object={{ kind: "note", id: "n1", title: "Ledger risks", ref: NOTE } as never} onClose={() => {}} />);
    expect(view.container.textContent).toContain("kept words");
    expect(screen.getByRole("textbox", { name: "Tags" })).toHaveValue("a, b");
    view.unmount();
  });
});

describe("B2 slice two: a pullout whose record is gone is dropped at load", () => {
  it("drops a returned pullout whose record no longer exists, keeps the rest", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openPullout("note:n1");
    useDesk.getState().openPullout("note:gone");
    const after = await reloadAndReturn({ note: [NOTE] });
    expect(after.desk.getState().pullouts.map((p) => p.id)).toEqual(["note:n1"]);
    expect(stored().windows.pullouts).toEqual(["note:n1"]);
    after.view.unmount();
  });

  it("keeps it while the read of its collection did not answer (proves nothing yet)", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openPullout("note:gone");
    vi.resetModules();
    const desk = await import("../store");
    const returning = await import("../returningWindows");
    const view = render(<returning.ReturningWindows />);
    await act(async () => { desk.useDesk.setState({ items: { note: [] } as never, status: { note: "unreachable" } as never, updatedAt: Date.now() }); });
    expect(desk.useDesk.getState().pullouts.map((p) => p.id)).toEqual(["note:gone"]);
    view.unmount();
  });
});
