/* HS-202-04 — no counter of zero, in text OR in an accessible name.
 *
 * Doctrine (UX-CANON A.8: "`0 Watches`, `REV 1`, `0 today` are bounces;
 * omit the zero token or say the true thing"):
 *
 *  - `countToken` (`desk/surface/count.ts`) is the ONE way a face says
 *    "N things" and it already returns null at zero. The survivors are the
 *    sites that never used it.
 *  - `SURFACE-INVENTORY-2026-09-20.md:58` counted 11 rendered zero
 *    counters, and §4 named the one the rig could not see at all:
 *    "An empty zone announces '…zone, 0 items' (`DeskListView.tsx:214`)"
 *    — a counter of zero inside an accessible name, where only a screen
 *    reader meets it. Its visible twin is the same row's Items cell
 *    (`DeskListView.tsx:243`).
 *  - The walk's `app-ask` legs recorded `SESSION · 0 TURNS`
 *    (`01-measured-walk.md:150`) on the Ask AI face
 *    (`desk/components/AskPanel.tsx:292`) at every desk and both widths.
 */
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../../../lib/primitives";
import { EMPTY_ITEMS, type Items } from "../../api";
import { useDesk } from "../../store";
import { usePalette } from "../../chromeState";
import { useProjections } from "../../projections";
import { DeskListView } from "../DeskListView";
import { AskPanel } from "../AskPanel";
import { WorldStage } from "../../gl/WorldStage";

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

/** One zone with no members, and one note outside it. */
const items: Items = {
  ...EMPTY_ITEMS,
  note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
  directory: [
    {
      kind: "directory",
      id: "z1",
      name: "Launch",
      memberIds: [],
    } as never,
  ],
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
    askOpen: true,
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
  });
  useProjections.setState({ subject_counts: {} });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) })),
  );
});

describe("an empty zone never counts to a screen reader (A.8)", () => {
  it("does not announce '0 items' in the row's accessible name", () => {
    render(
      <MemoryRouter>
        <DeskListView />
      </MemoryRouter>,
    );
    const names = [...document.querySelectorAll("[aria-label]")].map(
      (element) => element.getAttribute("aria-label") ?? "",
    );
    expect(names).toContain("Launch zone");
    expect(names.filter((name) => /\b0 items?\b/.test(name))).toEqual([]);
  });

  /* The shot walk caught this one: `countToken`'s default plural appends
   * an S to the token as given, so a lowercase noun announced "2 itemS".
   * A screen reader reads the case. */
  it("announces a filled zone in plain lowercase words", () => {
    useDesk.setState({
      items: {
        ...items,
        directory: [
          { kind: "directory", id: "z1", name: "Launch",
            memberIds: ["note:n1"] } as never,
        ],
      },
    });
    render(
      <MemoryRouter>
        <DeskListView />
      </MemoryRouter>,
    );
    const names = [...document.querySelectorAll("[aria-label]")].map(
      (element) => element.getAttribute("aria-label") ?? "",
    );
    expect(names).toContain("Launch zone, 1 item");
    expect(names.some((name) => /itemS/.test(name))).toBe(false);
  });

  it("does not print 0 ITEMS in the zone row's own cell", () => {
    render(
      <MemoryRouter>
        <DeskListView />
      </MemoryRouter>,
    );
    const cells = [...document.querySelectorAll("td")].map(
      (cell) => cell.textContent ?? "",
    );
    expect(cells.some((cell) => cell.includes("Launch"))).toBe(true);
    expect(cells.filter((cell) => /^0 ITEMS?$/.test(cell.trim()))).toEqual([]);
  });
});

/* The shot walk found the SECOND site the inventory's §4 actually named:
 * the spatial Floor's own accessibility layer (`desk/gl/WorldStage.tsx`).
 * At 393 the list face never opened, and the names the 393 leg read came
 * from there, still saying "0 items". */
describe("the spatial Floor announces no zero either (A.8)", () => {
  it("names an empty zone without a count", () => {
    const { container } = render(<WorldStage />);
    const names = [...container.querySelectorAll("[data-zone-id]")].map(
      (element) => element.getAttribute("aria-label") ?? "",
    );
    expect(names).toContain("Launch zone");
    expect(names.filter((name) => /\b0 items?\b/.test(name))).toEqual([]);
  });

  it("counts a filled zone in plain lowercase words", () => {
    useDesk.setState({
      items: {
        ...items,
        directory: [
          { kind: "directory", id: "z1", name: "Launch",
            memberIds: ["note:n1"] } as never,
        ],
      },
    });
    const { container } = render(<WorldStage />);
    const names = [...container.querySelectorAll("[data-zone-id]")].map(
      (element) => element.getAttribute("aria-label") ?? "",
    );
    expect(names).toContain("Launch zone, 1 item");
  });
});

describe("Ask AI opens without counting its turns to zero (A.8)", () => {
  it("heads a fresh session with SESSION, not SESSION · 0 TURNS", () => {
    render(<AskPanel />);
    const head = document.querySelector(
      ".desk-ask-body .surface-well-head",
    )?.textContent;
    expect(head, "the Ask session well draws its head").toBeTruthy();
    expect(head).toBe("SESSION");
  });
});
