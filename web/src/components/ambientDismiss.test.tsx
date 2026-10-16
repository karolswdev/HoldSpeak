import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DeskProjection } from "../desk/projections";
import recorded from "../test/wire/desk-projections.remote-receipt.wire.json";

const runtime = vi.hoisted(() => ({
  listeners: new Set<(frame: { type: string; data: unknown }) => void>(),
  subscribe: (topic: string, listener: (frame: { type: string; data: unknown }) => void) => {
    if (topic === "*") runtime.listeners.add(listener);
    return () => { runtime.listeners.delete(listener); };
  },
}));
vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: runtime.subscribe }),
  useRuntimeFrame: () => null,
}));

const NOW = Date.parse("2026-10-15T18:00:00Z");
const KEY = "holdspeak.ambient.attention.dismissed-through";
// Replay the recorded wire shape with scenario-specific attention fields.
function attention(id: string, patch: Partial<DeskProjection> = {}): DeskProjection {
  return {
    ...recorded.wire.projections[0],
    id,
    projection_kind: "attention",
    attention_state: "needs_attention",
    title: "Meeting capture needs recovery",
    summary: "",
    source_kind: "meeting",
    detail_url: "/",
    timestamp: "2026-10-15T17:00:00Z",
    ...patch,
  } as DeskProjection;
}
function response(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body } as Response;
}
function envelope(rows: DeskProjection[]) {
  return {
    ...recorded.wire,
    projections: rows,
    counts: { needs_attention: rows.length },
    page: { offset: 0, limit: 4, total: rows.length, has_more: false },
  };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

let store: typeof import("../desk/projections").useProjections;
let AmbientLayer: typeof import("./AmbientLayer").AmbientLayer;
let rows: DeskProjection[];
let ambientRead: () => Promise<Response>;
let drawerRead: () => Promise<Response>;
let writer: ReturnType<typeof vi.fn<(id: string) => Promise<Response>>>;
let fetcher: ReturnType<typeof vi.fn>;
let writes: string[];

beforeEach(async () => {
  vi.resetModules();
  sessionStorage.clear();
  vi.spyOn(Date, "now").mockReturnValue(NOW);
  runtime.listeners.clear();
  rows = [];
  writes = [];
  ambientRead = async () => response(envelope(rows.filter((row) => !row.dismissed)));
  drawerRead = ambientRead;
  writer = vi.fn(async () => response({ success: true }));
  fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url === "/api/settings") return response({ presence: { enabled: true, mascot: true } });
    if (init?.method === "PUT") {
      const id = decodeURIComponent(url.split("/").at(-2)!);
      expect(JSON.parse(String(init.body))).toEqual({ action: "dismiss" });
      writes.push(id);
      const result = await writer(id);
      if (result.ok) rows = rows.map((row) => row.id === id ? { ...row, dismissed: true } : row);
      return result;
    }
    if (url.includes("attention_state=")) return ambientRead();
    if (url.startsWith("/api/desk/projections?")) return drawerRead();
    throw new Error(`Unexpected request: ${url}`);
  });
  vi.stubGlobal("fetch", fetcher);
  store = (await import("../desk/projections")).useProjections;
  AmbientLayer = (await import("./AmbientLayer")).AmbientLayer;
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function settled() {
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => url.includes("attention_state="))).toBe(true));
}

