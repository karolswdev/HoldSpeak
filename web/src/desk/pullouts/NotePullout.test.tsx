import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../lib/api";
import { useDesk } from "../store";
import { NotePullout } from "./NotePullout";
import { actOnReview, adoptThought, completeThought, originalThought, reconcileThought, refineThought, resumeThought, reviewThought, stopRefinement, thoughtForNote } from "../thoughts";

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

beforeEach(() => { vi.mocked(apiFetch).mockResolvedValue({ models: [] } as never); });
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
    const keep = await screen.findByRole("button", { name: "Keep refining" });
    fireEvent.click(keep);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Could not start refining"));
    const requestId = vi.mocked(refineThought).mock.calls[0][1];
    fireEvent.click(screen.getByRole("button", { name: "Keep refining" }));
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

  it("keeps Stop primary while live and exposes YOLO Finish instead through More", async () => {
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
    fireEvent.click(within(screen.getByRole("region", { name: "More thought actions" })).getByRole("button", { name: "Finish instead" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
  });

  it("makes Good enough the sole primary when no model is ready", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ ready: false }] } as never);
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Good enough" })).toHaveClass("is-primary");
    expect(screen.queryByRole("button", { name: "Keep refining" })).not.toBeInTheDocument();
  });

  it("names a terminal model failure without hiding the owner's next actions", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ models: [{ id: "this_machine", ready: true }] } as never);
    const failed = { ...ownedThought, continuity: { state: "named_failure", invocation_id: "rinv-failed", code: "provider_failed" } };
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: failed });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    expect(await screen.findByRole("status")).toHaveTextContent("Could not get a useful question");
    expect(screen.getByRole("button", { name: "Keep refining" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Finish instead" })).toBeInTheDocument();
  });
  it("executes Good enough immediately and leaves the same completed Note read-only with a receipt", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(completeThought).mockResolvedValue({ thought: { ...ownedThought, state: "completed", aggregate_revision: 2, lifecycle_revision: 2 }, receipt: {
      id: "rcomp-1", kind: "thought_completed", thought_id: "thought-1", note_ref: "note:note-1", aggregate_revision: 2, lifecycle_revision: 2, created_at: "now",
    } });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Good enough" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
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
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor, closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Resume refining" }));
    await waitFor(() => expect(resumeThought).toHaveBeenCalledWith(completed));
    expect(openEditor).toHaveBeenCalledWith("note-1");
  });

  it("clears a prior completion key on Resume so the next Good enough uses a new request", async () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Good enough" }));
    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
    expect(vi.mocked(completeThought).mock.calls[0][0].request_id).not.toBe("K");
  });

  it("clears a stale completion key and does not loop it after its named conflict", async () => {
    sessionStorage.setItem("hs.thought.complete.thought-1", "K");
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(completeThought).mockRejectedValueOnce(new ApiError(409, "stale", { error: "completion_request_payload_mismatch" }));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Good enough" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("no longer current"));
    expect(sessionStorage.getItem("hs.thought.complete.thought-1")).toBeNull();
  });

  it("does not call completion when the editor flush reports a retained save failure", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    flushThoughtEditor.mockRejectedValueOnce(new Error("thought save failed"));
    useDesk.setState({ editingId: "note-1", refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Good enough" }));
    await waitFor(() => expect(flushThoughtEditor).toHaveBeenCalledTimes(1));
    expect(completeThought).not.toHaveBeenCalled();
    expect(screen.queryByText("We couldn't confirm completion on this hub. Your thought is still here. Retry Good enough.")).not.toBeInTheDocument();
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
