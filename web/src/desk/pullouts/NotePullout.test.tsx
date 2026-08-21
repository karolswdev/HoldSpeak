import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../lib/api";
import { useDesk } from "../store";
import { NotePullout } from "./NotePullout";
import { actOnReview, adoptThought, attachThoughtContext, completeThought, detachThoughtContext, listThoughtContext, originalThought, reconcileThought, refineThought, refreshThoughtContext, replaceDefaultThoughtContext, resumeThought, reviewThought, stopRefinement, thoughtForNote } from "../thoughts";

const { copySpy, flushThoughtEditor } = vi.hoisted(() => ({ copySpy: vi.fn(), flushThoughtEditor: vi.fn() }));

vi.mock("../surface/SurfaceFooter", () => ({ SurfaceFooter: ({ receipt, verbs }: { receipt?: unknown; verbs: unknown }) => <footer>{receipt as any}{verbs as any}</footer> }));
vi.mock("../components/DeskFilingStrip", () => ({ DeskFilingStrip: () => null }));
vi.mock("../surface/Material", () => ({ Material: ({ children }: { children: unknown }) => <>{children}</> }));
vi.mock("../surface/Surface", () => ({ SurfaceState: () => null }));
vi.mock("./editors", () => ({ INLINE_EDITOR_CONTENT: {} }));
vi.mock("./editors/ThoughtNoteEditor", async () => {
  const React = await import("react");
  return { ThoughtNoteEditor: React.forwardRef((_props, ref) => { React.useImperativeHandle(ref, () => ({ flush: flushThoughtEditor })); return null; }) };
});
vi.mock("../hooks/useCopyReceipt", () => ({ useCopyReceipt: () => ({ copy: copySpy, receipt: null }) }));
vi.mock("../api", async (importOriginal) => ({ ...(await importOriginal<typeof import("../api")>()), qualifiedRef: () => "note:note-1" }));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("../../lib/api")>()), apiFetch: vi.fn() }));
vi.mock("../thoughts", () => ({
  thoughtForNote: vi.fn(), adoptThought: vi.fn(), originalThought: vi.fn(), completeThought: vi.fn(), resumeThought: vi.fn(),
  refineThought: vi.fn(), stopRefinement: vi.fn(), reconcileThought: vi.fn(), reviewThought: vi.fn(), actOnReview: vi.fn(),
  listThoughtContext: vi.fn(), attachThoughtContext: vi.fn(), detachThoughtContext: vi.fn(), refreshThoughtContext: vi.fn(), replaceDefaultThoughtContext: vi.fn(),
  sourceLabel: (kind: string) => kind,
}));

const ordinary = {
  ownership: "ordinary" as const,
  note: { id: "note-1", title: "Note", body_markdown: "body", tags: [], last_modified: "1" },
  source_precondition: { content_sha256: "sha-1", last_modified: "1" },
};
const object = { id: "note-1", kind: "note", title: "Note", ref: { kind: "note", bodyMarkdown: "body" } } as any;
const ownedThought = {
  id: "thought-1", source: { kind: "typed" as const }, raw_captured_at: "2026-01-01T00:00:00Z",
  state: "working" as const, aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1,
  attachment_revision: 1, filing_status: "missing" as const,
  working_note: ordinary.note,
};
const everyday = {
  ref: "knowledge:hs-seed-everyday-context", kind: "knowledge" as const, title: "Everyday context",
  leaf_count: 5, state: "current" as const,
  leaves: [{ ref: "note:about", title: "About me", version_label: "version from 10:42" }],
};
const compactContext = {
  attachments: [],
  pinned: [{ ...everyday, leaves: undefined }],
  recent: [], results: [], next_cursor: null,
  default_context: { revision: 0, configuration_sha256: "empty", refs: [], selections: [] },
};

beforeEach(() => {
  vi.mocked(apiFetch).mockResolvedValue({ models: [] } as never);
  vi.mocked(listThoughtContext).mockResolvedValue(compactContext as any);
});
afterEach(() => { cleanup(); vi.clearAllMocks(); sessionStorage.clear(); });

