// HS-93-08 — the semantic list mode is the SAME Desk: identical records,
// identical actions (open, select, dive) through the one store, paged
// honestly, and legible to a screen reader (roles, names, labels asserted
// by hand; vitest-axe is not a dependency here).
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS, qualifiedRef, type Items } from "../api";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { allObjects, objectByRef, worldObjects } from "../world";
import { DeskListView, LIST_PAGE } from "./DeskListView";
import { DeskChrome } from "./DeskChrome";
import { DeskToolShelf } from "./DeskToolShelf";

const items: Items = {
  ...EMPTY_ITEMS,
  meeting: [{ kind: "meeting", id: "m1", title: "Q3 kickoff" }],
  note: [
    { kind: "note", id: "n1", title: "Release checklist" },
    { kind: "note", id: "filed1", title: "Rollout risks" },
  ],
  recipe: [{ kind: "recipe", id: "r1", name: "Scout" }],
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
  useDesk.setState({
    items: seed,
    selectedIds: [],
    divedZone: null,
    pulloutId: null,
    pulloutBackId: null,
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

describe("HS-93-08 semantic list mode: same records", () => {
  it("renders one row per world object with kind, attention, and zone", () => {
    useProjections.setState({
      subject_counts: { "note:n1": { needs_attention: 2, receipts: 0 } },
    });
    renderList();

    // Every record the world knows appears — including the filed note the
    // spatial root stage hides behind its zone (no stranded object).
    const expected = allObjects(items);
    const rows = screen.getAllByRole("row").slice(1); // minus the header row
    expect(rows).toHaveLength(expected.length);
    for (const o of expected) {
      expect(
        screen.getByRole("button", { name: o.title }),
      ).toBeInTheDocument();
    }

    // Kind labels use the shared product nouns.
    const kickoff = screen.getByRole("button", { name: "Q3 kickoff" });
    expect(kickoff.closest("tr")).toHaveTextContent("Meeting");
    expect(
      screen.getByRole("button", { name: "Scout" }).closest("tr"),
    ).toHaveTextContent("Agent");

    // The attention count rides the same projection subject the floater uses.
    expect(
      screen.getByRole("button", { name: "Release checklist" }).closest("tr"),
    ).toHaveTextContent("2 need attention");

    // Zone membership is a column, resolved from the same directory records.
    expect(
      screen.getByRole("button", { name: "Rollout risks" }).closest("tr"),
    ).toHaveTextContent("Launch");
  });

  it("opens the SAME pull-out record a floater click opens", () => {
    const { container } = renderList();
    fireEvent.click(screen.getByRole("button", { name: "Release checklist" }));
    const pulloutId = useDesk.getState().pulloutId;
    expect(pulloutId).toBe(qualifiedRef("note", "n1"));
    // The spatial DeskObject opens with the bare id; both refs resolve to
    // the identical record through the one lookup.
    const viaList = objectByRef(items, pulloutId!);
    const viaFloater = objectByRef(items, "n1");
    expect(viaList).toMatchObject({ kind: "note", id: "n1" });
    expect(viaFloater).toMatchObject({ kind: "note", id: "n1" });
    // The pull-out window itself renders in list mode.
    expect(container.querySelector(".desk-pullout")).not.toBeNull();
  });

  it("selects the SAME ref shift-click ropes into the Ask context", () => {
    renderList();
    const box = screen.getByRole("checkbox", {
      name: "Select Release checklist for Ask context",
    });
    fireEvent.click(box);
    expect(useDesk.getState().selectedIds).toEqual([
      qualifiedRef("note", "n1"),
    ]);
    // The same Ask bar appears over the list.
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    fireEvent.click(box);
    expect(useDesk.getState().selectedIds).toEqual([]);
  });

  it("dives into a zone and lists exactly the zone's members", () => {
    renderList();
    fireEvent.click(screen.getByRole("button", { name: /Launch/ }));
    expect(useDesk.getState().divedZone).toBe("z1");
    const expected = worldObjects(items, "z1");
    expect(expected.map((o) => o.id)).toEqual(["filed1"]);
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: "Rollout risks" }),
    ).toBeInTheDocument();
    // Surface back to everything.
    fireEvent.click(screen.getByRole("button", { name: "← All" }));
    expect(useDesk.getState().divedZone).toBeNull();
  });

  it("carries the accessible grammar: named table, headers, status", () => {
    renderList();
    expect(
      screen.getByRole("table", { name: "Desk items" }),
    ).toBeInTheDocument();
    const headers = screen
      .getAllByRole("columnheader")
      .map((th) => th.textContent);
    expect(headers).toEqual([
      "Select for Ask context",
      "Item",
      "Kind",
      "Attention",
      "Zone",
    ]);
    expect(screen.getByRole("status")).toHaveTextContent("Showing 4 of 4");
    expect(screen.getByRole("navigation", { name: "Zones" })).toBeVisible();
  });
});

describe("HS-93-08 pagination at 1,000 items", () => {
  const bigItems: Items = {
    ...EMPTY_ITEMS,
    note: Array.from({ length: 999 }, (_, i) => ({
      kind: "note" as const,
      id: `bn${i}`,
      title: `Note ${i}`,
    })),
    kb: [{ kind: "kb" as const, id: "needle", name: "Meridian launch brief" }],
  };

  beforeEach(() => resetStore(bigItems));

  it("pages by 100 with an honest count and no focus loss", () => {
    renderList();
    expect(screen.getAllByRole("row").slice(1)).toHaveLength(LIST_PAGE);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Showing 100 of 1000",
    );
    const more = screen.getByRole("button", { name: "Show 100 more" });
    more.focus();
    fireEvent.click(more);
    expect(screen.getAllByRole("row").slice(1)).toHaveLength(2 * LIST_PAGE);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Showing 200 of 1000",
    );
    // The button survives the click and keeps focus (no keyboard stranding).
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
      })),
    });
    renderList();
    const more = screen.getByRole("button", { name: "Show 50 more" });
    more.focus();
    fireEvent.click(more);
    expect(screen.getAllByRole("row").slice(1)).toHaveLength(150);
    expect(
      screen.queryByRole("button", { name: /Show .* more/ }),
    ).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("status"));
  });

  it("Tools search reaches items no page has rendered yet", () => {
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
    expect(useDesk.getState().pulloutId).toBe(qualifiedRef("kb", "needle"));
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
