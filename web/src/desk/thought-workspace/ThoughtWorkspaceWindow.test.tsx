import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import {
  actOnReview,
  completeThought,
  refineThought,
  saveThoughtWorkingInWorkspace,
  stopRefinement,
  thoughtWorkbench,
  type Thought,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import { ThoughtWorkspaceWindow } from "./ThoughtWorkspaceWindow";

/* HS-201-12 — doctrine (a) for the tests this file lost.
 *
 * The settled design of story 12 gives band 3 ONE verb ("Add to note"), so
 * the chained turn ("Add & ask next", `answer_and_continue`) and its
 * admission-race recovery left THIS window; the service and its idempotent
 * composite are untouched (`desk/thoughts.ts:answerAndContinue`) and the
 * Note pullout still drives them. The 393 tab nav ("Note" / "Interview 1")
 * left with the two-pane composition — at 393 the same four bands stack, so
 * the mobile proxy tests describe a face that no longer exists. Nothing was
 * papered over: every test below runs against the real reducer.
 */

vi.mock("../components/DeskWindow", () => ({
  DeskWindowFrame: ({ children, onClose }: { children: React.ReactNode; onClose: () => void }) => <section aria-label="Thought"><button onClick={onClose}>Close window</button>{children}</section>,
}));
vi.mock("./ThoughtDocumentPane", () => ({
  ThoughtDocumentPane: ({ draft, onEdit, lockedReason }: { draft: { title: string; body: string }; onEdit: (patch: { body: string }) => void; lockedReason?: string }) => <section aria-label="Note"><span data-testid="note-title">{draft.title}</span>{lockedReason ? <span data-testid="note-locked">{lockedReason}</span> : null}<textarea aria-label="Note body" value={draft.body} onChange={(event) => onEdit({ body: event.target.value })} /></section>,
}));
vi.mock("./ThoughtReadsWell", () => ({
  ThoughtReadsWell: ({ thought }: { thought: Thought }) => <div role="region" aria-label="What the AI reads">{thought.working_note.body_markdown}</div>,
}));
vi.mock("../sprites", () => ({ spriteUrl: () => "note.png" }));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../thoughts", async (importOriginal) => {
  const original = await importOriginal<typeof import("../thoughts")>();
  return {
    ...original,
    thoughtWorkbench: vi.fn(),
    saveThoughtWorking: vi.fn(),
    saveThoughtWorkingInWorkspace: vi.fn(),
    refineThought: vi.fn(),
    actOnReview: vi.fn(),
    completeThought: vi.fn(),
    resumeThought: vi.fn(),
    stopRefinement: vi.fn(),
    detachThoughtContext: vi.fn(),
    refreshThoughtContext: vi.fn(),
  };
});

const context = { ref: "knowledge:everyday", kind: "knowledge" as const, title: "Everyday context", leaf_count: 5, state: "current" as const, leaves: [] };

const thought: Thought = {
  id: "thought-1",
  source: { kind: "voice" },
  raw_captured_at: "2026-08-19T00:00:00Z",
  state: "working",
  aggregate_revision: 3,
  lifecycle_revision: 1,
  working_revision: 2,
  attachment_revision: 1,
  attachments: [context],
  working_note: { id: "note-1", title: "Well, there's just a little bit of misunderstanding here", body_markdown: "Yeah, I have it that way and what about you?", tags: [] },
  filing_status: "filed",
};

const cursor = { hub_id: "hub-1", thought_id: thought.id, aggregate_revision: 3, continuity_revision: 4 };
const originalMatchMedia = window.matchMedia;

function projection(overrides: Partial<ThoughtWorkspaceProjection> = {}): ThoughtWorkspaceProjection {
  return {
    schema_version: 1,
    process_scope: { kind: "hub_local", hub_id: "hub-1", state: "available" },
    workspace_cursor: cursor,
    thought,
    workspace_state: "idle",
    actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["update_working", "attach_context", "complete"] },
    review: null,
    context_status: { summary: "Everyday context", state: "current", repair_ref: null },
    inference: { availability: "ready", continuation_admission: "ready", intended_placement: { target_id: "this_machine", target_name: "This device", target_kind: "this_device", boundary: "same_device", readiness: "ready" } },
    terminal_status: null,
    ...overrides,
  };
}

