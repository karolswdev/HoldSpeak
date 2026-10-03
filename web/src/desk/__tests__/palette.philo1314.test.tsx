/** PHILO-13-14 (C4) — a palette that knows his week and does verbs.
 *
 * - `Priya` opens her window (People, on her relationship); `Prep 1:1 with
 *   Priya Shah` opens her on Prep (the registry's week verbs).
 * - a word inside a thought finds it (the note body is a word-scored term:
 *   a word, never a scattered-letter match over a long body).
 * - `send` leads with `Send <front document> to <destination>`; the pick goes
 *   through C5's push seam (the well is picked) and posts no send.
 * - `Draft update for <project>` opens the Room in its Update posture.
 * - `People` puts the People app above the `People & vocabulary` note; one
 *   Escape closes the shelf, also with a query typed.
 * Real store, real palette, real C5 seam; the hub transport is the double. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const opened = vi.hoisted(() => ({ surfaces: [] as Array<[string, string | undefined]> }));
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return {
    ...actual,
    openSurface: (key: string, scope?: string) => { opened.surfaces.push([key, scope]); return true; },
    openSurfaceOr: (key: string, _href: string, scope?: string) => { opened.surfaces.push([key, scope]); },
    openProjectRoom: (id: string) => { opened.surfaces.push(["open-project-memory", `project:${id}`]); },
  };
});

import { EMPTY_ITEMS } from "../api";
import type { Note } from "../../lib/primitives";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { DeskToolShelf, rankRow } from "../components/DeskToolShelf";
import { announceWindow, retractWindow } from "../components/window/windowRegistry";
import { resetSendTo } from "../windowSend";
import { pickedDestination, resetSendStore } from "../surface/send";
import { takeRoomUpdatesRequest } from "../openObject";

const calls: Array<[string, string]> = [];

beforeEach(() => {
  localStorage.clear();
  opened.surfaces = [];
  calls.length = 0;
  resetSendTo();
  resetSendStore();
  usePalette.setState({ open: false });
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string, init: RequestInit = {}) => {
    calls.push([init.method ?? "GET", path]);
    const p = path.split("?")[0];
    if (p === "/api/people/relationships")
      return Promise.resolve({ relationships: [
        { id: "rel-priya", display_name: "Priya Shah", relationship_kind: "direct_report", owner_aliases: ["Priya"], state: "active" },
        { id: "rel-omar", display_name: "Omar Haddad", relationship_kind: "peer", owner_aliases: [], state: "active" },
      ] });
    if (p === "/api/channels/destinations")
      return Promise.resolve({ destinations: [
        { id: "chd_f", name: "Team updates", channel: "file", account: {}, target: { folder: "/x" }, synced: false,
          state: "active", created_at: "2026-10-02T08:00:00Z", parked_at: null },
      ] });
    return Promise.resolve({});
  });
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [
        { kind: "note", id: "n-vocab", title: "People & vocabulary", bodyMarkdown: "Names.", tags: [], createdAt: "" } as Note,
        { kind: "note", id: "n-th1", title: "Thought", bodyMarkdown: "Ask about the rollback runbook and the Kafka offsets.", tags: [], createdAt: "" } as Note,
        { kind: "note", id: "n-th2", title: "Thought", bodyMarkdown: "Lunch on Friday.", tags: [], createdAt: "" } as Note,
      ],
    },
    projects: [{ id: "p-ledger", name: "Payments ledger cutover" }] as never,
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    panelOrder: [],
    panelMin: [],
    openPullout: vi.fn(),
    openToolInspector: vi.fn(),
    diveInto: vi.fn(),
    focusPanel: vi.fn(),
  });
});

async function deck() {
  render(<MemoryRouter><DeskToolShelf /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
  return screen.getByRole("combobox", { name: "Search tools and Desk items" });
}

async function type(input: HTMLElement, q: string) {
  fireEvent.change(input, { target: { value: q } });
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
}

const options = () => screen.queryAllByRole("option").map((o) => o.textContent ?? "");
const top = () => screen.getAllByRole("option").find((o) => o.className.includes("is-selected"))?.textContent ?? "";

describe("PHILO-13-14 the palette knows his week", () => {
  it("`Priya` opens her window (her relationship in People)", async () => {
    const input = await deck();
    await type(input, "Priya");
    expect(top()).toContain("Priya Shah");
    expect(top()).toContain("PERSON");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(opened.surfaces).toContainEqual(["open-people", "people:rel-priya"]);
    expect(calls).toContainEqual(["GET", "/api/people/relationships"]);
  });

  it("`Prep 1:1 with <person>` for each relationship; Priya's opens her on Prep", async () => {
    const input = await deck();
    await type(input, "prep");
    expect(options().some((o) => o.includes("Prep 1:1 with Priya Shah"))).toBe(true);
    expect(options().some((o) => o.includes("Prep 1:1 with Omar Haddad"))).toBe(true);
    fireEvent.click(screen.getByRole("option", { name: /Prep 1:1 with Priya Shah/ }));
    expect(opened.surfaces).toContainEqual(["open-people", "people:rel-priya:prep"]);
  });

  it("a word inside a thought finds that thought, and Enter opens it", async () => {
    const input = await deck();
    await type(input, "kafka");
    expect(top()).toContain("Thought");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n-th1");
  });

  it("a body matches by word only: scattered letters over a long body find nothing", () => {
    expect(rankRow({ label: "Thought", body: "Ask about the rollback runbook" }, "rollb", false)).toBeGreaterThan(0);
    expect(rankRow({ label: "Thought", body: "Ask about the rollback runbook" }, "atrb", false)).toBe(0);
    expect(rankRow({ label: "Thought", body: "Ask about the rollback runbook" }, "llback", false)).toBe(0);
  });

  it("`send` leads with `Send <front document> to <destination>`; the pick opens the well, nothing is sent", async () => {
    announceWindow("pullout:decision:d-freeze", "Freeze the old ledger", "○", () => {});
    useDesk.setState({ panelOrder: ["pullout:decision:d-freeze"] });
    try {
      const input = await deck();
      await type(input, "send");
      expect(top()).toContain("Send Freeze the old ledger to Team updates");
      fireEvent.keyDown(input, { key: "Enter" });
      expect(useDesk.getState().focusPanel).toHaveBeenCalledWith("pullout:decision:d-freeze");
      await vi.waitFor(() => expect(pickedDestination("desk_decision:d-freeze")).toBe("chd_f"));
      expect(calls.filter(([m, p]) => m === "POST" && p.startsWith("/api/channels/send"))).toEqual([]);
    } finally {
      retractWindow("pullout:decision:d-freeze");
    }
  });

  it("no document window in front: no Send row (a verb that does nothing is withheld)", async () => {
    const input = await deck();
    await type(input, "send");
    expect(options().some((o) => o.startsWith("▸Send "))).toBe(false);
  });

  it("`Draft update for <project>` opens the Room in its Update posture", async () => {
    const input = await deck();
    await type(input, "draft update");
    fireEvent.click(screen.getByRole("option", { name: /Draft update for Payments ledger cutover/ }));
    expect(opened.surfaces).toContainEqual(["open-project-memory", "project:p-ledger"]);
    expect(takeRoomUpdatesRequest("p-ledger")).toBe(true);
    expect(takeRoomUpdatesRequest("p-ledger")).toBe(false);
  });

  it("`People` puts the People app first, above the `People & vocabulary` note", async () => {
    const input = await deck();
    await type(input, "People");
    expect(top()).toContain("Open People");
    const rows = options();
    expect(rows.findIndex((o) => o.includes("Open People"))).toBeLessThan(rows.findIndex((o) => o.includes("People & vocabulary")));
    fireEvent.keyDown(input, { key: "Enter" });
    expect(opened.surfaces).toContainEqual(["open-people", undefined]);
  });

  it("one Escape closes the shelf, also with a query typed", async () => {
    const input = await deck();
    await type(input, "People");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(usePalette.getState().open).toBe(false);
  });
});