describe("Qlippy attention presentation", () => {
  it("keeps dictation journal warnings in Attention without a popup or write", async () => {
    rows = [attention("dictation:1", { source_kind: "dictation_journal" })];
    render(<AmbientLayer />);
    await settled();
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    expect(store.getState().ambient.map((row) => row.id)).toEqual(["dictation:1"]);
    expect(writes).toEqual([]);
  });

  it("selects a valid recovery after dictation and already dismissed rows", async () => {
    rows = [
      attention("dictation:1", { source_kind: "dictation_journal", title: "Dictation needs review" }),
      attention("dismissed", { dismissed: true, title: "Dismissed recovery" }),
      attention("recovery"),
    ];
    // A stale ambient read can still contain a dismissed row.
    ambientRead = async () => response(envelope(rows));
    render(<AmbientLayer />);
    expect(await screen.findByText("Meeting capture needs recovery")).toBeTruthy();
    expect(screen.queryByText("Dictation needs review")).toBeNull();
    expect(screen.queryByText("Dismissed recovery")).toBeNull();
    expect(screen.queryByRole("button", { name: "Review source" })).toBeNull();
  });

  it("dismisses only the visible identical row and suppresses old backlog after refresh, remount and reload", async () => {
    rows = [attention("first"), attention("old-2"), attention("old-3")];
    let mounted = render(<AmbientLayer />);
    fireEvent.click(await screen.findByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByLabelText("Qlippy")).toBeNull());
    expect(writes).toEqual(["first"]);
    expect(rows.filter((row) => row.dismissed).map((row) => row.id)).toEqual(["first"]);
    expect(store.getState().projections.map((row) => row.id)).toEqual(["old-2", "old-3"]);
    await act(async () => { await store.getState().refreshAmbient(); });
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    mounted.unmount();
    mounted = render(<AmbientLayer />);
    await settled();
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    mounted.unmount();
    // A fresh module has no memory fallback: only this tab's saved cutoff survives.
    vi.resetModules();
    store = (await import("../desk/projections")).useProjections;
    AmbientLayer = (await import("./AmbientLayer")).AmbientLayer;
    render(<AmbientLayer />);
    await waitFor(() => expect(store.getState().ambient).toHaveLength(2));
    expect(sessionStorage.getItem(KEY)).toBe(String(NOW));
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    rows.unshift(attention("new", { timestamp: "2026-10-15T18:00:01Z", title: "New recovery" }));
    await act(async () => { await store.getState().refreshAmbient(); });
    expect(await screen.findByText("New recovery")).toBeTruthy();
    expect(writes).toEqual(["first"]);
  });

  it("keeps the clicked row pending while the writer's ambient refresh selects another row", async () => {
    rows = [attention("first", { title: "First recovery" }), attention("second", { title: "Second recovery" })];
    const refresh = deferred<Response>();
    render(<AmbientLayer />);
    await screen.findByText("First recovery");
    drawerRead = () => refresh.promise;
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(store.getState().ambient[0].id).toBe("second"));
    expect(screen.getByText("First recovery")).toBeTruthy();
    expect(screen.queryByText("Second recovery")).toBeNull();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    await act(async () => { refresh.resolve(response(envelope(rows.filter((row) => !row.dismissed)))); });
    await waitFor(() => expect(screen.queryByLabelText("Qlippy")).toBeNull());
    expect(writes).toEqual(["first"]);
  });

  it("keeps a failed write visible and retries its exact ID after a refresh", async () => {
    rows = [attention("first", { title: "First recovery" }), attention("second", { title: "Second recovery" })];
    writer.mockResolvedValueOnce(response({ error: "Writer refused" }, 409));
    render(<AmbientLayer />);
    fireEvent.click(await screen.findByRole("button", { name: "Dismiss" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Cannot dismiss");
    ambientRead = async () => response(envelope([rows[1]]));
    await act(async () => { await store.getState().refreshAmbient(); });
    expect(screen.getByText("First recovery")).toBeTruthy();
    expect(screen.queryByText("Second recovery")).toBeNull();
    expect(sessionStorage.getItem(KEY)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByLabelText("Qlippy")).toBeNull());
    expect(writes).toEqual(["first", "first"]);
    expect(rows[1].dismissed).toBe(false);
  });

  it("uses memory when session storage is refused, including after remount", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("denied"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("denied"); });
    rows = [attention("first"), attention("second")];
    const mounted = render(<AmbientLayer />);
    fireEvent.click(await screen.findByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByLabelText("Qlippy")).toBeNull());
    mounted.unmount();
    render(<AmbientLayer />);
    await settled();
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    expect(writes).toEqual(["first"]);
  });

  it("preserves runtime learning cards when old attention is suppressed", async () => {
    sessionStorage.setItem(KEY, String(NOW));
    rows = [attention("old")];
    render(<AmbientLayer />);
    await settled();
    act(() => {
      for (const listener of runtime.listeners) listener({ type: "learning_event", data: { id: "learned", title: "Learned shortcut" } });
    });
    expect(await screen.findByText("Learned shortcut")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    expect(writes).toEqual([]);
  });
});
