/** New Decision, app-level (the owner, 2026-10-25: "go -> new decision ->
 * opens up a cluster fuck of a window"). The real Desk store, the real
 * window host (SurfaceWindows), the real New decision window and the real
 * Decisions window. Only the transport is a double, and it replays the hub's
 * own recorded answers (tests/integration/test_face_wire_fences.py
 * ::test_new_decision_reads): the from-desk create, the record read and the
 * list read. Nothing typed by hand (the SCAR LAW).
 *
 * The press is driven to the rendered outcome: New Decision opens a window
 * of its own (never the palette); Create writes ONE decision and the record
 * opens in the Decisions window, selected, in its reader; never in Today. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CREATED from "../../../test/wire/decision-records.from-desk.wire.json";
import RECORD from "../../../test/wire/decision-record.new.wire.json";
import LIST from "../../../test/wire/decision-records.list-new.wire.json";
import MEETING_DECISION from "../../../test/wire/decision.honest-faces.wire.json";
import NO_RECORD from "../../../test/wire/decision.no-record.wire.json";
import NO_RECORD_ROW from "../../../test/wire/decisions.no-record.wire.json";
import WORK_TWO from "../../../test/wire/decision-records.work-two.wire.json";
import GOVERNING_A from "../../../test/wire/decision-record.governing-a.wire.json";
import GOVERNING_B from "../../../test/wire/decision-record.governing-b.wire.json";

const hub = vi.hoisted(() => ({
  posts: [] as Array<{ url: string; body: Record<string, unknown> }>,
  puts: [] as string[],
  gets: [] as string[],
}));

vi.mock("../../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const answer = (body: unknown, status = 200) =>
    Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(structuredClone(body)) });
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      const method = (init?.method ?? "GET").toUpperCase();
      if (method === "POST") {
        hub.posts.push({ url, body: JSON.parse(String(init?.body ?? "{}")) });
        if (url === "/api/decision-records/from-desk") return answer(CREATED.wire, 201);
      }
      if (method === "PUT") hub.puts.push(decodeURIComponent(url));
      return answer({});
    }),
    apiFetch: vi.fn((url: string) => {
      hub.gets.push(url);
      if (url === `/api/decision-records/${RECORD.wire.id}`) return Promise.resolve(structuredClone(RECORD.wire));
      if (url.startsWith("/api/decision-records?")) return Promise.resolve(structuredClone(LIST.wire));
      if (url.startsWith("/api/channels/sends")) return Promise.resolve({ sends: [] });
      // A meeting's decision (recorded) and the records made from it / the
      // records that govern one work item: the recorded record, as a list.
      if (url === `/api/decisions/${MEETING_DECISION.wire.decision.id}`) return Promise.resolve(structuredClone(MEETING_DECISION.wire));
      if (url === `/api/decision-records/source/meeting/${MEETING_DECISION.wire.decision.id}`) return Promise.resolve([structuredClone(RECORD.wire)]);
      if (url === "/api/decision-records/work/item/w-1") return Promise.resolve([structuredClone(RECORD.wire)]);
      // A meeting's decision with no record yet (its read, no records made
      // from it, its one ledger row) and the two records that govern w-2
      // (tests/integration/test_face_wire_fences.py::test_decisions_window_scope_reads).
      if (url === `/api/decisions/${NO_RECORD.wire.decision.id}`) return Promise.resolve(structuredClone(NO_RECORD.wire));
      if (url === `/api/decision-records/source/meeting/${NO_RECORD.wire.decision.id}`) return Promise.resolve([]);
      if (url.startsWith("/api/decisions?") && url.includes(`decision_id=${NO_RECORD.wire.decision.id}`)) return Promise.resolve(structuredClone(NO_RECORD_ROW.wire));
      if (url === "/api/decision-records/work/item/w-2") return Promise.resolve(structuredClone(WORK_TWO.wire));
      if (url === `/api/decision-records/${GOVERNING_A.wire.id}`) return Promise.resolve(structuredClone(GOVERNING_A.wire));
      if (url === `/api/decision-records/${GOVERNING_B.wire.id}`) return Promise.resolve(structuredClone(GOVERNING_B.wire));
      return Promise.resolve({});
    }),
  };
});
vi.mock("../../../desk/setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: () => () => undefined }),
}));

import { __resetSurfaces } from "../../../desk/shell";
import { SurfaceWindows } from "../../../desk/components/SurfaceWindows";
import { useDesk } from "../../../desk/store";
import { VERBS } from "../../../desk/verbRegistry";
import { usePalette } from "../../../desk/chromeState";
import { openMember } from "../../../desk/drawer/open";
import { openIntelligence } from "../../../desk/intelligenceNavigation";
import { openRef } from "../../../desk/openObject";
import { WhyControl } from "../../../desk/components/WhyControl";

const PROJECT = { id: "proj-57969b0497a9", name: "Payments ledger cutover" };
const NEW_WINDOW = "surface-new-decision";
const DECISIONS_WINDOW = "surface-decisions";

beforeEach(() => {
  hub.posts = [];
  hub.puts = [];
  hub.gets = [];
  localStorage.clear();
  sessionStorage.clear();
  usePalette.getState().setOpen(false);
  useDesk.setState({
    windowsById: {}, panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [],
    pullouts: [], editingId: null, newIds: [], drafts: {},
    // The desk's Projects read: the window names the Project in front by it.
    projects: [PROJECT] as never,
  });
  __resetSurfaces();
  // The record's time, plus a few seconds: the status bar says "just now".
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(Date.parse(RECORD.wire.created_at) + 5_000) });
});

afterEach(() => {
  vi.useRealTimers();
  __resetSurfaces();
});

const newDecision = () => VERBS.find((verb) => verb.id === "desk.new-decision")!;

async function openNewDecision(overrides: Record<string, unknown> = {}) {
  render(<SurfaceWindows />);
  await act(async () => { await useDesk.getState().createPrimitive("decision", overrides); });
  return screen.findByRole("group", { name: "New decision" });
}

describe("New Decision opens a window of its own", () => {
  it("the verb opens the New decision window, not the palette, and writes nothing", async () => {
    render(<SurfaceWindows />);
    await act(async () => { newDecision().run({ selectedRef: null }); });
    const form = await screen.findByRole("group", { name: "New decision" });
    expect(useDesk.getState().windowsById[NEW_WINDOW]?.applicationKey).toBe("new-decision");
    expect(usePalette.getState().open).toBe(false);
    // The label/control grid: Decision and Why; no About row without a Project.
    expect(within(form).getByRole("textbox", { name: "Decision title" })).toHaveValue("");
    expect(within(form).getByRole("textbox", { name: "Why" })).toHaveValue("");
    expect(within(form).queryByTestId("decision-about-chip")).toBeNull();
    expect(screen.getByRole("button", { name: /Create/ })).toBeDisabled();
    expect(hub.posts).toEqual([]);
  });

  it("Cancel closes the window and writes nothing; Enter with no title writes nothing", async () => {
    const form = await openNewDecision();
    const title = within(form).getByRole("textbox", { name: "Decision title" });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    expect(hub.posts).toEqual([]);
    fireEvent.change(title, { target: { value: "Half a thought" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("group", { name: "New decision" })).toBeNull());
    expect(useDesk.getState().windowsById[NEW_WINDOW]).toBeUndefined();
    expect(hub.posts).toEqual([]);
    // A fresh New Decision starts empty: the abandoned words do not return.
    await act(async () => { await useDesk.getState().createPrimitive("decision", {}); });
    const again = await screen.findByRole("group", { name: "New decision" });
    expect(within(again).getByRole("textbox", { name: "Decision title" })).toHaveValue("");
  });

  it("the unfinished title and Why are kept for a reload", async () => {
    const form = await openNewDecision();
    fireEvent.change(within(form).getByRole("textbox", { name: "Decision title" }), { target: { value: "Keep the ledger" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Why" }), { target: { value: "One writer" } });
    expect(useDesk.getState().drafts).toMatchObject({
      "desk/new-decision/title": "Keep the ledger",
      "desk/new-decision/why": "One writer",
    });
    expect(hub.posts).toEqual([]);
  });

  it("Create writes one decision about the Project and opens it in the Decisions window, selected, in its reader", async () => {
    const form = await openNewDecision({ project_id: PROJECT.id, project_name: PROJECT.name });
    expect(within(form).getByTestId("decision-about-chip").textContent).toBe(PROJECT.name);
    const create = screen.getByRole("button", { name: /Create/ });
    expect(create).toBeDisabled();
    fireEvent.change(within(form).getByRole("textbox", { name: "Decision title" }), { target: { value: "Keep the ledger on SQLite" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Why" }), {
      target: { value: "One writer, one file. Postgres waits until we need a second host." },
    });
    expect(create).not.toBeDisabled();
    await act(async () => { fireEvent.click(create); });

    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].url).toBe("/api/decision-records/from-desk");
    expect(hub.posts[0].body).toMatchObject({
      title: "Keep the ledger on SQLite",
      why: "One writer, one file. Postgres waits until we need a second host.",
      project_id: PROJECT.id,
      project_name: PROJECT.name,
      status: "accepted",
    });
    expect(hub.puts).toEqual([`/api/projects/${PROJECT.id}/resources/decision_record:${RECORD.wire.id}`]);

    // The New decision window is gone; the Decisions window holds the record.
    await waitFor(() => expect(useDesk.getState().windowsById[NEW_WINDOW]).toBeUndefined());
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`);
    // Never Today's window (the owner's catch: a receipts page inside Today).
    expect(useDesk.getState().windowsById["intelligence:desk"]).toBeUndefined();

    const reader = await screen.findByTestId("decision-reader");
    expect(await within(reader).findByRole("heading", { name: "Keep the ledger on SQLite" })).toBeTruthy();
    expect(reader.textContent).toContain("One writer, one file. Postgres waits until we need a second host.");
    expect(within(reader).getByTestId("decision-reader-about").textContent).toBe(PROJECT.name);
    expect(within(reader).getByRole("button", { name: /Send…/ })).toBeTruthy();
    expect(screen.getByTestId("decision-reader-state").textContent).toBe("Decided just now");
    // No mono-capital captions, no state chip, no source button on this path.
    expect(reader.textContent).not.toMatch(/DECISION|CURRENT|Decision context|Open decision/);

    // ‹ Decisions: the list, with the new record selected.
    fireEvent.click(within(reader).getByTestId("decision-reader-back"));
    const row = await screen.findByTestId("decisions-row");
    expect(row.textContent).toContain("Keep the ledger on SQLite");
    expect(row.getAttribute("aria-selected")).toBe("true");
    // The window forgets the record it opened on: a reload shows the list.
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope ?? null).toBeNull();
  });
});

// The owner, 2026-10-25: the reader in the Decisions window is the ONE face
// of a decision record. Every door to a record, and Today's Decisions door,
// opens that window; none opens the old desk decision window or a Decisions
// page inside Today.
describe("every decision door opens the Decisions window", () => {
  const todayOpen = () =>
    Boolean(useDesk.getState().windowsById["intelligence:desk"]) || useDesk.getState().pullouts.some((pullout) => pullout.id === "intelligence:desk");

  it("a drawer's decision record opens in the Decisions window reader, with no source read first", async () => {
    render(<SurfaceWindows />);
    act(() => openMember({ id: `decision_record:${RECORD.wire.id}`, ref: `decision_record:${RECORD.wire.id}`, kind: "decision", name: "X", facts: {} } as never));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`);
    const reader = await screen.findByTestId("decision-reader");
    expect(await within(reader).findByRole("heading", { name: "Keep the ledger on SQLite" })).toBeTruthy();
    expect(within(reader).getByRole("button", { name: /Send…/ })).toBeTruthy();
    expect(within(reader).getByTestId("decision-reader-back")).toBeTruthy();
    expect(screen.getByTestId("decision-reader-state").textContent).toBe("Decided just now");
    // Not the old desk decision window, not Today; no read of the source decision.
    expect(hub.gets.some((url) => url.startsWith("/api/decisions/"))).toBe(false);
    expect(Object.keys(useDesk.getState().windowsById)).toEqual([DECISIONS_WINDOW]);
    expect(todayOpen()).toBe(false);
  });

  it("an open Decisions window comes to the front on the record asked for", async () => {
    render(<SurfaceWindows />);
    act(() => useDesk.getState().openSurfaceWindow("open-decisions"));
    expect(await screen.findByTestId("decisions-window")).toBeTruthy();
    act(() => openMember({ id: `decision_record:${RECORD.wire.id}`, ref: `decision_record:${RECORD.wire.id}`, kind: "decision", name: "X", facts: {} } as never));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`);
    expect(await screen.findByTestId("decision-reader")).toBeTruthy();
    expect(screen.getAllByTestId("decisions-window")).toHaveLength(1);
  });

  it("Today's Decisions door opens the Decisions window list, never a page in Today", async () => {
    const asked: unknown[] = [];
    const listen = (event: Event) => asked.push((event as CustomEvent).detail);
    window.addEventListener("holdspeak:intelligence-navigate", listen);
    try {
      render(<SurfaceWindows />);
      act(() => openIntelligence({ view: "receipts" }));
      expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope ?? null).toBeNull();
      const row = await screen.findByTestId("decisions-row");
      expect(row.textContent).toContain("Keep the ledger on SQLite");
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(asked).toEqual([]);
      expect(todayOpen()).toBe(false);
    } finally {
      window.removeEventListener("holdspeak:intelligence-navigate", listen);
    }
  });

  it("a meeting's decision that has a record opens that record in the reader", async () => {
    render(<SurfaceWindows />);
    act(() => openRef(`decision:${MEETING_DECISION.wire.decision.id}`));
    await waitFor(() => expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`));
    expect(await screen.findByTestId("decision-reader")).toBeTruthy();
    expect(todayOpen()).toBe(false);
  });

  it("WHY with one governing record opens that record in the reader", async () => {
    render(<><SurfaceWindows /><WhyControl workType="item" workRef="w-1" /></>);
    fireEvent.click(await screen.findByRole("button", { name: /governing decision receipt/ }));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`);
    expect(await screen.findByTestId("decision-reader")).toBeTruthy();
    expect(todayOpen()).toBe(false);
  });

  it("a door that names the record (Open canonical record) opens it in the reader", async () => {
    render(<SurfaceWindows />);
    act(() => openIntelligence({ view: "receipts", receiptId: RECORD.wire.id }));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`record:${RECORD.wire.id}`);
    expect(await screen.findByTestId("decision-reader")).toBeTruthy();
    expect(todayOpen()).toBe(false);
  });

  it("a meeting's decision with no record yet opens in the Decisions window reader, from its meeting", async () => {
    const id = NO_RECORD.wire.decision.id;
    render(<SurfaceWindows />);
    act(() => openRef(`decision:${id}`));
    await waitFor(() => expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`decision:${id}`));
    const reader = await screen.findByTestId("decision-reader");
    expect(reader.getAttribute("data-from")).toBe("meeting");
    expect(await within(reader).findByRole("heading", { name: "Freeze the old ledger on Nov 5" })).toBeTruthy();
    expect(reader.textContent).toContain("Dual-write is stable.");
    expect(reader.textContent).toContain("Ledger cutover sync");
    expect(within(reader).getByTestId("decision-reader-meeting").textContent).toContain("Open meeting");
    expect(screen.getByTestId("decision-reader-state").textContent).toMatch(/^Decided/);
    expect(screen.getByTestId("decision-reader-status").textContent).toContain("From a meeting");
    // No Send (no record to send yet), no mono-capital captions.
    expect(within(reader).queryByTestId("decision-reader-send")).toBeNull();
    expect(reader.textContent).not.toMatch(/DECISION|Decision context|Results/);
    expect(todayOpen()).toBe(false);
    // ‹ Decisions: the list; the window forgets the decision it opened on.
    fireEvent.click(within(reader).getByTestId("decision-reader-back"));
    expect(await screen.findByTestId("decisions-row")).toBeTruthy();
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope ?? null).toBeNull();
  });

  it("WHY with several governing records lists only those, the first in the reader", async () => {
    const [first, second] = WORK_TWO.wire;
    render(<><SurfaceWindows /><WhyControl workType="item" workRef="w-2" /></>);
    fireEvent.click(await screen.findByRole("button", { name: /governing decision receipts/ }));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe(`records:${first.id},${second.id}`);
    const reader = await screen.findByTestId("decision-reader");
    expect(await within(reader).findByRole("heading", { name: first.decision_text })).toBeTruthy();
    expect(todayOpen()).toBe(false);
    // ‹ Decisions: only the two governing records, the one read selected.
    fireEvent.click(within(reader).getByTestId("decision-reader-back"));
    await waitFor(() => expect(screen.getAllByTestId("decisions-row")).toHaveLength(2));
    const rows = screen.getAllByTestId("decisions-row");
    expect(rows.map((row) => row.textContent).join(" ")).toContain(second.decision_text);
    expect(rows.find((row) => row.textContent?.includes(first.decision_text))?.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByTestId("decisions-status").textContent).toContain("2 decisions");
    // All decisions: the whole list again.
    fireEvent.click(screen.getByTestId("decisions-all"));
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope ?? null).toBeNull();
    await waitFor(() => expect(screen.queryByTestId("decisions-all")).toBeNull());
  });

  it("Review decisions opens the Decisions window with Current only on", async () => {
    render(<SurfaceWindows />);
    const review = VERBS.find((verb) => verb.id === "desk.intelligence-review-decisions")!;
    await act(async () => { review.run({ selectedRef: null }); });
    expect(useDesk.getState().windowsById[DECISIONS_WINDOW]?.scope).toBe("current");
    await screen.findByTestId("decisions-window");
    expect(screen.getByRole("checkbox", { name: "Current only" })).toBeChecked();
    expect(await screen.findByTestId("decisions-row")).toBeTruthy();
    expect(todayOpen()).toBe(false);
  });
});

