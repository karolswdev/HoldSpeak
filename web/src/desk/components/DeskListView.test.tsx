// HS-93-08 — the semantic list mode is the SAME Desk: identical records,
// identical actions (open, select, dive) through the one store, paged
// honestly, and legible to a screen reader.
// PHILO-14 A2 — re-anchored to the ObjectList species: a press or Space =
// Ask context (the selected row, never a `[x]` mark), Enter or a double
// press = open, ContextMenu = the object WorkMenu.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Meeting, Note, Persona, KB } from "../../lib/primitives";
import { EMPTY_ITEMS, qualifiedRef, type Items } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { useProjections } from "../projections";
import { allObjects, objectByRef } from "../world";
import { DeskListView, LIST_PAGE } from "./DeskListView";
import { keyContext } from "../keymap";
import { verbById } from "../verbRegistry";
import { DeskChrome } from "./DeskChrome";
import { DeskToolShelf } from "./DeskToolShelf";

// DeskChrome reads the production runtime bus; the list-mode unit fixture
// exercises its menu state, not a websocket connection.
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
  note: [
    { kind: "note", id: "n1", title: "Release checklist" } as Note,
    { kind: "note", id: "filed1", title: "Rollout risks" } as Note,
  ],
  recipe: [{ kind: "recipe", id: "r1", name: "Scout" } as Persona],
  directory: [
    {
      kind: "directory",
      id: "z1",
      name: "Launch",
      memberIds: ["note:filed1"],
    } as any,
  ],
};

function resetStore(seed: Items) {
  localStorage.clear();
  usePalette.setState({ open: false });
  useDesk.setState({
    items: seed,
    selectedIds: [],
    divedZone: null,
    pullouts: [],
    infoWindows: [],
    editingId: null,
    askOpen: false,
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
  });
  useProjections.setState({ subject_counts: {} });
}

beforeEach(() => {
  resetStore(items);
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
    ),
  );
});

function renderList() {
  return render(
    <MemoryRouter>
      <DeskListView />
    </MemoryRouter>,
  );
}

/** A list row's one verb: its name Button (`<name>, <KIND>[, <when>][, <state>]`). */
function row(name: string) {
  const escape = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return screen.getByRole("button", { name: new RegExp(`^${escape}, `) });
}

/** Space on a button: the browser activates it (a click with no pointer). */
function space(el: HTMLElement) {
  fireEvent.keyDown(el, { key: " " });
  fireEvent.keyUp(el, { key: " " });
  fireEvent.click(el, { detail: 0 });
}

