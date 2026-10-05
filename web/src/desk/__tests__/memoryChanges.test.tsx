// Astra's PR #877 review, P1 + P2, fenced:
//  P1 — a write elsewhere (a note deleted) re-reads the memory faces; until
//       that read lands, a belief or a page sentence whose evidence names the
//       changed source is NOT drawn. A failed re-read keeps it held.
//  P2 — the standing pages are bound to their scope: on a scope change the
//       old scope's pages are gone at once, and a late answer for another
//       scope is dropped (Atlas sentences never drawn in Harbor's Room).
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { RecallFace } from "../../features/project-room/recall/RecallFace";
import type { BeliefCardData } from "../../features/project-room/recall/model";
import { StandingPagesSection, useStandingPages, type StandingPageWire } from "../standingPages";
import { changedIds, refId } from "../memoryChanges";

const bus = vi.hoisted(() => ({ handlers: new Set<(frame: unknown) => void>() }));
vi.mock("../../runtime/RuntimeBus", () => {
  const value = {
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      if (type !== "desk_changed") return () => undefined;
      bus.handlers.add(handler);
      return () => bus.handlers.delete(handler);
    },
  };
  return { useRuntimeBus: () => value };
});
vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../shell", async (original) => ({
  ...await original<typeof import("../shell")>(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
}));
vi.mock("../components/MicButton", () => ({
  MicButton: ({ label }: { label: string }) => <button type="button" className="desk-mic" aria-label={label} />,
}));
vi.mock("../surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt }: { receipt?: React.ReactNode }) => <footer>{receipt}</footer>,
}));

/** The frame the hub sends for `DELETE /api/notes/n2`. */
const deleted = (id: string) => ({
  type: "desk_changed",
  data: { kind: "note", id, op: "delete", origin: "owner", changes: [{ kind: "note", id, op: "delete" }] },
});
const send = (frame: unknown) => act(() => { bus.handlers.forEach((h) => h(frame)); });

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

const page = (slug: string, sentences: [string, string][]): StandingPageWire => ({
  slug, question: "What changed this week?",
  sentences: sentences.map(([text, ref]) => ({ text, refs: [{ ref, token: "NOTE 10-05", opens: true }] })),
  built_at: new Date().toISOString(), stale: false, new_sources: 0, model: "pages", boundary: "local",
});
const ATLAS = { pages: [page("what-changed-this-week", [
  ["Atlas cutover is 10-17.", "note:n2"], ["Atlas freeze is 10-12.", "meeting:m1"]])] };
const ATLAS_FRESH = { pages: [page("what-changed-this-week", [["Atlas freeze is 10-12.", "meeting:m1"]])] };
const HARBOR = { pages: [page("what-changed-this-week", [["Harbor budget is 40k.", "note:nh"]])] };

function Pages({ projectId }: { projectId: string }) {
  const pages = useStandingPages("project", projectId);
  return <StandingPagesSection pages={pages} onOpenRef={() => {}} />;
}

describe("the pure helpers", () => {
  it("a frame names its ids; a ref names its id", () => {
    expect(changedIds(deleted("n2").data)).toEqual(["n2"]);
    expect(changedIds({ kind: "desk", id: "" })).toEqual([]);
    expect(refId("note:n2")).toBe("n2");
    expect(refId("thread:t1#m4")).toBe("t1");
  });
});

describe("standing pages follow the bus (P1)", () => {
  beforeEach(() => { vi.mocked(apiFetch).mockReset(); bus.handlers.clear(); });

  it("a deleted source's sentence is not drawn from the frame on, while the re-read is in flight and when it fails", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(ATLAS);
    render(<Pages projectId="atlas" />);
    await screen.findByText("Atlas cutover is 10-17.");
    const reread = deferred<unknown>();
    vi.mocked(apiFetch).mockReturnValueOnce(reread.promise as Promise<never>);
    send(deleted("n2"));
    // At once, before any re-read: the n2 sentence is gone, the m1 one stays.
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    expect(screen.getByText("Atlas freeze is 10-12.")).toBeTruthy();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    // A failed re-read keeps the hold.
    await act(async () => { reread.reject(new Error("500")); });
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    // The next frame's re-read lands: the face draws the fresh answer.
    vi.mocked(apiFetch).mockResolvedValueOnce(ATLAS_FRESH);
    send({ type: "desk_changed", data: { kind: "meeting", id: "m9", op: "update" } });
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(3));
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    expect(screen.getByText("Atlas freeze is 10-12.")).toBeTruthy();
  });
});