function questionProjection(question: string, id = "review-1"): ThoughtWorkspaceProjection {
  return projection({
    workspace_state: "question",
    actions: { primary: { kind: "answer_review", review_result_id: id }, state: [{ kind: "answer_review", review_result_id: id }], ambient: ["update_working", "attach_context", "complete"] },
    review: { id, kind: "question", question, frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
  });
}

const object = { id: "note-1", kind: "note", title: "Thought", ref: { kind: "note", bodyMarkdown: thought.working_note.body_markdown } } as never;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  sessionStorage.clear();
  useDesk.setState({ editingId: null, closeEditor: vi.fn() });
});
afterEach(() => {
  cleanup();
  if (vi.isFakeTimers()) {
    vi.clearAllTimers();
    vi.useRealTimers();
  }
  vi.clearAllMocks();
  Object.defineProperty(window, "matchMedia", { configurable: true, writable: true, value: originalMatchMedia });
});

describe("ThoughtWorkspaceWindow — the four bands", () => {
  it("folds band 3 to one row, says the context once, and holds one filled primary", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const ask = await screen.findByRole("button", { name: "Ask" });
    const band = screen.getByRole("region", { name: "One question" });
    expect(band).toHaveTextContent("ONE QUESTION");
    expect(band.querySelectorAll(".thought-note-ask-open")).toHaveLength(0);
    expect(screen.queryByRole("textbox", { name: "Your answer" })).not.toBeInTheDocument();
    expect(ask).not.toHaveClass("btn--primary");

    // The context fact is stated ONCE, in the Reads line of the foot.
    expect(screen.getAllByText(/Everyday context/)).toHaveLength(1);
    expect(screen.getByText(/READS · Everyday context · 5 NOTES/)).toBeInTheDocument();
    expect(screen.queryByText(/^Attached/)).not.toBeInTheDocument();

    // One filled primary, and it is Finish. "Kept", never "Filed"/"Saved".
    const primaries = document.querySelectorAll(".btn--primary");
    expect(primaries).toHaveLength(1);
    expect(primaries[0]).toHaveTextContent("Finish");
    // PHILO-3-04: the filing state is its own line; KEPT carries a time
    // and needs a hub stamp, which this fixture's note does not have.
    expect(screen.getByText("IN A DRAWER")).toBeInTheDocument();
    expect(screen.queryByText(/Filed|Saved/)).not.toBeInTheDocument();

    // The window that was two features is one: no tabs, no rail, no rack.
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Interview/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Interview" })).not.toBeInTheDocument();
  });

  it("never renders a heading over an empty question", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("   "));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    await screen.findByRole("region", { name: "Note" });
    // The defect the owner shot: a kicker over an h2 that renders nothing.
    const headings = [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")];
    expect(headings.filter((node) => !node.textContent?.trim())).toHaveLength(0);
    expect(headings).toHaveLength(0);
    await screen.findByRole("region", { name: "One question" });
    const texts = document.querySelectorAll(".thought-note-ask-text");
    expect(texts).toHaveLength(0);
    for (const node of document.querySelectorAll(".thought-note-ask *")) {
      expect(node.textContent?.trim().length === 0 && node.children.length === 0 && node.tagName !== "IMG").toBe(false);
    }
  });

  it("names the engine before the ask and shows the question with one verb", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Who is misunderstanding what?"));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const band = await screen.findByRole("region", { name: "One question" });
    expect(band).toHaveTextContent("Who is misunderstanding what?");
    expect(band.querySelector(".gadget-chip-egress")).toHaveTextContent("THIS DEVICE");
    expect(screen.getByRole("textbox", { name: "Your answer" })).toBeVisible();
    expect(screen.getAllByRole("button", { name: "Add to note" })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /ask next/i })).not.toBeInTheDocument();
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
  });

  it("keeps the answer and reuses one request id when Add to note fails", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Who owns launch?"));
    vi.mocked(actOnReview).mockRejectedValue(new ApiError(503, "Connection lost", {}));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const answer = await screen.findByRole("textbox", { name: "Your answer" });
    fireEvent.change(answer, { target: { value: "Mina owns it." } });
    fireEvent.click(screen.getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(actOnReview).toHaveBeenCalledTimes(1));
    expect(answer).toHaveValue("Mina owns it.");
    await waitFor(() => expect(answer).toHaveFocus());

    fireEvent.click(screen.getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(actOnReview).toHaveBeenCalledTimes(2));
    const [first, second] = vi.mocked(actOnReview).mock.calls;
    expect(second[0].request_id).toBe(first[0].request_id);
    expect(second[0].answer).toBe("Mina owns it.");
  });

  it("adds a typed answer, then keeps against the cursor that answer advanced", async () => {
    // Astra finding 2: completing against the pre-answer cursor is the 409
    // `workspace_cursor_conflict` her isolated-hub probe recorded.
    const answered = { ...thought, aggregate_revision: 4, working_revision: 3 };
    const answeredCursor = { ...cursor, aggregate_revision: 4, continuity_revision: 6 };
    const afterAnswer = projection({ thought: answered, workspace_cursor: answeredCursor });
    vi.mocked(thoughtWorkbench)
      .mockResolvedValueOnce(questionProjection("Who owns launch?"))
      .mockResolvedValue(afterAnswer);
    vi.mocked(actOnReview).mockResolvedValue({ thought: answered, workbench: afterAnswer });
    vi.mocked(completeThought).mockResolvedValue({
      thought: { ...answered, state: "completed" },
      receipt: { id: "receipt-1", kind: "thought_completed", thought_id: thought.id, note_ref: "note:note-1", aggregate_revision: 5, lifecycle_revision: 2, created_at: "2026-09-20T09:50:00Z" },
      workbench: projection({ thought: { ...answered, state: "completed" }, workspace_state: "completed" }),
    });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Your answer" }), { target: { value: "Mina owns it." } });
    fireEvent.click(screen.getByRole("button", { name: "Finish" }));

    await waitFor(() => expect(completeThought).toHaveBeenCalledTimes(1));
    expect(vi.mocked(actOnReview).mock.calls[0][0].answer).toBe("Mina owns it.");
    expect(vi.mocked(actOnReview).mock.invocationCallOrder[0])
      .toBeLessThan(vi.mocked(completeThought).mock.invocationCallOrder[0]);
    const completion = vi.mocked(completeThought).mock.calls[0][0];
    expect(completion.workspace_cursor).toEqual(answeredCursor);
    expect(completion.thought.aggregate_revision).toBe(4);
    expect(completion.thought.working_revision).toBe(3);
  });

  it("appends a returned draft to the note instead of replacing it", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      workspace_state: "synthesis",
      actions: { primary: { kind: "accept_review", review_result_id: "review-draft" }, state: [{ kind: "accept_review", review_result_id: "review-draft" }], ambient: ["complete"] },
      review: { id: "review-draft", kind: "synthesis", title: "A tidier title", body_markdown: "Mina owns the launch date.", frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
    }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(async (current, patch) => ({
      thought: { ...current, aggregate_revision: current.aggregate_revision + 1, working_revision: current.working_revision + 1, working_note: { ...current.working_note, title: patch.title ?? current.working_note.title, body_markdown: patch.body_markdown ?? current.working_note.body_markdown } },
      workbench: projection(),
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const band = await screen.findByRole("region", { name: "One question" });
    expect(band).toHaveTextContent("A draft from your note");
    expect(band).toHaveTextContent("Mina owns the launch date.");
    expect(screen.queryByRole("textbox", { name: "Your answer" })).not.toBeInTheDocument();
    expect(document.querySelectorAll("h1, h2, h3, h4")).toHaveLength(0);
    const add = screen.getAllByRole("button", { name: "Add to note" });
    expect(add).toHaveLength(1);
    fireEvent.click(add[0]);

    // The hub's `accept` REPLACES title, body and tags — this window must
    // never call it; the draft joins the note through the sole writer.
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1));
    expect(actOnReview).not.toHaveBeenCalled();
    const patch = vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[0][1];
    expect(patch.body_markdown).toBe(`${thought.working_note.body_markdown}\n\nMina owns the launch date.`);
    expect(patch.title).toBe(thought.working_note.title);
  });

  it("offers Reload — not a dead Try again — when the note changed elsewhere", async () => {
    // `writer.retry` returns during a conflict (useThoughtNoteWriter.ts:238),
    // so the conflict recovery verb must re-read the note and work.
    const elsewhere = { ...thought, aggregate_revision: 9, working_revision: 7, working_note: { ...thought.working_note, body_markdown: "The version the hub holds" } };
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(projection()).mockResolvedValue(projection({ thought: elsewhere }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockRejectedValue(new ApiError(409, "conflict", { context: { current: elsewhere } }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const body = await screen.findByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "My own edit" } });
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalled());
    await screen.findByText("CHANGED ELSEWHERE");
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() => expect(body).toHaveValue("The version the hub holds"));
    await waitFor(() => expect(screen.queryByText("CHANGED ELSEWHERE")).not.toBeInTheDocument());
  });

  it("says a save failure once, in the foot, with its own Retry", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockRejectedValue(new Error("offline"));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Note body" }), { target: { value: "An edit that cannot land" } });
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalled());
    const line = await screen.findByText("DID NOT SAVE · THE HUB DID NOT ANSWER");
    expect(line.closest(".surface-footer")).not.toBeNull();
    expect(screen.getAllByText("DID NOT SAVE · THE HUB DID NOT ANSWER")).toHaveLength(1);
    expect(screen.queryByText(/^KEPT/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(2));
  });

  it("reopens a finished note with the reason it cannot be edited and Resume", async () => {
    const finished = { ...thought, state: "completed" as const };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({ thought: finished, workspace_state: "completed", actions: { primary: { kind: "resume" }, state: [{ kind: "resume" }], ambient: [] } }));
    render(<ThoughtWorkspaceWindow object={object} thought={finished} onClose={vi.fn()} />);

    expect(await screen.findByTestId("note-title")).toHaveTextContent(thought.working_note.title);
    expect(screen.getByTestId("note-locked")).toHaveTextContent("FINISHED");
    // PHILO-3-04: FINISHED joins the filing line (canvas, state 1).
    expect(screen.getByText("IN A DRAWER · FINISHED")).toBeInTheDocument();
    const primaries = document.querySelectorAll(".btn--primary");
    expect(primaries).toHaveLength(1);
    expect(primaries[0]).toHaveTextContent("Resume");
    expect(screen.queryByRole("region", { name: "One question" })).not.toBeInTheDocument();
  });

  it("separates no engine at all from an engine that cannot be reached", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      actions: { primary: { kind: "configure_ai" }, state: [{ kind: "configure_ai" }], ambient: ["update_working", "attach_context", "complete"] },
      inference: { availability: "unavailable", continuation_admission: "unavailable", intended_placement: null },
    }));
    const { unmount } = render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const band = await screen.findByRole("region", { name: "One question" });
    expect(band).toHaveTextContent("NO ENGINE YET");
    expect(band.querySelector(".gadget-chip-egress")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Choose an engine" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
    unmount();

    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      actions: { primary: { kind: "configure_ai" }, state: [{ kind: "configure_ai" }], ambient: ["update_working", "attach_context", "complete"] },
      inference: { availability: "unavailable", continuation_admission: "unavailable", intended_placement: { target_id: "lan", target_name: "Workstation", target_kind: "lan_host", boundary: "private_network", readiness: "unreachable" } },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Check" })).toBeEnabled();
    expect(screen.getByRole("region", { name: "One question" })).toHaveTextContent("ENGINE NOT REACHABLE");
    expect(screen.getByText("WORKSTATION")).toBeInTheDocument();
    // …and no destination chip stands beside "no engine yet" (nowhere to go).
    expect(document.querySelectorAll(".gadget-chip-egress")).toHaveLength(1);
  });

  it("does not call a ready engine missing when the coordinator is the blocker", async () => {
    // refinement_application_service.py:80 — inference_available is
    // (coordinator accepting) AND (target ready); a ready target with
    // unavailable inference is a BUSY coordinator, not an absent engine.
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["complete"] },
      inference: {
        availability: "unavailable",
        continuation_admission: "unavailable",
        intended_placement: { target_id: "this_machine", target_name: "This device", target_kind: "this_device", boundary: "same_device", readiness: "ready" },
      },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const band = await screen.findByRole("region", { name: "One question" });
    expect(band).toHaveTextContent("ENGINE BUSY");
    expect(band).not.toHaveTextContent("NO ENGINE YET");
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Choose an engine" })).not.toBeInTheDocument();
  });

  it("rechecks the engine after Settings saves", async () => {
    vi.mocked(thoughtWorkbench)
      .mockResolvedValueOnce(projection({
        actions: { primary: { kind: "configure_ai" }, state: [{ kind: "configure_ai" }], ambient: ["complete"] },
        inference: { availability: "unavailable", continuation_admission: "unavailable", intended_placement: null },
      }))
      .mockResolvedValueOnce(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    await screen.findByRole("button", { name: "Choose an engine" });
    window.dispatchEvent(new Event("holdspeak:settings-updated"));
    expect(await screen.findByRole("button", { name: "Ask" })).toBeEnabled();
  });

  it("says one plain reason for a failed ask and offers Try again beside Finish", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      workspace_state: "named_failure",
      actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["complete"] },
      terminal_status: { category: "retryable", code: "engine_busy", retryable: true, message: "The engine was busy." },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    expect(await screen.findByRole("button", { name: "Try again" })).toBeEnabled();
    expect(screen.getByRole("region", { name: "One question" })).toHaveTextContent("The engine was busy.");
    expect(screen.getByRole("button", { name: "Finish" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Ask" })).not.toBeInTheDocument();
  });

  it("keeps a stale context visible in the Reads line with its repair verb", async () => {
    const staleThought = { ...thought, attachments: [{ ...context, state: "stale" as const }] };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      thought: staleThought,
      workspace_state: "stale",
      actions: { primary: { kind: "refresh_context" }, state: [{ kind: "refresh_context" }], ambient: ["complete"] },
      context_status: { summary: "Everyday context", state: "stale", repair_ref: context.ref },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={staleThought} onClose={vi.fn()} />);

    expect(await screen.findByText(/READS · Everyday context · 5 NOTES · CHANGED/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Update it" })).toBeEnabled();
  });

  it("keeps the mounted workspace behind a restart gate until explicit hub adoption", async () => {
    const foreignThought = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "Foreign authority" } };
    const foreign = projection({ thought: foreignThought, workspace_cursor: { ...cursor, hub_id: "hub-2", aggregate_revision: 4, continuity_revision: 1 } });
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(projection());
    vi.mocked(refineThought).mockResolvedValue({
      thought: foreignThought,
      continuity: { state: "reserved", invocation_id: "rinv-foreign" },
      workbench: foreign,
    });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Ask" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Hub restarted");
    expect(screen.getByRole("textbox", { name: "Note body", hidden: true })).toHaveValue(thought.working_note.body_markdown);
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(foreign);
    fireEvent.click(screen.getByRole("button", { name: "Reload Thought" }));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("Foreign authority"));
  });

  it("scopes Mod-Enter to the focused window when two Thoughts are open", async () => {
    const second = { ...thought, id: "thought-2", working_note: { ...thought.working_note, id: "note-2", title: "Second thought" } };
    const questionFor = (item: Thought): ThoughtWorkspaceProjection => ({
      ...questionProjection(`Question for ${item.id}?`, `review-${item.id}`),
      thought: item,
      workspace_cursor: { ...cursor, thought_id: item.id },
    });
    vi.mocked(thoughtWorkbench).mockImplementation(async (id) => questionFor(id === second.id ? second : thought));
    vi.mocked(actOnReview).mockRejectedValue(new ApiError(503, "offline", {}));
    const secondObject = { id: "note-2", kind: "note", title: "Second thought", ref: { kind: "note", bodyMarkdown: second.working_note.body_markdown } } as never;
    render(<><ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} /><ThoughtWorkspaceWindow object={secondObject} thought={second} onClose={vi.fn()} /></>);

    const answers = await screen.findAllByRole("textbox", { name: "Your answer" });
    fireEvent.change(answers[0], { target: { value: "First" } });
    fireEvent.change(answers[1], { target: { value: "Second" } });
    answers[1].focus();
    fireEvent.keyDown(answers[1], { key: "Enter", metaKey: true });

    await waitFor(() => expect(actOnReview).toHaveBeenCalledTimes(1));
    expect(vi.mocked(actOnReview).mock.calls[0][0].thought.id).toBe("thought-2");
  });

  it.each([{ metaKey: true }, { ctrlKey: true }])("uses $metaKey/$ctrlKey Mod-S to drain only the focused window", async (modifier) => {
    const second = { ...thought, id: "thought-save-2", working_note: { ...thought.working_note, id: "note-save-2", title: "Second thought" } };
    vi.mocked(thoughtWorkbench).mockImplementation(async (id) => projection({ thought: id === second.id ? second : thought, workspace_cursor: { ...cursor, thought_id: id } }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(async (current, _patch, currentCursor) => ({ thought: current, workbench: projection({ thought: current, workspace_cursor: currentCursor! }) }));
    const secondObject = { id: "note-save-2", kind: "note", title: "Second thought", ref: { kind: "note", bodyMarkdown: second.working_note.body_markdown } } as never;
    render(<><ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} /><ThoughtWorkspaceWindow object={secondObject} thought={second} onClose={vi.fn()} /></>);
    const bodies = await screen.findAllByRole("textbox", { name: "Note body" });
    fireEvent.change(bodies[0], { target: { value: "First dirty" } });
    fireEvent.change(bodies[1], { target: { value: "Second dirty" } });
    fireEvent.keyDown(bodies[1], { key: "s", ...modifier });

    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1));
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[0][0].id).toBe(second.id);
  });

  it("vetoes close when the dirty Note cannot flush and keeps the draft", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockRejectedValue(new Error("offline"));
    const onClose = vi.fn();
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={onClose} />);

    const body = await screen.findByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "Unsaved owner detail" } });
    fireEvent.click(screen.getByRole("button", { name: "Close window" }));

    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1));
    expect(onClose).not.toHaveBeenCalled();
    expect(body).toHaveValue("Unsaved owner detail");
    expect(await screen.findByRole("status")).toBeInTheDocument();
  });

  it("drains the sole writer before the Reads well opens on the latest note", async () => {
    const saved = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "Saved before context" } };
    const nextCursor = { ...cursor, aggregate_revision: 4, continuity_revision: 5 };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockResolvedValue({ thought: saved, workbench: projection({ thought: saved, workspace_cursor: nextCursor }) });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Note body" }), { target: { value: "Saved before context" } });
    fireEvent.click(screen.getByRole("button", { name: "Change" }));

    expect(await screen.findByRole("region", { name: "What the AI reads" })).toHaveTextContent("Saved before context");
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledWith(thought, expect.objectContaining({ body_markdown: "Saved before context" }), cursor);
  });

  it("stops only the live process while preserving a dirty Note draft", async () => {
    const liveThought = { ...thought, continuity: { invocation_id: "invocation-1" } } as Thought;
    const live = projection({
      thought: liveThought,
      workspace_state: "in_flight",
      actions: { primary: { kind: "stop_refinement" }, state: [{ kind: "stop_refinement" }], ambient: ["update_working"] },
    });
    const stopped = projection({ thought: liveThought, workspace_state: "idle" });
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(live).mockResolvedValueOnce(stopped);
    vi.mocked(stopRefinement).mockResolvedValue(liveThought);
    render(<ThoughtWorkspaceWindow object={object} thought={liveThought} onClose={vi.fn()} />);

    const body = await screen.findByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "Dirty while AI runs" } });
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));

    await waitFor(() => expect(stopRefinement).toHaveBeenCalledWith(liveThought, "invocation-1", cursor));
    await waitFor(() => expect(screen.getByRole("button", { name: "Ask" })).toBeEnabled());
    expect(body).toHaveValue("Dirty while AI runs");
  });

  it("fences the dirty-Note debounce until Stop has completed", async () => {
    vi.useFakeTimers();
    const liveThought = { ...thought, continuity: { invocation_id: "invocation-slow" } } as Thought;
    const live = projection({
      thought: liveThought,
      workspace_state: "in_flight",
      actions: { primary: { kind: "stop_refinement" }, state: [{ kind: "stop_refinement" }], ambient: ["update_working"] },
    });
    const stopped = deferred<Thought>();
    vi.mocked(thoughtWorkbench).mockResolvedValue(live);
    vi.mocked(stopRefinement).mockReturnValue(stopped.promise);
    render(<ThoughtWorkspaceWindow object={object} thought={liveThought} onClose={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });

    const body = screen.getByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "Dirty during slow Stop" } });
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    fireEvent.keyDown(body, { key: "s", ctrlKey: true });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });

    expect(stopRefinement).toHaveBeenCalledTimes(1);
    expect(saveThoughtWorkingInWorkspace).not.toHaveBeenCalled();
    expect(body).toHaveValue("Dirty during slow Stop");
    await act(async () => { stopped.resolve(liveThought); await Promise.resolve(); });
  });

  it("waits for an in-flight save before Stop without flushing the queued edit", async () => {
    vi.useFakeTimers();
    const liveThought = { ...thought, continuity: { invocation_id: "invocation-ordered" } } as Thought;
    const live = projection({ thought: liveThought, workspace_state: "in_flight", actions: { primary: { kind: "stop_refinement" }, state: [{ kind: "stop_refinement" }], ambient: ["update_working"] } });
    const save = deferred<{ thought: Thought; workbench: ThoughtWorkspaceProjection }>();
    const stopped = deferred<Thought>();
    const savedThought = { ...liveThought, aggregate_revision: 4, working_revision: 3, working_note: { ...liveThought.working_note, body_markdown: "A" } };
    const savedCursor = { ...cursor, aggregate_revision: 4, continuity_revision: 5 };
    vi.mocked(thoughtWorkbench).mockResolvedValue(live);
    vi.mocked(saveThoughtWorkingInWorkspace).mockReturnValue(save.promise);
    vi.mocked(stopRefinement).mockReturnValue(stopped.promise);
    render(<ThoughtWorkspaceWindow object={object} thought={liveThought} onClose={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });

    const body = screen.getByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    fireEvent.change(body, { target: { value: "B queued" } });
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    expect(stopRefinement).not.toHaveBeenCalled();

    await act(async () => {
      save.resolve({ thought: savedThought, workbench: projection({ thought: savedThought, workspace_cursor: savedCursor, workspace_state: "in_flight" }) });
      await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
    });
    expect(stopRefinement).toHaveBeenCalledWith(savedThought, "invocation-ordered", savedCursor);
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1);
    expect(body).toHaveValue("B queued");
    await act(async () => { stopped.resolve(savedThought); await Promise.resolve(); });
  });
});
