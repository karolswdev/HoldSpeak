/** Inventory gap 9 (Astra on #774) — an object older than its desk list is
 * read by its id once it is held, for every kind a MEMORY row opens.
 * The real `loadAll`; the hub transport is the double. */
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

import { __resetHeldObjects, heldArtifactSource, holdObject, loadAll } from "../api";
import { objectWindowStandIn } from "../objectWindows";
import { ApiError } from "../../lib/api";

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
    if (path.startsWith("/api/artifacts/")) {
      const id = decodeURIComponent(path.slice("/api/artifacts/".length));
      if (id === "art-missing") return Promise.reject(new ApiError(404, "Unknown artifact: art-missing", {}));
      if (id === "art-failed") return Promise.reject(new TypeError("Failed to fetch"));
      if (id === "art-invalid") return Promise.resolve({ artifact: {} });
      return Promise.resolve({ artifact: {
        id, title: "Cited artifact", artifact_type: "run_output", body_markdown: "ARTIFACT10-15",
        status: id === "art-rejected" ? "rejected" : "pending-review", origin: "run",
        sources: [{ source_type: "workbench", source_ref: "wb-source" }],
      } });
    }
    if (path === "/api/notes") return Promise.resolve({ notes: [] });
    if (path === "/api/decisions") return Promise.resolve({ decisions: [] });
    if (path === "/api/threads") return Promise.resolve({ threads: [] });
    if (path === "/api/meetings/m-old") return Promise.resolve({ id: "m-old", title: "Old meeting" });
    if (path === "/api/notes/n-old") return Promise.resolve({ note: { id: "n-old", title: "Old note", body_markdown: "x" } });
    if (path === "/api/decisions/d-old") return Promise.resolve({ decision: { id: "d-old", title: "Old decision" } });
    if (path === "/api/decisions/mdec-1")
      return Promise.resolve({ decision: { id: "mdec-1", text: "Freeze the old ledger", source_meeting_id: "m-old" }, lineage: {} });
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
    expect(calls.some((c) => /\/api\/(meetings|artifacts|notes|decisions|threads)\/./.test(c))).toBe(false);
    expect(calls).not.toContain("/api/sync/pull?limit=500");
  });

  it("independent held reads continue after a failure, while a later refusal retains only real material", async () => {
    holdObject("artifact:art-missing");
    holdObject("artifact:art-far");
    const first = await loadAll();
    expect(ids(first.items.artifact)).toContain("art-far");
    expect(ids(first.items.artifact)).not.toContain("art-missing");
    expect(first.status.artifact).toBe("live");
    expect(first.transientFailures?.artifact).toBeUndefined();
    const normalRead = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation((path: string) => path === "/api/artifacts/art-far"
      ? Promise.reject(new ApiError(404, "Source removed", {})) : normalRead(path));
    const later = await loadAll();
    expect(ids(later.items.artifact)).not.toContain("art-far");
    expect(heldArtifactSource("art-far")).toMatchObject({
      id: "art-far", bodyMarkdown: "ARTIFACT10-15", status: "pending-review",
      sourceRead: { state: "unavailable", hasMaterial: true, message: "Source removed" },
    });
    expect(heldArtifactSource("art-missing")?.sourceRead?.hasMaterial).toBe(false);
  });

  it("each held kind is read by its id and stays in its bucket", async () => {
    for (const ref of ["meeting:m-old", "artifact:art-27", "note:n-old", "decision:d-old", "thread:t-old#msg-4"])
      expect(holdObject(ref)).toBe(true);
    const { items } = await loadAll();
    expect(ids(items.meeting)).toEqual(["m-new", "m-old"]);
    expect(ids(items.artifact)).toHaveLength(25);
    expect(ids(items.artifact)).toContain("art-27");
    expect(calls).toContain("/api/artifacts/art-27");
    expect(calls).not.toContain("/api/sync/pull?limit=500");
    expect(ids(items.note)).toEqual(["n-old"]);
    expect(ids(items.decision)).toEqual(["d-old"]);
    expect(ids(items.thread)).toEqual(["t-old"]);
    // The next load keeps them (a window whose object leaves the store is dropped).
    const again = await loadAll();
    expect(ids(again.items.meeting)).toContain("m-old");
    expect(ids(again.items.artifact)).toContain("art-27");
  });

  it("a failed exact read remains visible when the same ID is still in the public bucket", async () => {
    holdObject("artifact:art-0");
    await loadAll();
    const normalRead = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation((path: string) => path === "/api/artifacts/art-0"
      ? Promise.reject(new TypeError("Connection refused")) : normalRead(path));
    const later = await loadAll();
    expect(ids(later.items.artifact)).toContain("art-0");
    expect(objectWindowStandIn("artifact:art-0")?.ref).toMatchObject({
      id: "art-0", bodyMarkdown: "ARTIFACT10-15",
      sourceRead: { state: "failed", hasMaterial: true, message: "Connection refused" },
    });
    expect(later.status.artifact).toBe("live");
  });

  // PHILO-17: a decision a meeting recorded is not a Desk object; held, it
  // never becomes an untitled "New decision" on the Floor.
  it("a held decision a meeting recorded is left out of the Desk's decisions", async () => {
    holdObject("decision:mdec-1");
    const { items } = await loadAll();
    expect(calls).toContain("/api/decisions/mdec-1");
    expect(ids(items.decision)).toEqual([]);
  });

  it("cited pending and rejected outputs use exact reads and survive later bounded refreshes", async () => {
    holdObject("artifact:art-far#source");
    holdObject("artifact:art-rejected");
    const { items } = await loadAll();
    expect(items.artifact.find((a) => a.id === "art-far")).toMatchObject({
      id: "art-far", status: "pending-review", bodyMarkdown: "ARTIFACT10-15",
      sources: [{ source_type: "workbench", source_ref: "wb-source" }],
    });
    expect(items.artifact.find((a) => a.id === "art-rejected")?.status).toBe("rejected");
    const again = await loadAll();
    expect(ids(again.items.artifact)).toEqual(ids(items.artifact));
    expect(calls.filter((c) => c === "/api/artifacts/art-far")).toHaveLength(2);
    expect(calls).not.toContain("/api/sync/pull?limit=500");
    expect(calls.every((c) => !/accept|keep|publish|send/.test(c))).toBe(true);
  });

  it.each(["art-missing", "art-failed", "art-invalid"])("a failed exact source read stays local to its window: %s", async (id) => {
    holdObject(`artifact:${id}`);
    const { items, error, failed } = await loadAll();
    expect(ids(items.artifact)).not.toContain(id);
    expect(error).toBe("");
    expect(failed).toBeNull();
    expect(heldArtifactSource(id)?.sourceRead).toMatchObject({ hasMaterial: false });
    expect(objectWindowStandIn(`artifact:${id}`)?.ref).toMatchObject({ id, sourceRead: { hasMaterial: false } });
    expect(calls).toContain(`/api/artifacts/${id}`);
    expect(calls).not.toContain("/api/sync/pull?limit=500");
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
