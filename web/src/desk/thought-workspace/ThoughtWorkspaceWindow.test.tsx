import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import {
  actOnReview,
  answerAndContinue,
  refineThought,
  saveThoughtWorkingInWorkspace,
  stopRefinement,
  thoughtWorkbench,
  type Thought,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import { ThoughtWorkspaceWindow } from "./ThoughtWorkspaceWindow";

vi.mock("../components/DeskWindow", () => ({
  DeskWindowFrame: ({ children, onClose }: { children: React.ReactNode; onClose: () => void }) => <section aria-label="Thought"><button onClick={onClose}>Close window</button>{children}</section>,
}));
vi.mock("./ThoughtDocumentPane", () => ({
  ThoughtDocumentPane: ({ draft, onEdit }: { draft: { title: string; body: string }; onEdit: (patch: { body: string }) => void }) => <section aria-label="Note"><h1>{draft.title}</h1><textarea aria-label="Note body" value={draft.body} onChange={(event) => onEdit({ body: event.target.value })} /></section>,
}));
vi.mock("../pullouts/ThoughtContextPicker", () => ({ ThoughtContextPicker: ({ thought: current, workspaceCursor }: { thought: Thought; workspaceCursor: { continuity_revision: number } }) => <section aria-label="Attach context">{current.working_note.body_markdown} · cursor {workspaceCursor.continuity_revision}</section> }));
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
    answerAndContinue: vi.fn(),
    completeThought: vi.fn(),
    resumeThought: vi.fn(),
    stopRefinement: vi.fn(),
    detachThoughtContext: vi.fn(),
    refreshThoughtContext: vi.fn(),
  };
});

const thought: Thought = {
  id: "thought-1",
  source: { kind: "typed" },
  raw_captured_at: "2026-08-19T00:00:00Z",
  state: "working",
  aggregate_revision: 3,
  lifecycle_revision: 1,
  working_revision: 2,
  attachment_revision: 1,
  attachments: [],
  working_note: { id: "note-1", title: "Launch ownership", body_markdown: "The launch needs an owner.", tags: [] },
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
    context_status: { summary: "None", state: "empty", repair_ref: null },
    inference: { availability: "ready", continuation_admission: "ready", intended_placement: { target_id: "this_machine", target_name: "This device", target_kind: "this_device", boundary: "same_device", readiness: "ready" } },
    terminal_status: null,
    ...overrides,
  };
}

const object = { id: "note-1", kind: "note", title: "Launch ownership", ref: { kind: "note", bodyMarkdown: thought.working_note.body_markdown } } as never;

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

