/* PHILO-13-07 (B2) — the Desk remembers.
 *
 * Every fence reads the document the app itself writes
 * (`hs.desk.workspace.v1` in the real localStorage), then reloads the module
 * graph (`vi.resetModules` + a fresh import: the store reads the document
 * again, as a page reload does). No fence writes a hand-built document.
 *
 * Red on main (e9b01e22): pullouts, Info/Roadmap/Repository/Workbench
 * windows, minimized state, the Chair's closed windows and the screen were
 * session-only; the People 1:1 note, the Room update body and the Thought
 * body were component state.
 */
import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ProjectUpdate } from "../../features/project-room/update/model";
import type { Thought } from "../thoughts";

const KEY = "hs.desk.workspace.v1";
const stored = () => JSON.parse(localStorage.getItem(KEY) || "{}");

/** A page reload: drop every module, import the store graph again. */
async function reload() {
  vi.resetModules();
  return import("../store");
}

const fetchUpdates = vi.fn();
const saveUpdate = vi.fn();
vi.mock("../../features/project-room/update/api", () => ({
  fetchUpdates: (...args: unknown[]) => fetchUpdates(...args),
  saveUpdate: (...args: unknown[]) => saveUpdate(...args),
}));

vi.mock("../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../thoughts")>()),
  saveThoughtWorking: vi.fn(),
  saveThoughtWorkingInWorkspace: vi.fn(),
}));

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("B2: every open window returns after a reload", () => {
  it("pullouts return in open order; a closed one stays gone", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openPullout("decision:d1");
    useDesk.getState().openPullout("note:n1");
    useDesk.getState().openPullout("meeting:m1");
    useDesk.getState().closePullout("note:n1");
    expect(stored().windows.pullouts).toEqual(["decision:d1", "meeting:m1"]);

    const fresh = await reload();
    expect(fresh.useDesk.getState().pullouts.map((p) => p.id)).toEqual(["decision:d1", "meeting:m1"]);
  });

  it("Info, Roadmap, Repository and Workbench windows return; a closed one stays gone", async () => {
    const { useDesk } = await import("../store");
    const s = useDesk.getState();
    s.openInfoWindow("decision:d1");
    s.openRoadmapWindow("atlas-desk");
    s.openRepositoryWindow("repo-1");
    s.openWorkbenchWindow("wb-1");
    s.openWorkbenchWindow("wb-2");
    useDesk.getState().closeWorkbenchWindow("wb-2");

    const fresh = (await reload()).useDesk.getState();
    expect(fresh.infoWindows.map((w) => w.ref)).toEqual(["decision:d1"]);
    expect(fresh.roadmapWindows.map((w) => w.slug)).toEqual(["atlas-desk"]);
    expect(fresh.repositoryWindows.map((w) => w.id)).toEqual(["repo-1"]);
    expect(fresh.workbenchWindows.map((w) => w.id)).toEqual(["wb-1"]);
  });

  it("a minimized window comes back minimized; a moved window comes back where it was; order and zoom return", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openPullout("decision:d1");
    useDesk.getState().openInfoWindow("decision:d1");
    useDesk.getState().setPanelRect("pullout:decision:d1", { x: 10, y: 54, w: 420, h: 300 }, true);
    useDesk.getState().minimizePanel("info:decision:d1");
    useDesk.getState().toggleMaximizePanel("pullout:decision:d1");

    const fresh = (await reload()).useDesk.getState();
    expect(fresh.panelMin).toEqual(["info:decision:d1"]);
    expect(fresh.panelRects["pullout:decision:d1"]).toEqual({ x: 10, y: 54, w: 420, h: 300 });
    expect(fresh.panelMax).toContain("pullout:decision:d1");
    expect(fresh.panelOrder.at(-1)).toBe("pullout:decision:d1");
  });

  it("a window that comes back minimized stays minimized when its frame mounts; a stale minimize is dropped", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openPullout("decision:d1");
    useDesk.getState().minimizePanel("pullout:decision:d1");
    useDesk.getState().minimizePanel("delivery-board"); // a window that does not return
    const fresh = (await reload()).useDesk;
    expect(fresh.getState().panelMin).toEqual(["pullout:decision:d1"]);
    const { DeskWindowFrame } = await import("../components/DeskWindow");
    const view = render(<DeskWindowFrame id="pullout:decision:d1" title="D1" open onClose={() => {}}>d</DeskWindowFrame>);
    expect(fresh.getState().panelMin).toEqual(["pullout:decision:d1"]);
    view.unmount();
  });

  it("opening a window that came back minimized brings it to the front", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().openInfoWindow("decision:d1");
    useDesk.getState().minimizePanel("info:decision:d1");
    const fresh = (await reload()).useDesk;
    fresh.getState().openInfoWindow("decision:d1");
    expect(fresh.getState().panelMin).toEqual([]);
    expect(fresh.getState().panelOrder.at(-1)).toBe("info:decision:d1");
  });

  it("a closed Chair window stays closed; the phone's window returns", async () => {
    const chair = await import("../chair/chairWindows");
    chair.openChairWindow("chair:week");
    chair.closeChairWindow("chair:brief");
    expect(stored().chair).toEqual({ closed: ["chair:brief"], phone: "chair:week" });

    vi.resetModules();
    const fresh = await import("../chair/chairWindows");
    expect(fresh.isChairWindowOpen("chair:brief")).toBe(false);
    expect(fresh.isChairWindowOpen("chair:week")).toBe(true);
    expect(fresh.useChairWindows.getState().phone).toBe("chair:week");
  });

  it("the screen (Chair or Floor) returns, and the compositor's save keeps it", async () => {
    const { useChairState } = await import("../chairState");
    const { useDesk } = await import("../store");
    useChairState.getState().setSurface("floor");
    useDesk.getState().openPullout("decision:d1"); // a compositor save after it
    expect(stored().screen).toBe("floor");

    vi.resetModules();
    const fresh = await import("../chairState");
    expect(fresh.useChairState.getState().surface).toBe("floor");
  });
});

