import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { attachThoughtContext, detachThoughtContext, listThoughtContext, type Thought } from "../thoughts";
import { ThoughtReadsWell } from "./ThoughtReadsWell";

vi.mock("../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../thoughts")>()),
  attachThoughtContext: vi.fn(), detachThoughtContext: vi.fn(), listThoughtContext: vi.fn(),
}));

// The existing workspace scenario's aggregate and context row; only the
// transport outcomes vary here. No owner hub or microphone is invoked.
const context = { ref: "knowledge:everyday", kind: "knowledge" as const, title: "Everyday context", leaf_count: 5, state: "current" as const, leaves: [] };
const thought: Thought = {
  id: "reads-storage-thought", source: { kind: "voice" }, raw_captured_at: "2026-08-19T00:00:00Z",
  state: "working", aggregate_revision: 3, lifecycle_revision: 1, working_revision: 2, attachment_revision: 1,
  attachments: [], working_note: { id: "note-1", title: "Thought", body_markdown: "Working note", tags: [] }, filing_status: "filed",
};
const cursor = { hub_id: "hub-1", thought_id: thought.id, aggregate_revision: 3, continuity_revision: 4 };
const listing = {
  attachments: [], pinned: [context], recent: [], results: [], next_cursor: null,
  default_context: { revision: 0, configuration_sha256: "empty", refs: [], selections: [] },
};
const attached = { thought: { ...thought, aggregate_revision: 4, attachment_revision: 2, attachments: [context] }, receipt: { id: "ctx-attached", action: "attach" as const, ref: context.ref, title: context.title, leaf_count: 5, leaves: [] } };

beforeEach(() => {
  vi.mocked(listThoughtContext).mockReset().mockResolvedValue(listing);
  vi.mocked(attachThoughtContext).mockReset().mockResolvedValue(attached);
  vi.mocked(detachThoughtContext).mockReset().mockResolvedValue({ ...attached, thought, receipt: { ...attached.receipt, action: "detach" } });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); sessionStorage.clear(); });

describe("ThoughtReadsWell recovery", () => {
  it("keeps the new action ID across set denial after accepted cleanup left an older stored ID", async () => {
    const onApplied = vi.fn();
    const host = render(<ThoughtReadsWell thought={thought} cursor={cursor} onApplied={onApplied} onClose={vi.fn()}/>);
    const check = await screen.findByRole("checkbox", { name: context.title });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => { throw new Error("Cleanup denied"); });
    fireEvent.click(check);
    await waitFor(() => expect(onApplied).toHaveBeenCalledTimes(1));
    const acceptedId = vi.mocked(attachThoughtContext).mock.calls[0][2];
    const key = `hs.thought.reads.attach.${thought.id}.${context.ref}`;
    expect(sessionStorage.getItem(key)).toBe(acceptedId);

    // A later authoritative aggregate has removed that context. Attaching
    // again is a new action, while refused cleanup left the old stored ID.
    const later = { ...thought, aggregate_revision: 5, attachment_revision: 3 };
    host.rerender(<ThoughtReadsWell thought={later} cursor={{ ...cursor, aggregate_revision: 5 }} onApplied={onApplied} onClose={vi.fn()}/>);
    await waitFor(() => expect(listThoughtContext).toHaveBeenCalledTimes(2));
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Write denied"); });
    vi.mocked(attachThoughtContext).mockRejectedValueOnce(new Error("offline"));
    fireEvent.click(screen.getByRole("checkbox", { name: context.title }));
    expect(await screen.findByRole("alert")).toHaveTextContent("offline");
    const newId = vi.mocked(attachThoughtContext).mock.calls[1][2];
    expect(newId).not.toBe(acceptedId);
    expect(sessionStorage.getItem(key)).toBe(acceptedId);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(onApplied).toHaveBeenCalledTimes(2));
    expect(vi.mocked(attachThoughtContext).mock.calls[2][2]).toBe(newId);
  });

  it.each(["getItem", "setItem"] as const)("reuses its attach request after storage %s and transport refuse", async (method) => {
    const onApplied = vi.fn();
    vi.mocked(attachThoughtContext).mockRejectedValueOnce(new Error("offline"));
    render(<ThoughtReadsWell thought={thought} cursor={cursor} onApplied={onApplied} onClose={vi.fn()}/>);
    const check = await screen.findByRole("checkbox", { name: context.title });
    vi.spyOn(Storage.prototype, method).mockImplementation(() => { throw new Error("Storage denied"); });
    fireEvent.click(check);
    expect(await screen.findByRole("alert")).toHaveTextContent("offline");
    expect(check).toBeEnabled();
    const id = vi.mocked(attachThoughtContext).mock.calls[0][2];
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(onApplied).toHaveBeenCalledWith(attached));
    expect(vi.mocked(attachThoughtContext).mock.calls[1]).toEqual([thought, context.ref, id, cursor]);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it.each(["attach", "detach"] as const)("applies the accepted %s receipt even when cleanup refuses", async (action) => {
    const held = action === "detach" ? { ...thought, attachments: [context] } : thought;
    vi.mocked(listThoughtContext).mockResolvedValue({ ...listing, attachments: held.attachments ?? [] });
    const onApplied = vi.fn();
    render(<ThoughtReadsWell thought={held} cursor={cursor} onApplied={onApplied} onClose={vi.fn()}/>);
    const check = await screen.findByRole("checkbox", { name: context.title });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => { throw new Error("Storage denied"); });
    fireEvent.click(check);
    await waitFor(() => expect(onApplied).toHaveBeenCalledTimes(1));
    expect(onApplied.mock.calls[0][0].receipt.action).toBe(action);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(check).toBeEnabled();
  });

  it("shows loading before a genuine empty read, and retries a failed listing", async () => {
    let finish!: (value: typeof listing) => void;
    vi.mocked(listThoughtContext).mockReturnValueOnce(new Promise((resolve) => { finish = resolve; }));
    render(<ThoughtReadsWell thought={thought} onApplied={vi.fn()} onClose={vi.fn()}/>);
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText("Nothing to read yet")).toBeNull();
    await waitFor(() => expect(listThoughtContext).toHaveBeenCalledTimes(1));
    await act(async () => finish({ ...listing, pinned: [] }));
    expect(screen.getByText("Nothing to read yet")).toBeVisible();
    vi.mocked(listThoughtContext).mockRejectedValueOnce(new Error("Read failed"));
    fireEvent.change(screen.getByRole("textbox", { name: "Add notes" }), { target: { value: "launch" } });
    expect(await screen.findByRole("alert")).toHaveTextContent("Read failed");
    expect(screen.queryByText("No match")).toBeNull();
    vi.mocked(listThoughtContext).mockResolvedValueOnce({ ...listing, results: [context] });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("checkbox", { name: context.title })).toBeEnabled();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
