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