describe("PHILO-14 A2 the list is a list: same records", () => {
  it("renders one ObjectList row per world object: Name, Kind, When, State", () => {
    useProjections.setState({
      subject_counts: { "note:n1": { needs_attention: 2, receipts: 0 } },
    });
    const { container } = renderList();

    // Every record the world knows appears — including the filed note the
    // spatial root stage hides behind its zone (no stranded object).
    for (const o of allObjects(items)) expect(row(o.title)).toBeInTheDocument();

    // The species' four sort headers, Name sorted ascending.
    const heads = within(screen.getByRole("grid", { name: "Desk items" })).getAllByRole("columnheader");
    expect(heads.map((h) => h.textContent?.replace(/[▲▼]/g, ""))).toEqual(["Name", "Kind", "When", "State"]);
    expect(heads[0]).toHaveAttribute("aria-sort", "ascending");

    // The head is a mono fact line, not prose.
    expect(screen.getByText("4 ITEMS · 1 ZONE · 2 ATTNS")).toBeInTheDocument();

    // The attention count rides the row's State (one lamp + its word).
    expect(row("Release checklist")).toHaveAccessibleName("Release checklist, NOTE, ATTN 2");

    // A filed object names its zone beside its kind (the Floor spans zones).
    expect(row("Rollout risks")).toHaveAccessibleName("Rollout risks, NOTE · LAUNCH");

    // A zone is a row of its own: a press dives.
    expect(row("Launch")).toHaveAccessibleName("Launch, ZONE, 1 ITEM");

    // The text-mode list is gone: no `[ ]` / `[x]` anywhere.
    expect(container.textContent).not.toMatch(/\[ \]|\[x\]/);
  });

  it("Enter opens the SAME pull-out record a floater click opens", () => {
    const { container } = renderList();
    fireEvent.keyDown(row("Release checklist"), { key: "Enter" });
    const pulloutId = useDesk.getState().pullouts.at(-1)?.id;
    expect(pulloutId).toBe(qualifiedRef("note", "n1"));
    const viaList = objectByRef(items, pulloutId!);
    expect(viaList).toMatchObject({ kind: "note", id: "n1" });
    expect(container.querySelector(".desk-pullout")).not.toBeNull();
  });

  it("a double press opens the row", () => {
    renderList();
    fireEvent.doubleClick(row("Q3 kickoff"));
    expect(useDesk.getState().pullouts.at(-1)?.id).toBe(qualifiedRef("meeting", "m1"));
  });

  it("Space ropes the SAME ref into the Ask context: the selected row, no mark", () => {
    const { container } = renderList();
    space(row("Release checklist"));
    expect(useDesk.getState().selectedIds).toEqual([qualifiedRef("note", "n1")]);
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    // The mark is the row's selected state plus words for a screen reader.
    expect(screen.getByRole("button", { name: "Release checklist, NOTE, in Ask context" })).toBeInTheDocument();
    const selectedRow = container.querySelector(`.object-list-row[data-object-id="note:n1"]`)!;
    expect(selectedRow).toHaveAttribute("aria-selected", "true");
    expect(selectedRow).toHaveAttribute("data-selected", "true");
    expect(container.textContent).not.toMatch(/\[ \]|\[x\]/);
    space(screen.getByRole("button", { name: "Release checklist, NOTE, in Ask context" }));
    expect(useDesk.getState().selectedIds).toEqual([]);
    expect(selectedRow).toHaveAttribute("aria-selected", "false");
  });

  it("two refs in the Ask context are two selected rows", () => {
    const { container } = renderList();
    space(row("Release checklist"));
    space(row("Q3 kickoff"));
    const on = [...container.querySelectorAll(`.object-list-row[aria-selected="true"]`)].map((r) => r.getAttribute("data-object-id"));
    expect(on.sort()).toEqual(["meeting:m1", "note:n1"]);
    expect(screen.getByRole("button", { name: "Q3 kickoff, MEETING, in Ask context" })).toBeInTheDocument();
  });

  // Inventory 2026-10-03: a pointer could not select a list row (a press
  // opened it), so the Object menu stayed all ghost. A press selects now.
  it("a press selects the row and does not open it", () => {
    const { container } = renderList();
    fireEvent.click(row("Release checklist"), { detail: 1 });
    expect(useDesk.getState().selectedIds).toEqual([qualifiedRef("note", "n1")]);
    expect(useDesk.getState().pullouts).toEqual([]);
    expect(container.querySelector(".desk-pullout")).toBeNull();
    // The Object menu reads this selection: its verbs are live.
    const ctx = keyContext();
    expect(ctx.selectedRef).toBe(qualifiedRef("note", "n1"));
    expect(verbById("object.info")!.ghost(ctx)).toBeNull();
    expect(verbById("object.open")!.ghost(ctx)).toBeNull();
    fireEvent.click(row("Release checklist"), { detail: 1 });
    expect(useDesk.getState().selectedIds).toEqual([]);
    expect(verbById("object.info")!.ghost(keyContext())).toBe("Select an object");
  });

  it("Get Info on a selected row opens its Info window in list mode", () => {
    const { container } = renderList();
    fireEvent.click(row("Release checklist"), { detail: 1 });
    act(() => verbById("object.info")!.run(keyContext()));
    const info = container.querySelector(".desk-info-window");
    expect(info).not.toBeNull();
    expect(info!.getAttribute("aria-label") ?? info!.textContent).toContain("Release checklist");
  });

  // Found on the glass: Get Info on a decision threw "Unknown HoldSpeak
  // product term: decision" and the whole desk fell to the reset screen.
  it("Get Info opens for a kind the product-language registry does not hold", () => {
    resetStore({
      ...items,
      decision: [{ kind: "decision", id: "d1", title: "Freeze the old ledger" } as never],
      workbench: [{ kind: "workbench", id: "w1", name: "Cutover bench" } as never],
    });
    const { container } = renderList();
    for (const [name, word] of [["Freeze the old ledger", "Decision"], ["Cutover bench", "Workbench"]]) {
      fireEvent.contextMenu(row(name));
      fireEvent.click(screen.getByRole("menuitem", { name: "Get Info" }));
      const info = [...container.querySelectorAll(".desk-info-window")].at(-1)!;
      expect(info.querySelector(".info-kind")?.textContent).toBe(word);
    }
    expect(container.querySelectorAll(".desk-info-window")).toHaveLength(2);
  }, 15000);

  // Astra on #794: a Filed zone link opened a zone window the list does not
  // mount. In list mode it dives into that zone.
  it("a Filed zone in Get Info dives into that zone in list mode", () => {
    renderList();
    act(() => useDesk.getState().openInfoWindow(qualifiedRef("note", "filed1")));
    const info = document.querySelector(".desk-info-window") as HTMLElement;
    fireEvent.click(within(info).getByRole("button", { name: /Launch/ }));
    expect(useDesk.getState().divedZone).toBe("z1");
    expect(useDesk.getState().zoneWindows ?? []).toEqual([]);
  });

  // Astra on #794: Rename sent `{name}` to a decision (200, title kept) and
  // PUT to a thread (405). Each kind sends its own field by its own method.
  it("Rename sends title to a decision by PUT and to a thread by PATCH", async () => {
    resetStore({
      ...items,
      decision: [{ kind: "decision", id: "d1", title: "Freeze the old ledger" } as never],
      thread: [{ kind: "thread", id: "t1", title: "Cutover thread" } as never],
    });
    const fetchMock = vi.fn((_input: RequestInfo | URL, _init?: RequestInit) =>
      Promise.resolve(new Response("{}", { status: 200, headers: { "content-type": "application/json" } })));
    vi.stubGlobal("fetch", fetchMock);
    const { container } = renderList();
    for (const [ref, title, next] of [["decision:d1", "Freeze the old ledger", "Freeze on Nov 6"], ["thread:t1", "Cutover thread", "Cutover talk"]]) {
      act(() => useDesk.getState().openInfoWindow(ref));
      const info = [...container.querySelectorAll(".desk-info-window")].at(-1)!;
      fireEvent.click(within(info as HTMLElement).getByTitle("Rename"));
      const field = within(info as HTMLElement).getByRole("textbox", { name: "Name" });
      fireEvent.change(field, { target: { value: next } });
      fireEvent.keyDown(field, { key: "Enter" });
      expect(title).not.toBe(next);
    }
    await vi.waitFor(() => expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "PUT" || init?.method === "PATCH")).toHaveLength(2));
    const writes = fetchMock.mock.calls
      .filter(([, init]) => init?.method === "PUT" || init?.method === "PATCH")
      .map(([input, init]) => [String(input), init!.method, JSON.parse(String(init!.body))]);
    expect(writes).toEqual([
      ["/api/decisions/d1", "PUT", { title: "Freeze on Nov 6" }],
      ["/api/threads/t1", "PATCH", { title: "Cutover talk" }],
    ]);
  });

  it("Get Info from the row's own menu opens the Info window", () => {
    const { container } = renderList();
    fireEvent.contextMenu(row("Q3 kickoff"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Get Info" }));
    expect(container.querySelector(".desk-info-window")).not.toBeNull();
  });

  it("the ContextMenu key opens the object WorkMenu on the row", () => {
    renderList();
    fireEvent.keyDown(row("Release checklist"), { key: "ContextMenu" });
    const menu = screen.getByRole("menu", {
      name: "Release checklist menu",
    });
    expect(menu).toBeInTheDocument();
    fireEvent.click(screen.getByRole("menuitem", { name: "Open" }));
    expect(useDesk.getState().pullouts.at(-1)?.id).toBe("n1");
  });

  it("right-click opens the same object menu", () => {
    renderList();
    fireEvent.contextMenu(row("Q3 kickoff"));
    expect(
      screen.getByRole("menu", { name: "Q3 kickoff menu" }),
    ).toBeInTheDocument();
  });

  it("dives into a zone from its row and surfaces back", () => {
    renderList();
    fireEvent.click(row("Launch"), { detail: 1 });
    expect(useDesk.getState().divedZone).toBe("z1");
    expect(row("Rollout risks")).toBeInTheDocument();
    // The dived census names the zone.
    expect(screen.getByText(/LAUNCH ·/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "ALL" }));
    expect(useDesk.getState().divedZone).toBeNull();
  });

  it("keeps the honest count status", () => {
    renderList();
    expect(screen.getByRole("status")).toHaveTextContent("4 SHOWN OF 4");
  });

  it("keeps repository roadmaps out of the ordinary root list", () => {
    resetStore({
      ...items,
      roadmap: [
        {
          kind: "roadmap",
          id: "roadmap:holdspeak",
          title: "HoldSpeak — Roadmap",
          slug: "holdspeak",
          name: "HoldSpeak — Roadmap",
          phaseCount: 1,
          currentPhase: 140,
          currentPhaseTitle: "First sentence",
          storiesDone: 0,
          storiesTotal: 1,
          health: "green",
          issues: [],
          nextStoryId: null,
        },
      ] as any,
    });

    renderList();

    expect(screen.queryByRole("button", { name: /^HoldSpeak — Roadmap/ })).toBeNull();
    expect(screen.getByText("4 ITEMS · 1 ZONE")).toBeInTheDocument();
  });
});

