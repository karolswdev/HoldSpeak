// HS-93-08 — the semantic list mode is the SAME Desk: identical records,
// identical actions (open, select, dive) through the one store, paged
// honestly, and legible to a screen reader.
// HS-111-07 — re-locked to the SurfaceLedger face: 26px mono rows under
// kind bands, Space = Ask-context, ContextMenu = the object WorkMenu.
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Meeting, Note, Persona, KB } from "../../lib/primitives";
import { EMPTY_ITEMS, qualifiedRef, type Items } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { useProjections } from "../projections";
import { allObjects, objectByRef } from "../world";
import { DeskListView, LIST_PAGE } from "./DeskListView";
import { DeskChrome } from "./DeskChrome";
import { DeskToolShelf } from "./DeskToolShelf";

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

describe("HS-111-07 the ledger face: same records", () => {
  it("renders one ledger row per world object with kind band, fact, STATE", () => {
    useProjections.setState({
      subject_counts: { "note:n1": { needs_attention: 2, receipts: 0 } },
    });
    renderList();

    // Every record the world knows appears — including the filed note the
    // spatial root stage hides behind its zone (no stranded object).
    for (const o of allObjects(items)) {
      expect(
        screen.getByRole("button", { name: o.title }),
      ).toBeInTheDocument();
    }

    // Kind bands replace the zone chip strip.
    expect(screen.getByText("MEETINGS")).toBeInTheDocument();
    expect(screen.getByText("NOTES")).toBeInTheDocument();
    expect(screen.getByText("AGENTS")).toBeInTheDocument();

    // The head is a mono fact line, not prose.
    expect(
      screen.getByText("ITEMS 4 · ZONES 1 · ATTN 2"),
    ).toBeInTheDocument();

    // The attention count rides the row as a STATE token.
    expect(
      screen.getByRole("button", { name: "Release checklist" }),
    ).toHaveTextContent("ATTN 2");

    // Zone membership is the row's fact token.
    expect(
      screen.getByRole("button", { name: "Rollout risks" }),
    ).toHaveTextContent("LAUNCH");
  });

  it("opens the SAME pull-out record a floater click opens", () => {
    const { container } = renderList();
    fireEvent.click(screen.getByRole("button", { name: "Release checklist" }));
    const pulloutId = useDesk.getState().pullouts.at(-1)?.id;
    expect(pulloutId).toBe(qualifiedRef("note", "n1"));
    const viaList = objectByRef(items, pulloutId!);
    expect(viaList).toMatchObject({ kind: "note", id: "n1" });
    expect(container.querySelector(".desk-pullout")).not.toBeNull();
  });

  it("Space ropes the SAME ref into the Ask context ([x] token, no checkbox)", () => {
    renderList();
    const row = screen.getByRole("button", { name: "Release checklist" });
    fireEvent.keyDown(row, { key: " " });
    expect(useDesk.getState().selectedIds).toEqual([
      qualifiedRef("note", "n1"),
    ]);
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Release checklist, in Ask context" }),
    ).toHaveTextContent("[x]");
    fireEvent.keyDown(
      screen.getByRole("button", { name: "Release checklist, in Ask context" }),
      { key: " " },
    );
    expect(useDesk.getState().selectedIds).toEqual([]);
  });

  it("the ContextMenu key opens the object WorkMenu on the row", () => {
    renderList();
    const row = screen.getByRole("button", { name: "Release checklist" });
    fireEvent.keyDown(row, { key: "ContextMenu" });
    const menu = screen.getByRole("menu", {
      name: "Release checklist menu",
    });
    expect(menu).toBeInTheDocument();
    fireEvent.click(screen.getByRole("menuitem", { name: "Open" }));
    expect(useDesk.getState().pullouts.at(-1)?.id).toBe("n1");
  });

  it("right-click opens the same object menu", () => {
    renderList();
    fireEvent.contextMenu(
      screen.getByRole("button", { name: "Q3 kickoff" }),
    );
    expect(
      screen.getByRole("menu", { name: "Q3 kickoff menu" }),
    ).toBeInTheDocument();
  });

  it("dives into a zone from the ZONES band and surfaces back", () => {
    renderList();
    fireEvent.click(
      screen.getByRole("button", { name: "Launch zone, 1 item" }),
    );
    expect(useDesk.getState().divedZone).toBe("z1");
    expect(
      screen.getByRole("button", { name: "Rollout risks" }),
    ).toBeInTheDocument();
    // The dived band head is the zone (the fact token repeats it).
    expect(screen.getAllByText("LAUNCH").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "← ALL" }));
    expect(useDesk.getState().divedZone).toBeNull();
  });

  it("keeps the honest count status", () => {
    renderList();
    expect(screen.getByRole("status")).toHaveTextContent("Showing 4 of 4");
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
      "Showing 100 of 1000",
    );
    const more = screen.getByRole("button", { name: "Show 100 more" });
    more.focus();
    fireEvent.click(more);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Showing 200 of 1000",
    );
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Show 100 more" }),
    );
  });

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
  });

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
    const hit = screen.getByRole("button", {
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