describe("NotePullout adoption recovery", () => {
  it("keeps one refinement request id across an ambiguous retry and clears it after admission", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(refineThought).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce({
      thought: { ...ownedThought, continuity: { state: "reserved", invocation_id: "rinv-1" } }, continuity: { state: "reserved", invocation_id: "rinv-1" },
    });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const keep = await screen.findByRole("button", { name: "Ask AI" });
    fireEvent.click(keep);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Could not start refining"));
    const requestId = vi.mocked(refineThought).mock.calls[0][1];
    fireEvent.click(screen.getByRole("button", { name: "Ask AI" }));
    await waitFor(() => expect(refineThought).toHaveBeenCalledTimes(2));
    expect(vi.mocked(refineThought).mock.calls[1][1]).toBe(requestId);
    expect(sessionStorage.getItem("hs.thought.refine.thought-1")).toBeNull();
  });

  it("answers one reviewed question immediately without starting another model turn", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const ready = { ...ownedThought, continuity: { state: "review_ready", invocation_id: "rinv-1", review_result_id: "review-1" } };
    const answered = { ...ownedThought, aggregate_revision: 2, working_revision: 2, continuity: { state: "named_failure", code: "owner_answered" } };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ready });
    vi.mocked(reviewThought).mockResolvedValue({ id: "review-1", kind: "question", question: "Who owns launch?", reason: "Name one owner." });
    vi.mocked(actOnReview).mockResolvedValue({ thought: answered });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByText("Who owns launch?")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Answer" }), { target: { value: "Mina." } });
    fireEvent.click(screen.getByRole("button", { name: "Answer" }));
    await waitFor(() => expect(actOnReview).toHaveBeenCalledWith(expect.objectContaining({
      thought: ready, reviewId: "review-1", action: "answer", answer: "Mina.",
    })));
    expect(screen.getByRole("status")).toHaveTextContent("Answer added to your working note");
    expect(refineThought).not.toHaveBeenCalled();
  });

  it("keeps Stop primary while live and exposes direct Finish Thought through More", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const live = { ...ownedThought, continuity: { state: "in_flight", invocation_id: "rinv-live" } };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: live });
    vi.mocked(completeThought).mockResolvedValue({ thought: { ...live, state: "completed", aggregate_revision: 2, lifecycle_revision: 2 }, receipt: {
      id: "done-live", kind: "thought_completed", thought_id: "thought-1", note_ref: "note:note-1", aggregate_revision: 2, lifecycle_revision: 2, created_at: "now",
    } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Stop" })).toHaveClass("is-primary");
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    fireEvent.click(within(screen.getByRole("region", { name: "More thought actions" })).getByRole("button", { name: "Finish Thought" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
  });

  it("makes Finish Thought the sole primary when no model is ready", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ ready: false }] } as never);
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Finish Thought" })).toHaveClass("is-primary");
    expect(screen.queryByRole("button", { name: "Ask AI" })).not.toBeInTheDocument();
  });

  it("names a terminal model failure without hiding the owner's next actions", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const failed = { ...ownedThought, continuity: { state: "named_failure", invocation_id: "rinv-failed", code: "provider_failed" } };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: failed });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByRole("status")).toHaveTextContent("Could not get a useful question");
    expect(screen.getByRole("button", { name: "Ask AI" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Finish Thought" })).toBeInTheDocument();
  });
  it("executes Finish Thought immediately and leaves the same completed Note read-only with a receipt", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(completeThought).mockResolvedValue({ thought: { ...ownedThought, state: "completed", aggregate_revision: 2, lifecycle_revision: 2 }, receipt: {
      id: "rcomp-1", kind: "thought_completed", thought_id: "thought-1", note_ref: "note:note-1", aggregate_revision: 2, lifecycle_revision: 2, created_at: "now",
    } });
    const refresh = vi.fn().mockResolvedValue(undefined);
    useDesk.setState({ editingId: null, refresh, openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Finish Thought" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("button", { name: "Resume refining" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save" })).not.toBeInTheDocument();
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("renders and copies the authoritative accepted working Note rather than the stale pullout snapshot", async () => {
    const acceptedB = { ...ownedThought, aggregate_revision: 3, working_revision: 3,
      working_note: { ...ordinary.note, title: "Accepted B title", body_markdown: "Accepted B body" } };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: acceptedB });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByText("Accepted B body")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    expect(copySpy).toHaveBeenCalledWith("Accepted B body");
  });

  it("resumes a completed Note through lifecycle CAS before opening its editor", async () => {
    const completed = { ...ownedThought, state: "completed" as const, aggregate_revision: 2, lifecycle_revision: 2 };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: completed });
    vi.mocked(resumeThought).mockResolvedValue({ ...completed, state: "working", aggregate_revision: 3, lifecycle_revision: 3 });
    const openEditor = vi.fn();
    const refresh = vi.fn().mockResolvedValue(undefined);
    useDesk.setState({ editingId: null, refresh, openEditor, closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Resume refining" }));
    await waitFor(() => expect(resumeThought).toHaveBeenCalledWith(completed));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    expect(openEditor).toHaveBeenCalledWith("note-1");
  });

  it("clears a prior completion key on Resume so the next Finish Thought uses a new request", async () => {
    const completed = { ...ownedThought, state: "completed" as const, aggregate_revision: 2, lifecycle_revision: 2 };
    const resumed = { ...completed, state: "working" as const, aggregate_revision: 3, lifecycle_revision: 3 };
    sessionStorage.setItem("hs.thought.complete.thought-1", "K");
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: completed });
    vi.mocked(resumeThought).mockResolvedValue(resumed);
    vi.mocked(completeThought).mockResolvedValue({ thought: { ...resumed, state: "completed", aggregate_revision: 4, lifecycle_revision: 4 }, receipt: {
      id: "rcomp-new", kind: "thought_completed", thought_id: "thought-1", note_ref: "note:note-1", aggregate_revision: 4, lifecycle_revision: 4, created_at: "now",
    } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Resume refining" }));
    await waitFor(() => expect(sessionStorage.getItem("hs.thought.complete.thought-1")).toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "Finish Thought" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
    expect(vi.mocked(completeThought).mock.calls[0][0].request_id).not.toBe("K");
  });

  it("clears a stale completion key and does not loop it after its named conflict", async () => {
    sessionStorage.setItem("hs.thought.complete.thought-1", "K");
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(completeThought).mockRejectedValueOnce(new ApiError(409, "stale", { error: "completion_request_payload_mismatch" }));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Finish Thought" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("no longer current"));
    expect(sessionStorage.getItem("hs.thought.complete.thought-1")).toBeNull();
  });

  it("does not call completion when the editor flush reports a retained save failure", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    flushThoughtEditor.mockRejectedValueOnce(new Error("thought save failed"));
    useDesk.setState({ editingId: "note-1", refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Finish Thought" }));
    await waitFor(() => expect(flushThoughtEditor).toHaveBeenCalledTimes(1));
    expect(completeThought).not.toHaveBeenCalled();
    expect(screen.queryByText("We couldn't confirm completion on this hub. Your thought is still here. Retry Finish Thought.")).not.toBeInTheDocument();
  });

  it("keeps the request id and names a generic adoption failure without claiming a change", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue(ordinary);
    vi.mocked(adoptThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("unchanged and still here"));
    const firstId = vi.mocked(adoptThought).mock.calls[0][0].request_id;

    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Develop this thought" })); });
    await waitFor(() => expect(adoptThought).toHaveBeenCalledTimes(2));
    expect(vi.mocked(adoptThought).mock.calls[1][0].request_id).toBe(firstId);
  });

  it("uses changed-elsewhere language only for the named adoption CAS response", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue(ordinary);
    vi.mocked(adoptThought).mockRejectedValue(new ApiError(409, "conflict", {
      error: "note_adoption_conflict", note: { ...ordinary.note, title: "Current", last_modified: "2" },
      source_precondition: { content_sha256: "sha-2", last_modified: "2" },
    }));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("changed elsewhere"));
  });

  it("does not claim unchanged when adoption recovery cannot read ownership", async () => {
    vi.mocked(thoughtForNote).mockResolvedValueOnce(ordinary).mockResolvedValueOnce(ordinary).mockRejectedValueOnce(new Error("offline"));
    vi.mocked(adoptThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("couldn't confirm whether this was saved"));
    expect(screen.getByRole("status")).not.toHaveTextContent("unchanged");
  });

  it("scrolls a successful Original reveal into the nearest visible pullout position", async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(originalThought).mockResolvedValue({ ...ownedThought, raw_text: "Exact original" });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: /Original kept/ }));
    await waitFor(() => expect(screen.getByText("Exact original")).toBeInTheDocument());
    expect(screen.getByText("Exact original")).toHaveClass("thought-original-raw");
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "nearest", behavior: "smooth" });
    expect(screen.getByRole("region", { name: "Original kept" })).toHaveFocus();
  });

  it("does not scroll when Original fails to load", async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(originalThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: /Original kept/ }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Could not open the original"));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("keeps AI context empty by default and attaches pinned Everyday in one authoritative selection", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [] } });
    const attached = { ...ownedThought, aggregate_revision: 2, attachment_revision: 2, attachments: [everyday] };
    vi.mocked(attachThoughtContext).mockResolvedValue({
      thought: attached,
      receipt: { id: "ctx-1", action: "attach", ref: everyday.ref, title: everyday.title, leaf_count: 5, leaves: everyday.leaves },
    });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);

    const context = await screen.findByRole("region", { name: "Thought context" });
    expect(within(context).getByText("AI context")).toBeInTheDocument();
    expect(within(context).getByText("None")).toBeInTheDocument();
    fireEvent.click(within(context).getByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    expect(await within(picker).findByText("Pinned")).toBeInTheDocument();
    expect(within(picker).queryByText("All notes")).not.toBeInTheDocument();
    expect(within(picker).getByRole("searchbox", { name: "Search notes" })).not.toHaveFocus();
    fireEvent.click(within(picker).getByRole("button", { name: "Everyday context, 5 notes" }));

    await waitFor(() => expect(attachThoughtContext).toHaveBeenCalledWith(expect.objectContaining({ id: "thought-1" }), everyday.ref, expect.any(String), undefined));
    expect(screen.queryByRole("region", { name: "Attach context" })).not.toBeInTheDocument();
    expect(screen.getByText("Everyday context · 5 notes")).toBeInTheDocument();
    expect(screen.getByText("Attached Everyday context")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("region", { name: "Thought context" })).toHaveFocus());
  });

  it("shows both authoritative groups and only offers Use when this Thought has context", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [] } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    expect(within(picker).getByRole("heading", { name: "On this Thought" })).toBeInTheDocument();
    expect(within(picker).getByRole("heading", { name: "For new Thoughts" })).toBeInTheDocument();
    expect(within(picker).getByText("Attach context to use it by default.")).toBeVisible();
    expect(within(picker).queryByRole("button", { name: "Use these by default" })).not.toBeInTheDocument();
    expect(within(picker).queryByRole("button", { name: "Stop using by default" })).not.toBeInTheDocument();
  });

  it("closes the context sheet with Escape and returns focus to AI context", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [] } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const context = await screen.findByRole("region", { name: "Thought context" });
    fireEvent.click(within(context).getByRole("button", { name: "Attach" }));
    expect(await screen.findByRole("region", { name: "Attach context" })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("region", { name: "Attach context" })).not.toBeInTheDocument();
    await waitFor(() => expect(context).toHaveFocus());
  });

  it("replaces the complete future set and keeps persistent Default markers scoped", async () => {
    const launch = { ref: "note:launch", kind: "note" as const, title: "Project launch", leaf_count: 1, state: "current" as const, leaves: [] };
    const current = [{ ...everyday, is_default: true }, launch];
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: current } });
    vi.mocked(listThoughtContext).mockResolvedValue({
      ...compactContext, attachments: current, default_context: {
        revision: 3, configuration_sha256: "configured", refs: [everyday.ref],
        selections: [{ ref: everyday.ref, title: everyday.title, leaf_count: 5, state: "current" }],
      },
    } as any);
    vi.mocked(replaceDefaultThoughtContext).mockResolvedValue({
      default_context: { revision: 4, configuration_sha256: "both", refs: [everyday.ref, launch.ref], selections: [] },
      receipt: { id: "default-4", action: "replace_default_context", scope: "future_thoughts", prior_revision: 3, revision: 4, configuration_sha256: "both", refs: [everyday.ref, launch.ref], selections: [{ ref: everyday.ref, title: everyday.title, leaf_count: 5 }, { ref: launch.ref, title: launch.title, leaf_count: 1 }], no_op: false, existing_thoughts_changed: 0 },
    });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect((await screen.findAllByText("Default")).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    expect(within(picker).getAllByRole("button", { name: "Remove from this Thought" })).toHaveLength(2);
    await within(picker).findByRole("button", { name: "Stop using by default" });
    await act(async () => { fireEvent.click(within(picker).getByRole("button", { name: "Use these by default" })); });
    await waitFor(() => expect(replaceDefaultThoughtContext).toHaveBeenCalledWith(expect.objectContaining({
      expected_revision: 3, refs: [everyday.ref, launch.ref],
    })));
    expect(await screen.findByText("Used Everyday context + Project launch for new Thoughts")).toBeInTheDocument();
  });

  it("clears the whole future set without changing this Thought", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [everyday] } });
    vi.mocked(listThoughtContext).mockResolvedValue({ ...compactContext, attachments: [everyday], default_context: {
      revision: 2, configuration_sha256: "configured", refs: [everyday.ref], selections: [{ ref: everyday.ref, title: everyday.title, leaf_count: 5, state: "current" }],
    } } as any);
    vi.mocked(replaceDefaultThoughtContext).mockResolvedValue({ default_context: { revision: 3, configuration_sha256: "empty", refs: [], selections: [] }, receipt: {
      id: "default-3", action: "replace_default_context", scope: "future_thoughts", prior_revision: 2, revision: 3, configuration_sha256: "empty", refs: [], selections: [], no_op: false, existing_thoughts_changed: 0,
    } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    fireEvent.click(await within(picker).findByRole("button", { name: "Stop using by default" }));
    await waitFor(() => expect(replaceDefaultThoughtContext).toHaveBeenCalledWith(expect.objectContaining({ expected_revision: 2, refs: [] })));
    expect(await screen.findByText("New Thoughts start with no AI context. This Thought is unchanged.")).toBeInTheDocument();
    expect(screen.getByText("Everyday context · 5 notes")).toBeInTheDocument();
  });

  it("renders a named whole-set-skipped receipt on the first not-applied render", async () => {
    sessionStorage.setItem("hs.thought.default-context-receipt.thought-1", JSON.stringify({
      id: "app-failed", action: "apply_default_context", scope: "this_thought", thought_id: "thought-1",
      default_revision: 4, default_configuration_sha256: "configured", status: "not_applied",
      attachment_zero_sha256: "zero", attachment_revision: 0, attachment_sha256: "zero", attachments: [],
      failure: { code: "default_context_missing", selections: [{ ref: everyday.ref, title: everyday.title }] },
    }));
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachment_revision: 0, attachments: [] } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByText("Default AI context was not applied")).toBeVisible();
    expect(screen.getByText(/Everyday context could not be attached.*The whole set was skipped\./)).toBeVisible();
    expect(screen.getByText("None")).toBeVisible();
  });

  it("keeps the picker open on attach failure and exposes overlap as Included, not selectable", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [] } });
    vi.mocked(listThoughtContext).mockResolvedValue({
      ...compactContext,
      pinned: [
        compactContext.pinned[0],
        { ref: "note:about", kind: "note", title: "About me", leaf_count: 1, state: "current", disabled: true, disabled_reason: "Included in Everyday context" },
      ],
    } as any);
    vi.mocked(attachThoughtContext).mockRejectedValue(new ApiError(409, "Everyday context changed", { error: "context_changed" }));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    expect(await within(picker).findByRole("button", { name: "About me, Included in Everyday context" })).toBeDisabled();
    const everydayButton = within(picker).getByRole("button", { name: "Everyday context, 5 notes" });
    fireEvent.click(everydayButton);
    expect(await within(picker).findByRole("alert")).toHaveTextContent("Everyday context changed");
    expect(screen.getByRole("region", { name: "Attach context" })).toBeInTheDocument();
    await waitFor(() => expect(everydayButton).toHaveFocus());
    const firstRequest = vi.mocked(attachThoughtContext).mock.calls[0][2];
    fireEvent.click(everydayButton);
    await waitFor(() => expect(attachThoughtContext).toHaveBeenCalledTimes(2));
    expect(vi.mocked(attachThoughtContext).mock.calls[1][2]).toBe(firstRequest);
  });

  it("keeps the catalog behind Browse and searches through the server", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [] } });
    vi.mocked(listThoughtContext).mockImplementation(async (_id, input) => input.view === "browse" || input.query
      ? { attachments: [], pinned: compactContext.pinned as any, recent: [], results: [{ ref: "note:launch", kind: "note", title: "Launch notes", leaf_count: 1, state: "current" }], next_cursor: null }
      : compactContext as any);
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Attach" }));
    const picker = await screen.findByRole("region", { name: "Attach context" });
    expect(await within(picker).findByText("Pinned")).toBeInTheDocument();
    expect(within(picker).queryByText("Launch notes")).not.toBeInTheDocument();
    fireEvent.click(within(picker).getByRole("button", { name: "Browse all notes" }));
    expect(await within(picker).findByText("Launch notes")).toBeInTheDocument();
    fireEvent.click(within(picker).getByRole("button", { name: "Back" }));
    fireEvent.change(within(picker).getByRole("searchbox", { name: "Search notes" }), { target: { value: "launch" } });
    await waitFor(() => expect(listThoughtContext).toHaveBeenLastCalledWith("thought-1", expect.objectContaining({ query: "launch" })));
  });

  it("makes Update context the only primary for idle stale context", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const stale = { ...everyday, state: "stale" as const };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: { ...ownedThought, attachments: [stale] } });
    vi.mocked(refreshThoughtContext).mockResolvedValue({
      thought: { ...ownedThought, aggregate_revision: 2, attachment_revision: 2, attachments: [everyday] },
      receipt: { id: "ctx-2", action: "refresh", ref: stale.ref, title: stale.title, leaf_count: 5, leaves: stale.leaves },
    });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const primary = (await screen.findAllByRole("button", { name: "Update context" })).find((button) => button.classList.contains("is-primary"))!;
    expect(primary).toHaveClass("is-primary");
    expect(screen.getByText("Everyday context changed. Update it before asking another question.")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Ask AI" })).not.toBeInTheDocument();
    expect(document.querySelectorAll(".is-primary")).toHaveLength(1);
    fireEvent.click(primary);
    await waitFor(() => expect(refreshThoughtContext).toHaveBeenCalledWith(expect.objectContaining({ id: "thought-1" }), stale.ref, expect.any(String)));
  });

  it("keeps Answer primary for a stale question and replaces stale synthesis Accept with Update context", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const stale = { ...everyday, state: "stale" as const };
    const questionThought = { ...ownedThought, attachments: [stale], continuity: { state: "review_ready", invocation_id: "inv-q", review_result_id: "review-q" } };
    vi.mocked(thoughtForNote).mockResolvedValueOnce({ ownership: "thought", thought: questionThought } as any);
    vi.mocked(reviewThought).mockResolvedValueOnce({ id: "review-q", kind: "question", question: "Who owns it?", used_context: { visible_count: 1, leaf_count: 5, summary: "Used Everyday context · 5 notes", attachments: [everyday] } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    const rendered = render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByText("Used Everyday context · 5 notes")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Answer" }), { target: { value: "Mina" } });
    expect(screen.getByRole("button", { name: "Answer" })).toHaveClass("is-primary");
    expect(screen.getAllByRole("button", { name: "Update context" }).every((button) => !button.classList.contains("is-primary"))).toBe(true);
    rendered.unmount();

    const synthesisThought = { ...ownedThought, attachments: [stale], continuity: { state: "review_ready", invocation_id: "inv-s", review_result_id: "review-s" } };
    vi.mocked(thoughtForNote).mockResolvedValueOnce({ ownership: "thought", thought: synthesisThought } as any);
    vi.mocked(reviewThought).mockResolvedValueOnce({ id: "review-s", kind: "synthesis", title: "A plan", body_markdown: "Plan" });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByText("A plan")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Accept" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Update context" }).some((button) => button.classList.contains("is-primary"))).toBe(true);
  });

  it("keeps Original raw text wrapped locally without normalizing its bytes", () => {
    const css = readFileSync(resolve(process.cwd(), "src/desk/components/pullout.css"), "utf8");
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*white-space:\s*pre-wrap;/s);
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*overflow-wrap:\s*anywhere;/s);
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*max-width:\s*100%;/s);
  });

  it("keeps one full-width completion primary at the 393px surface breakpoint", () => {
    const css = readFileSync(resolve(process.cwd(), "src/desk/components/pullout.css"), "utf8");
    expect(css).toMatch(/@container surface \(max-width: 420px\)[\s\S]*\.thought-completion-secondary\s*\{\s*display:\s*none;/);
    expect(css).toMatch(/\.thought-completion-primary\s*\{[\s\S]*width:\s*100%;/);
    expect(css).toMatch(/\.thought-editor-cancel\s*\{\s*display:\s*inline-flex;/);
  });
});