describe("ThoughtWorkspaceWindow", () => {
  it("opens into the document/interview composition with exactly one state primary", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    expect(await screen.findByRole("button", { name: "Ask AI" })).toHaveClass("thought-state-primary");
    expect(screen.getByRole("button", { name: "Finish Thought" })).not.toHaveClass("btn--primary");
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
    expect(screen.getByRole("region", { name: "Note" })).toHaveTextContent("Launch ownership");
    expect(screen.getByRole("region", { name: "Interview" })).toHaveTextContent("One click reads the saved Note");
    expect(screen.queryByText(/Good enough|Keep refining|Finish instead/)).not.toBeInTheDocument();
  });

  it("turns unavailable AI into direct Models recovery and rechecks after Settings saves", async () => {
    const unavailable = projection({
      actions: { primary: { kind: "configure_ai" }, state: [{ kind: "configure_ai" }], ambient: ["update_working", "attach_context", "complete"] },
      inference: { availability: "unavailable", continuation_admission: "unavailable", intended_placement: null },
    });
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(unavailable).mockResolvedValueOnce(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const setup = await screen.findByRole("button", { name: "Set up AI" });
    const interview = screen.getByRole("region", { name: "Interview" });
    expect(interview).toHaveTextContent("AI needs a model");
    expect(within(interview).getByRole("button", { name: "Set up AI" })).toBe(setup);
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
    expect(document.querySelector(".thought-workspace-command .thought-state-primary")).toBeNull();
    fireEvent.click(setup);
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");

    window.dispatchEvent(new Event("holdspeak:settings-updated"));
    expect(await screen.findByRole("button", { name: "Ask AI" })).toBeEnabled();
  });

  it("uses the fixed mobile seat only as a proxy to the visible setup action", async () => {
    Object.defineProperty(window, "matchMedia", { configurable: true, writable: true, value: (query: string) => ({ matches: true, media: query, onchange: null, addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false }) });
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      actions: { primary: { kind: "configure_ai" }, state: [{ kind: "configure_ai" }], ambient: ["update_working", "attach_context", "complete"] },
      inference: { availability: "unavailable", continuation_admission: "unavailable", intended_placement: null },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const proxy = await screen.findByRole("button", { name: "Set up AI" });
    expect(proxy).toHaveClass("thought-state-primary");
    fireEvent.click(proxy);
    const buttons = screen.getAllByRole("button", { name: "Set up AI" });
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toHaveClass("thought-setup-ai");
    await waitFor(() => expect(buttons[0]).toHaveFocus());
  });

  it("keeps the answer and full composite payload stable across an ambiguous failure", async () => {
    const question = projection({
      workspace_state: "question",
      actions: { primary: { kind: "answer_and_continue", review_result_id: "review-1" }, state: [{ kind: "answer_and_continue", review_result_id: "review-1" }, { kind: "answer_review", review_result_id: "review-1" }], ambient: ["update_working", "attach_context", "complete"] },
      review: { id: "review-1", kind: "question", question: "Who owns launch?", reason: "Name one owner.", frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
    });
    vi.mocked(thoughtWorkbench).mockResolvedValue(question);
    vi.mocked(answerAndContinue).mockRejectedValue(new ApiError(503, "Connection lost", {}));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const answer = await screen.findByRole("textbox", { name: "Your answer" });
    fireEvent.change(answer, { target: { value: "Mina owns it." } });
    fireEvent.click(screen.getByRole("button", { name: "Add & ask next" }));
    await waitFor(() => expect(answerAndContinue).toHaveBeenCalledTimes(1));
    expect(answer).toHaveValue("Mina owns it.");
    await waitFor(() => expect(answer).toHaveFocus());
    const first = vi.mocked(answerAndContinue).mock.calls[0][0];
    expect(JSON.parse(sessionStorage.getItem("hs.thought.answer-next.review-1") || "null")).toEqual(first);

    fireEvent.click(screen.getByRole("button", { name: "Add & ask next" }));
    await waitFor(() => expect(answerAndContinue).toHaveBeenCalledTimes(2));
    expect(vi.mocked(answerAndContinue).mock.calls[1][0]).toEqual(first);
  });

  it("shows the exact admission-race recovery while retaining answer, focus, and key", async () => {
    const question = projection({
      workspace_state: "question",
      actions: { primary: { kind: "answer_and_continue", review_result_id: "review-race" }, state: [{ kind: "answer_and_continue", review_result_id: "review-race" }], ambient: ["update_working", "attach_context", "complete"] },
      review: { id: "review-race", kind: "question", question: "What changes?", frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
    });
    vi.mocked(thoughtWorkbench).mockResolvedValue(question);
    vi.mocked(answerAndContinue).mockRejectedValue(new ApiError(409, "unavailable", { error: "refinement_continuation_unavailable", workbench: question }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    const answer = await screen.findByRole("textbox", { name: "Your answer" });
    fireEvent.change(answer, { target: { value: "The launch date." } });
    fireEvent.click(screen.getByRole("button", { name: "Add & ask next" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Couldn't start the next turn. Your answer is still here. Add it to the Note.");
    expect(answer).toHaveValue("The launch date.");
    await waitFor(() => expect(answer).toHaveFocus());
    expect(sessionStorage.getItem("hs.thought.answer-next.review-race")).not.toBeNull();
  });

  it("promotes Add to Note when continuation admission is unavailable and suppresses its quiet duplicate", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      workspace_state: "question",
      actions: { primary: { kind: "answer_review", review_result_id: "review-1" }, state: [{ kind: "answer_review", review_result_id: "review-1" }], ambient: ["update_working", "attach_context", "complete"] },
      review: { id: "review-1", kind: "question", question: "Who owns launch?", frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
      inference: { availability: "ready", continuation_admission: "unavailable", intended_placement: null },
    }));
    vi.mocked(actOnReview).mockResolvedValue({ thought, workbench: projection() });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const interview = await screen.findByRole("region", { name: "Interview" });
    expect(screen.getAllByRole("button", { name: "Add to Note" })).toHaveLength(1);
    expect(within(interview).queryByRole("button", { name: "Add to Note" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add & ask next" })).not.toBeInTheDocument();
  });

  it("keeps the mobile Note-tab question proxy enabled before an answer exists", async () => {
    Object.defineProperty(window, "matchMedia", { configurable: true, writable: true, value: (query: string) => ({ matches: true, media: query, onchange: null, addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false }) });
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      workspace_state: "question",
      actions: { primary: { kind: "answer_and_continue", review_result_id: "review-mobile" }, state: [{ kind: "answer_and_continue", review_result_id: "review-mobile" }], ambient: ["update_working", "attach_context", "complete"] },
      review: { id: "review-mobile", kind: "question", question: "Who owns launch?", frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const proxy = await screen.findByRole("button", { name: "Answer question" });
    expect(proxy).toBeEnabled();
    fireEvent.click(proxy);
    expect(await screen.findByRole("textbox", { name: "Your answer" })).toBeVisible();
  });

  it("labels only a retryable named failure as Try again in the fixed action seat", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({
      workspace_state: "named_failure",
      actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["complete"] },
      terminal_status: { category: "retryable", code: "engine_busy", retryable: true, message: "The engine was busy." },
    }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Try again" })).toHaveClass("thought-state-primary");
    expect(screen.queryByRole("button", { name: "Ask AI" })).not.toBeInTheDocument();
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
    fireEvent.click(await screen.findByRole("button", { name: "Ask AI" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("This hub restarted");
    expect(screen.getByRole("textbox", { name: "Note body", hidden: true })).toHaveValue(thought.working_note.body_markdown);
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(foreign);
    fireEvent.click(screen.getByRole("button", { name: "Reload Thought" }));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("Foreign authority"));
  });

  it("scopes Mod-Enter to the focused Workbench when two Thoughts are open", async () => {
    const second = { ...thought, id: "thought-2", working_note: { ...thought.working_note, id: "note-2", title: "Second thought" } };
    const questionFor = (item: Thought): ThoughtWorkspaceProjection => projection({
      thought: item,
      workspace_cursor: { ...cursor, thought_id: item.id },
      workspace_state: "question",
      actions: { primary: { kind: "answer_and_continue", review_result_id: `review-${item.id}` }, state: [{ kind: "answer_and_continue", review_result_id: `review-${item.id}` }], ambient: ["update_working", "attach_context", "complete"] },
      review: { id: `review-${item.id}`, kind: "question", question: `Question for ${item.id}?`, frozen_aggregate_revision: 3, frozen_working_revision: 2, frozen_attachment_revision: 1 },
    });
    vi.mocked(thoughtWorkbench).mockImplementation(async (id) => questionFor(id === second.id ? second : thought));
    vi.mocked(answerAndContinue).mockRejectedValue(new ApiError(503, "offline", {}));
    const secondObject = { id: "note-2", kind: "note", title: "Second thought", ref: { kind: "note", bodyMarkdown: second.working_note.body_markdown } } as never;
    render(<><ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} /><ThoughtWorkspaceWindow object={secondObject} thought={second} onClose={vi.fn()} /></>);

    const answers = await screen.findAllByRole("textbox", { name: "Your answer" });
    fireEvent.change(answers[0], { target: { value: "First" } });
    fireEvent.change(answers[1], { target: { value: "Second" } });
    answers[1].focus();
    fireEvent.keyDown(answers[1], { key: "Enter", metaKey: true });

    await waitFor(() => expect(answerAndContinue).toHaveBeenCalledTimes(1));
    expect(vi.mocked(answerAndContinue).mock.calls[0][0].thought_id).toBe("thought-2");
  });

  it.each([{ metaKey: true }, { ctrlKey: true }])("uses $metaKey/$ctrlKey Mod-S to drain only the focused Workbench", async (modifier) => {
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
    expect(await screen.findByRole("status")).toHaveTextContent(/save failed/i);
  });

  it("drains the sole writer before opening context and advances the picker cursor", async () => {
    const saved = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "Saved before context" } };
    const nextCursor = { ...cursor, aggregate_revision: 4, continuity_revision: 5 };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockResolvedValue({ thought: saved, workbench: projection({ thought: saved, workspace_cursor: nextCursor }) });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Note body" }), { target: { value: "Saved before context" } });
    fireEvent.click(screen.getByRole("button", { name: "Attach" }));

    expect(await screen.findByRole("region", { name: "Attach context" })).toHaveTextContent("Saved before context · cursor 5");
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
    await waitFor(() => expect(screen.getByRole("button", { name: "Ask AI" })).toBeEnabled());
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