describe("HS-93-08 pagination at 1,000 items", () => {
  const bigItems: Items = {
    ...EMPTY_ITEMS,
    note: Array.from({ length: 999 }, (_, i) => ({
      kind: "note" as const,
      id: `bn${i}`,
      title: `Note ${i}`,
    } as Note)),
    kb: [{ kind: "kb" as const, id: "needle", name: "Meridian launch brief" } as KB],
  };

  beforeEach(() => resetStore(bigItems));

  it("pages by 100 with an honest count and no focus loss", () => {
    renderList();
    expect(screen.getByRole("status")).toHaveTextContent(
      "100 SHOWN OF 1000",
    );
    const more = screen.getByRole("button", { name: "Show 100 more" });
    more.focus();
    fireEvent.click(more);
    expect(screen.getByRole("status")).toHaveTextContent(
      "200 SHOWN OF 1000",
    );
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Show 100 more" }),
    );
  }, 15000);

  it("settles focus on the count when the last page lands", () => {
    resetStore({
      ...EMPTY_ITEMS,
      note: Array.from({ length: 150 }, (_, i) => ({
        kind: "note" as const,
        id: `sn${i}`,
        title: `Small ${i}`,
      } as Note)),
    });
    renderList();
    const more = screen.getByRole("button", { name: "Show 50 more" });
    more.focus();
    fireEvent.click(more);
    expect(
      screen.queryByRole("button", { name: /Show .* more/ }),
    ).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("status"));
  }, 15000);

  it("deck search reaches items no page has rendered yet", () => {
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    fireEvent.change(
      screen.getByPlaceholderText("Search tools and Desk items"),
      { target: { value: "Meridian" } },
    );
    const hit = screen.getByRole("option", {
      name: /Meridian launch brief/,
    });
    fireEvent.click(hit);
    expect(useDesk.getState().pullouts.at(-1)?.id).toBe(
      qualifiedRef("kb", "needle"),
    );
  });
});

describe("HS-93-08 chrome toggle", () => {
  beforeEach(() => {
    resetStore(items);
    useDesk.setState({ viewMode: "spatial" });
  });

  it("List is a pressed-state toggle persisted to storage and URL", () => {
    render(
      <MemoryRouter>
        <DeskChrome />
      </MemoryRouter>,
    );
    // HS-100-11: the toggle lives in the HoldSpeak menu now.
    fireEvent.click(screen.getByRole("button", { name: "HoldSpeak" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "List view" }));
    expect(useDesk.getState().viewMode).toBe("list");
    expect(localStorage.getItem("hs.desk.view")).toBe("list");
    expect(window.location.search).toContain("view=list");
    fireEvent.click(screen.getByRole("button", { name: "HoldSpeak" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Spatial view" }));
    expect(localStorage.getItem("hs.desk.view")).toBe("spatial");
    expect(window.location.search).not.toContain("view=list");
  });
});
