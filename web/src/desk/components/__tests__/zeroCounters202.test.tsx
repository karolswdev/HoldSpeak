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
import { AskPanel } from "../AskPanel";

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

// PHILO-17: the zone rows (DeskListView) and the spatial Floor (WorldStage)
// are parked with the Floor (desk/_parked/floor/); no face draws a zone.

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