describe("standing pages are bound to their scope (P2)", () => {
  beforeEach(() => { vi.mocked(apiFetch).mockReset(); bus.handlers.clear(); });

  it("a delayed Harbor answer: Atlas sentences are never drawn in Harbor's Room", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(ATLAS);
    const view = render(<Pages projectId="atlas" />);
    await screen.findByText("Atlas cutover is 10-17.");
    const harbor = deferred<unknown>();
    vi.mocked(apiFetch).mockReturnValueOnce(harbor.promise as Promise<never>);
    view.rerender(<Pages projectId="harbor" />);
    // The scope changed: nothing of Atlas, before Harbor's answer lands.
    expect(screen.queryByText(/Atlas/)).toBeNull();
    expect(screen.queryByTestId("standing-pages")).toBeNull();
    await act(async () => { harbor.resolve(HARBOR); });
    expect(screen.getByText("Harbor budget is 40k.")).toBeTruthy();
    expect(screen.queryByText(/Atlas/)).toBeNull();
  });

  it("a late Atlas answer after the switch to Harbor is dropped", async () => {
    const atlas = deferred<unknown>();
    vi.mocked(apiFetch).mockReturnValueOnce(atlas.promise as Promise<never>);
    const view = render(<Pages projectId="atlas" />);
    const harbor = deferred<unknown>();
    vi.mocked(apiFetch).mockReturnValueOnce(harbor.promise as Promise<never>);
    view.rerender(<Pages projectId="harbor" />);
    await act(async () => { harbor.resolve(HARBOR); });
    await act(async () => { atlas.resolve(ATLAS); });
    expect(screen.getByText("Harbor budget is 40k.")).toBeTruthy();
    expect(screen.queryByText(/Atlas/)).toBeNull();
  });
});

const BELIEF: BeliefCardData = {
  id: "obs-1", kind: "belief", text: "Atlas cutover is 10-17.", state: "current",
  proof_count: 1, source_count: 1, seen: "10-05", since: "", project: null,
  evidence: [{ ref: "note:n2", token: "NOTE 10-05", opens: true, against: false }], history: [],
};
const OTHER: BeliefCardData = {
  ...BELIEF, id: "obs-2", text: "Atlas freeze is 10-12.",
  evidence: [{ ref: "meeting:m1", token: "MTG 10-01 · 10:00", opens: true, against: false }],
};
const recall = (beliefs: BeliefCardData[]) => ({
  query: "cutover", filter: "all", searched_at: "2026-10-05T14:18:00", projects_searched: 2,
  current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [], also: [],
  beliefs, remembered: beliefs.length,
});

describe("Desk memory beliefs follow the bus (P1)", () => {
  beforeEach(() => { vi.mocked(apiFetch).mockReset(); bus.handlers.clear(); localStorage.clear(); });

  it("a deleted note's belief is not drawn from the frame on; the quiet re-read draws the fresh answer", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(recall([BELIEF, OTHER]));
    render(<RecallFace initialQuery="cutover" />);
    await screen.findByText("Atlas cutover is 10-17.");
    expect(screen.getByTestId("recall-display").textContent).toBe("2 remembered");
    const reread = deferred<unknown>();
    vi.mocked(apiFetch).mockReturnValueOnce(reread.promise as Promise<never>);
    send(deleted("n2"));
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    expect(screen.getByText("Atlas freeze is 10-12.")).toBeTruthy();
    expect(screen.getByTestId("recall-display").textContent).toBe("1 remembered");
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(2));
    // The re-read is the same search, quiet: no SEARCHING while it runs.
    expect(String(vi.mocked(apiFetch).mock.calls[1][0])).toBe("/api/memory/recall?query=cutover&filter=all");
    expect(screen.queryByTestId("recall-searching-token")).toBeNull();
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    await act(async () => { reread.resolve(recall([OTHER])); });
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    expect(screen.getByTestId("recall-display").textContent).toBe("1 remembered");
  });

  it("a failed re-read keeps the last result and the hold", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(recall([BELIEF, OTHER]));
    render(<RecallFace initialQuery="cutover" />);
    await screen.findByText("Atlas cutover is 10-17.");
    vi.mocked(apiFetch).mockRejectedValueOnce(new Error("500"));
    send(deleted("n2"));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(2));
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByText("Atlas cutover is 10-17.")).toBeNull();
    expect(screen.getByText("Atlas freeze is 10-12.")).toBeTruthy();
    expect(screen.queryByTestId("recall-failed-token")).toBeNull();
  });
});
