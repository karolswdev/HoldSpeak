/** Inventory gap 9 (Astra on #774) — an object older than its desk list is
 * read by its id once it is held, for every kind a MEMORY row opens.
 * The real `loadAll`; the hub transport is the double. */
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

import { __resetHeldObjects, holdObject, loadAll } from "../api";

let calls: string[] = [];

beforeEach(() => {
  __resetHeldObjects();
  calls = [];
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string) => {
    calls.push(path);
    const artifacts = (n: number) => Array.from({ length: n }, (_, i) => ({
      meta: { id: `art-${i}`, kind: "artifact", deleted: false },
      value: { id: `art-${i}`, title: `Artifact ${i}`, artifact_type: "notes", body_markdown: "" },
    }));
    if (path === "/api/meetings?limit=24") return Promise.resolve({ meetings: [{ id: "m-new", title: "New" }] });
    if (path === "/api/sync/pull?limit=50") return Promise.resolve({ artifacts: artifacts(30) });
    if (path === "/api/sync/pull?limit=500") return Promise.resolve({ artifacts: [...artifacts(30), {
      meta: { id: "art-far", kind: "artifact", deleted: false },
      value: { id: "art-far", title: "Far artifact", artifact_type: "notes", body_markdown: "" } }] });
    if (path === "/api/notes") return Promise.resolve({ notes: [] });
    if (path === "/api/decisions") return Promise.resolve({ decisions: [] });
    if (path === "/api/threads") return Promise.resolve({ threads: [] });
    if (path === "/api/meetings/m-old") return Promise.resolve({ id: "m-old", title: "Old meeting" });
    if (path === "/api/notes/n-old") return Promise.resolve({ note: { id: "n-old", title: "Old note", body_markdown: "x" } });
    if (path === "/api/decisions/d-old") return Promise.resolve({ decision: { id: "d-old", title: "Old decision" } });
    if (path === "/api/threads/t-old") return Promise.resolve({ id: "t-old", title: "Old thread" });
    if (path === "/api/meetings/m-gone") return Promise.reject(new Error("404"));
    return Promise.resolve({});
  });
});

const ids = (rows: Array<{ id: string }>) => rows.map((r) => r.id);

describe("held objects", () => {
  it("with nothing held, the lists stand as read: 24 artifacts, no read by id", async () => {
    const { items } = await loadAll();
    expect(items.artifact).toHaveLength(24);
    expect(calls.some((c) => /\/api\/(meetings|notes|decisions|threads)\/./.test(c))).toBe(false);
    expect(calls).not.toContain("/api/sync/pull?limit=500");
  });

  it("each held kind is read by its id and stays in its bucket", async () => {
    for (const ref of ["meeting:m-old", "artifact:art-27", "note:n-old", "decision:d-old", "thread:t-old#msg-4"])
      expect(holdObject(ref)).toBe(true);
    const { items } = await loadAll();
    expect(ids(items.meeting)).toEqual(["m-new", "m-old"]);
    expect(ids(items.artifact)).toHaveLength(25);
    expect(ids(items.artifact)).toContain("art-27");   // from the pull the desk already read
    expect(calls).not.toContain("/api/sync/pull?limit=500");
    expect(ids(items.note)).toEqual(["n-old"]);
    expect(ids(items.decision)).toEqual(["d-old"]);
    expect(ids(items.thread)).toEqual(["t-old"]);
    // The next load keeps them (a window whose object leaves the store is dropped).
    const again = await loadAll();
    expect(ids(again.items.meeting)).toContain("m-old");
    expect(ids(again.items.artifact)).toContain("art-27");
  });

  it("an artifact beyond the first pull takes one wider pull", async () => {
    holdObject("artifact:art-far");
    const { items } = await loadAll();
    expect(ids(items.artifact)).toContain("art-far");
    expect(calls.filter((c) => c === "/api/sync/pull?limit=500")).toHaveLength(1);
  });

  it("an object already in its list is not read again; a gone object is left out; other kinds are not held", async () => {
    holdObject("meeting:m-new");
    holdObject("meeting:m-gone");
    expect(holdObject("cadence:c-1")).toBe(false);
    expect(holdObject("meeting:")).toBe(false);
    const { items, error } = await loadAll();
    expect(ids(items.meeting)).toEqual(["m-new"]);
    expect(calls).not.toContain("/api/meetings/m-new");
    expect(error).toBe("");
  });
});