describe("B2 / B0-F2: a closed sheet (393) leaves the stacking order", () => {
  it("closing a compact window retires it, so after a reload its reopen lands in front of its opener", async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query.includes("max-width: 720px"), media: query, onchange: null,
      addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false,
    })) as typeof window.matchMedia;
    try {
      const { useDesk } = await import("../store");
      const { DeskWindowFrame } = await import("../components/DeskWindow");
      const board = render(<DeskWindowFrame id="delivery-board" title="Delivery" open onClose={() => {}}>b</DeskWindowFrame>);
      const dossier = render(<DeskWindowFrame id="delivery-dossier" title="ATLAS-1-01" open onClose={() => {}}>d</DeskWindowFrame>);
      expect(useDesk.getState().panelOrder).toEqual(["delivery-board", "delivery-dossier"]);
      dossier.unmount(); // Close
      expect(stored().panel.order).toEqual(["delivery-board"]);
      board.unmount();
    } finally {
      window.matchMedia = original;
    }
  });
});

describe("B2: unsent drafts return, per object, and clear on save", () => {
  function json(body: unknown, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  }
  const person = (id: string, name: string) => ({ id, display_name: name, relationship_kind: "direct_report", calendar_links: [] });
  const posted: string[] = [];
  function stubPeople() {
    posted.length = 0;
    const handlers: Record<string, () => Response> = {
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted", sync: "local_only", capture: "notes_only" }),
      "/api/people/relationships": () => json({ relationships: [person("r1", "Priya Nair"), person("r2", "Sam Lee")] }),
      "/api/people/relationships/r1": () => json({ relationship: person("r1", "Priya Nair") }),
      "/api/people/relationships/r2": () => json({ relationship: person("r2", "Sam Lee") }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [{ id: "s1", agenda: [] }] }),
      "/api/people/relationships/r2/one-on-ones": () => json({ one_on_ones: [] }),
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (init?.method === "POST") { posted.push(String(input)); return json({ ok: true }); }
      return (handlers[String(input)] ?? (() => json({})))();
    }));
  }
  const selectedTab = () => screen.getAllByRole("tab").find((t) => t.getAttribute("aria-selected") === "true")?.textContent;

  it("People: the person, the 1:1s tab and the unsent agenda item return after a close and a reload; Add clears it", async () => {
    stubPeople();
    let { PeopleCore } = await import("../../pages/cores/PeopleCore");
    const first = render(<PeopleCore />);
    fireEvent.click(await screen.findByText("Priya Nair"));
    fireEvent.click(await screen.findByRole("tab", { name: "1:1s" }));
    fireEvent.change(screen.getByLabelText("Agenda item"), { target: { value: "Ask about the EU shard backup plan" } });
    first.unmount(); // close mid-typing
    expect(stored().drafts).toEqual({ "people/1on1/r1": "Ask about the EU shard backup plan" });
    expect(posted).toEqual([]);

    vi.resetModules(); // reload
    ({ PeopleCore } = await import("../../pages/cores/PeopleCore"));
    const second = render(<PeopleCore />);
    await waitFor(() => expect(selectedTab()).toBe("1:1s"));
    expect(screen.getByRole("tablist", { name: "Priya Nair lenses" })).toBeInTheDocument();
    expect(screen.getByLabelText("Agenda item")).toHaveValue("Ask about the EU shard backup plan");
    expect(posted).toEqual([]); // restore never sends

    const agenda = screen.getByLabelText("Agenda item").closest(".people-agenda-add") as HTMLElement;
    fireEvent.click(within(agenda).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(stored().drafts).toEqual({}));
    expect(posted).toEqual(["/api/people/one-on-ones/s1/agenda"]);
    second.unmount();
  });

  it("People: a draft for one person never shows for another", async () => {
    stubPeople();
    const { PeopleCore } = await import("../../pages/cores/PeopleCore");
    const view = render(<PeopleCore />);
    fireEvent.click(await screen.findByText("Priya Nair"));
    fireEvent.click(await screen.findByRole("tab", { name: "1:1s" }));
    fireEvent.change(screen.getByLabelText("Agenda item"), { target: { value: "For Priya only" } });
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    fireEvent.click(await screen.findByText("Sam Lee"));
    fireEvent.click(await screen.findByRole("tab", { name: "1:1s" }));
    expect(screen.getByLabelText("Agenda item")).toHaveValue("");
    view.unmount();
  });

  const update = (id: string, body: string) =>
    ({ id, lifecycle: "draft", bodyMd: body, deliveries: [] }) as unknown as ProjectUpdate;

  // Astra's B2 condition (slice one check): an EMPTIED draft is its own
  // state. Red on 22287ab1: setDraft("") deleted the key and the Room fell
  // back to the saved text; UNSAVED disappeared.
  it("Room: a body cleared to empty stays empty and UNSAVED after a reload and a close/reopen; Save clears the draft", async () => {
    fetchUpdates.mockResolvedValue([update("u1", "No focus items")]);
    let { useUpdateController } = await import("../../features/project-room/update/useUpdateController");
    const first = renderHook(() => useUpdateController("p1", () => {}));
    await act(async () => { await first.result.current.enterUpdates(); });
    act(() => first.result.current.openUpdate(update("u1", "No focus items")));
    act(() => first.result.current.handleEditBody(""));
    first.unmount();
    expect(stored().drafts).toEqual({ "room/update-body/u1": "" });

    vi.resetModules(); // reload
    ({ useUpdateController } = await import("../../features/project-room/update/useUpdateController"));
    const second = renderHook(() => useUpdateController("p1", () => {}));
    await waitFor(() => expect(second.result.current.posture).toBe("editor"));
    expect(second.result.current.editBody).toBe("");
    expect(second.result.current.dirty).toBe(true);
    // close (back to the list) and reopen the same update
    await act(async () => { await second.result.current.backToList(); });
    act(() => second.result.current.openUpdate(update("u1", "No focus items")));
    expect(second.result.current.editBody).toBe("");
    expect(second.result.current.dirty).toBe(true);
    expect(saveUpdate).not.toHaveBeenCalled();

    saveUpdate.mockImplementationOnce(async (_id: string, body: string) => update("u1", body));
    await act(async () => { await second.result.current.save(); });
    expect(saveUpdate).toHaveBeenCalledWith("u1", "");
    expect(stored().drafts).toEqual({});
    second.unmount();
  });

  it("every keyed draft: an emptied field is kept as \"\"; forgetting removes it", async () => {
    const { useDesk } = await import("../store");
    useDesk.getState().setDraft("people/1on1/r1", "words");
    useDesk.getState().setDraft("people/1on1/r1", "");
    expect(stored().drafts).toEqual({ "people/1on1/r1": "" });
    const fresh = (await reload()).useDesk;
    expect(fresh.getState().drafts).toEqual({ "people/1on1/r1": "" });
    fresh.getState().setDraft("people/1on1/r1", null);
    expect(stored().drafts).toEqual({});
  });

  it("Room: the update editor and its 111 unsaved characters return after a reload; restore never saves; Save clears", async () => {
    const typed = "Ledger cutover: dry run passed Tuesday; EU shard backup plan due Friday; Priya owns the rollback runbook draft.";
    expect(typed.length).toBe(111);
    fetchUpdates.mockResolvedValue([update("u1", "No focus items"), update("u2", "Other update")]);
    let { useUpdateController } = await import("../../features/project-room/update/useUpdateController");
    const first = renderHook(() => useUpdateController("p1", () => {}));
    await act(async () => { await first.result.current.enterUpdates(); });
    act(() => first.result.current.openUpdate(update("u1", "No focus items")));
    act(() => first.result.current.handleEditBody(typed));
    first.unmount();
    expect(stored().drafts).toEqual({ "room/update-body/u1": typed });
    expect(stored().places).toEqual({ "room/update/p1": "editor:u1" });

    vi.resetModules();
    ({ useUpdateController } = await import("../../features/project-room/update/useUpdateController"));
    const second = renderHook(() => useUpdateController("p1", () => {}));
    await waitFor(() => expect(second.result.current.posture).toBe("editor"));
    expect(second.result.current.current?.id).toBe("u1");
    expect(second.result.current.editBody).toBe(typed);
    expect(second.result.current.dirty).toBe(true);
    expect(saveUpdate).not.toHaveBeenCalled();

    // another update keeps its own body
    act(() => second.result.current.openUpdate(update("u2", "Other update")));
    expect(second.result.current.editBody).toBe("Other update");
    act(() => second.result.current.openUpdate(update("u1", "No focus items")));
    expect(second.result.current.editBody).toBe(typed);

    saveUpdate.mockImplementationOnce(async (_id: string, body: string) => update("u1", body));
    await act(async () => { await second.result.current.save(); });
    expect(stored().drafts).toEqual({});
    second.unmount();
  });

  const thought: Thought = {
    id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
    aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 1,
    working_note: { id: "note-1", title: "Thought", body_markdown: "", tags: [] }, filing_status: "filed",
  } as Thought;

  it("Thought: words the hub has not kept return after a reload as an unsaved edit; restore never saves; a landed save clears them", async () => {
    vi.useFakeTimers();
    let { useThoughtNoteWriter } = await import("../pullouts/editors/useThoughtNoteWriter");
    const thoughts = await import("../thoughts");
    const first = renderHook(() => useThoughtNoteWriter({ thought, onThought: () => {} }));
    act(() => first.result.current.edit({ body: "Shard backup: ask Priya" }));
    first.unmount(); // reload inside the 450 ms wait, before the first save
    expect(thoughts.saveThoughtWorking).not.toHaveBeenCalled();
    expect(JSON.parse(stored().drafts["thought/body/thought-1"]).body).toBe("Shard backup: ask Priya");

    vi.resetModules();
    ({ useThoughtNoteWriter } = await import("../pullouts/editors/useThoughtNoteWriter"));
    const freshThoughts = await import("../thoughts");
    const second = renderHook(() => useThoughtNoteWriter({ thought, onThought: () => {} }));
    expect(second.result.current.draft.body).toBe("Shard backup: ask Priya");
    expect(second.result.current.pending).toBe(true);
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(freshThoughts.saveThoughtWorking).not.toHaveBeenCalled();

    const kept = { ...thought, aggregate_revision: 2, working_revision: 2, working_note: { ...thought.working_note, body_markdown: "Shard backup: ask Priya today" } };
    vi.mocked(freshThoughts.saveThoughtWorking).mockResolvedValueOnce(kept);
    act(() => second.result.current.edit({ body: "Shard backup: ask Priya today" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(freshThoughts.saveThoughtWorking).toHaveBeenCalledTimes(1);
    expect(stored().drafts).toEqual({});
    second.unmount();
  });
});
