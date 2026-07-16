// HS-93-08 — the spatial stage's honest render bound: a 1,000-item desk
// floats a capped set with a visible count chip (never silent truncation),
// while the store keeps every record so search and the list mode reach
// everything.
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { EMPTY_ITEMS, type Items } from "../api";
import { useDesk } from "../store";
import { allObjects } from "../world";
import { World, MAX_FLOATERS } from "../components/World";

const thousand: Items = {
  ...EMPTY_ITEMS,
  note: Array.from({ length: 600 }, (_, i) => ({
    kind: "note" as const,
    id: `n${i}`,
    title: `Note ${i}`,
  })),
  kb: Array.from({ length: 200 }, (_, i) => ({
    kind: "kb" as const,
    id: `k${i}`,
    name: `Knowledge ${i}`,
  })),
  recipe: Array.from({ length: 200 }, (_, i) => ({
    kind: "recipe" as const,
    id: `r${i}`,
    name: `Persona ${i}`,
  })),
  workflow: [
    { kind: "workflow" as const, id: "w-needle", name: "Meridian sweep" },
  ],
};

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    items: thousand,
    divedZone: null,
    positions: {},
    selectedIds: [],
    pulloutId: null,
    editingId: null,
    askOpen: false,
  });
});

describe("HS-93-08 spatial bound at 1,000 items", () => {
  it("caps floaters at MAX_FLOATERS and says so in a status chip", () => {
    const { container } = render(<World />);
    expect(container.querySelectorAll(".desk-obj")).toHaveLength(MAX_FLOATERS);
    expect(screen.getByRole("status")).toHaveTextContent(
      `Showing ${MAX_FLOATERS} of 1001`,
    );
    expect(screen.getByRole("status")).toHaveTextContent("List");
  });

  it("keeps every record findable regardless of what floats", () => {
    const all = allObjects(useDesk.getState().items);
    expect(all).toHaveLength(1001);
    // The needle workflow is far past the render bound in world order,
    // yet the search surface (allObjects, not rendered nodes) has it.
    const needle = all.filter((o) =>
      `${o.title}`.toLowerCase().includes("meridian"),
    );
    expect(needle.map((o) => o.id)).toEqual(["w-needle"]);
  });

  it("renders no chip when the desk fits", () => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "solo", title: "Solo" }],
      },
    });
    const { container } = render(<World />);
    expect(container.querySelector(".desk-scale-chip")).toBeNull();
    expect(container.querySelectorAll(".desk-obj")).toHaveLength(1);
  });
});

describe("HS-93-08 view mode persistence", () => {
  it("setViewMode writes hs.desk.view and mirrors ?view=list", () => {
    useDesk.getState().setViewMode("list");
    expect(useDesk.getState().viewMode).toBe("list");
    expect(localStorage.getItem("hs.desk.view")).toBe("list");
    expect(window.location.search).toContain("view=list");
    useDesk.getState().setViewMode("spatial");
    expect(localStorage.getItem("hs.desk.view")).toBe("spatial");
    expect(window.location.search).not.toContain("view=list");
  });
});
