import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
  NOTE_GREW_EVENT,
  type Thought,
  type ThoughtWorkspaceProjection,
} from "../thoughts";
import { ThoughtWorkspaceWindow } from "./ThoughtWorkspaceWindow";
import { latchAskSelection, takeAskSelection } from "../ask";

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

vi.mock("../components/DeskWindow", async () => {
  const { useState } = await import("react");
  const { FootSlotContext } = await import("../surface/foot");
  return {
    DeskWindowFrame: ({ children, onClose, beforeClose, onBack, label, minH, className }: { children: React.ReactNode; onClose: () => void; beforeClose?: () => Promise<boolean>; onBack?: () => void; label?: string; minH?: number; className?: string }) => {
      const [foot, setFoot] = useState<HTMLElement | null>(null);
      return <section aria-label="Thought" className={className} data-window-name={label} data-frame-min-height={minH} data-frame-close-guard={Boolean(beforeClose)}>
        <button onClick={() => { void (async () => { if (!beforeClose || await beforeClose()) onClose(); })(); }}>Close window</button>
        {onBack ? <button onClick={onBack}>Frame Back</button> : null}
        <FootSlotContext.Provider value={foot}>{children}</FootSlotContext.Provider>
        <footer ref={setFoot} className="surface-footer" data-testid="frame-foot" />
      </section>;
    },
  };
});
vi.mock("./ThoughtDocumentPane", () => ({
  ThoughtDocumentPane: ({ draft, onEdit, onSelectionChange, lockedReason }: { draft: { title: string; body: string }; onEdit: (patch: { body: string }) => void; onSelectionChange?: (selection: { from: number; to: number; text: string }) => void; lockedReason?: string }) => <section aria-label="Note"><span data-testid="note-title">{draft.title}</span>{lockedReason ? <span data-testid="note-locked">{lockedReason}</span> : null}<textarea aria-label="Note body" value={draft.body} onChange={(event) => { onEdit({ body: event.target.value }); onSelectionChange?.({ from: 0, to: 0, text: "" }); }} /><button type="button" data-testid="select-second-line" onClick={() => { const text = draft.body.split(/\r?\n/)[1] || draft.body.split(/\r?\n/)[0] || ""; const from = draft.body.indexOf(text); onSelectionChange?.({ from, to: from + text.length, text }); }}>Select second line</button></section>,
}));
vi.mock("../documentSendsLazy", () => ({
  NoteSendWells: ({ id, title, version }: { id: string; title?: string; version?: number }) => <div data-testid="send-well" data-doc={`note:${id}`} data-title={title} data-version={String(version)} />,
}));
vi.mock("../sprites", () => ({ spriteUrl: () => "note.png" }));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../hooks/useEngine", () => engineMock);
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
const engineMock = vi.hoisted(() => ({ useEngine: vi.fn(), refreshEngine: vi.fn() }));

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
  // clearAllMocks keeps unused once responses. Each projection scenario
  // must start with its own response queue, even after an async reread.
  vi.mocked(thoughtWorkbench).mockReset();
  sessionStorage.clear();
  latchAskSelection(null);
  useDesk.setState({ editingId: null, closeEditor: vi.fn(), askOpen: false, selectedIds: [] });
  engineMock.useEngine.mockReturnValue({ state: "unread", model: "", place: "" });
});
afterEach(() => {
  latchAskSelection(null);
  cleanup();
  if (vi.isFakeTimers()) {
    vi.clearAllTimers();
    vi.useRealTimers();
  }
  vi.clearAllMocks();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  Object.defineProperty(window, "matchMedia", { configurable: true, writable: true, value: originalMatchMedia });
});

describe("ThoughtWorkspaceWindow — the four bands", () => {
  it.each(["getItem", "setItem"] as const)("keeps the active answer retry identity when storage %s refuses", async (method) => {
    const answered = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "Mina owns launch." } };
    const accepted = projection({ thought: answered, workspace_cursor: { ...cursor, aggregate_revision: 4, continuity_revision: 5 } });
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Who owns launch?", `active-storage-${method}`));
    vi.mocked(actOnReview).mockRejectedValueOnce(new ApiError(503, "Connection lost", {})).mockResolvedValueOnce({ thought: answered, workbench: accepted });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()}/>);
    const answer = await screen.findByRole("textbox", { name: "Your answer" });
    fireEvent.change(answer, { target: { value: "Mina owns launch." } });
    vi.spyOn(Storage.prototype, method).mockImplementation(() => { throw new Error("Storage denied"); });
    fireEvent.click(screen.getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(actOnReview).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("button", { name: "Add to note" })).toBeEnabled());
    expect(answer).toHaveValue("Mina owns launch.");
    const id = vi.mocked(actOnReview).mock.calls[0][0].request_id;
    fireEvent.click(screen.getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("Mina owns launch."));
    expect(vi.mocked(actOnReview).mock.calls[1][0].request_id).toBe(id);
  });

  it("installs the accepted active answer when request cleanup refuses", async () => {
    const answered = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "Accepted active answer" } };
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Who owns launch?", "active-storage-remove"));
    vi.mocked(actOnReview).mockResolvedValue({ thought: answered, workbench: projection({ thought: answered, workspace_cursor: { ...cursor, aggregate_revision: 4, continuity_revision: 5 } }) });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()}/>);
    fireEvent.change(await screen.findByRole("textbox", { name: "Your answer" }), { target: { value: "Mina" } });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => { throw new Error("Storage denied"); });
    fireEvent.click(screen.getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("Accepted active answer"));
    expect(screen.queryByText(/Storage denied/)).toBeNull();
    expect(screen.queryByRole("textbox", { name: "Your answer" })).toBeNull();
  });

  it("keeps an idle note plain: the foot is Ask about this, Find the tasks, Send… and Done, and Done is the one primary", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const ask = await screen.findByRole("button", { name: "Ask about this" });
    expect(screen.queryByRole("region", { name: "Ask about this note" })).not.toBeInTheDocument();
    expect(screen.queryByText("ONE QUESTION")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Your answer" })).not.toBeInTheDocument();
    expect(ask).not.toHaveClass("btn--primary");

    // Betterment Q8: Add a note (the Reads well), Copy, Task, Finish and
    // Resume left the face; no engine line for a note that is not running.
    const foot = [...document.querySelectorAll(".thought-note-foot button")].map((button) => button.textContent);
    expect(foot).toEqual(["Ask about this", "Find the tasks", "Send…", "Done"]);
    expect(screen.queryByText(/Reads:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Attached/)).not.toBeInTheDocument();

    const primaries = document.querySelectorAll(".btn--primary");
    expect(primaries).toHaveLength(1);
    expect(primaries[0]).toHaveTextContent("Done");
    expect(screen.queryByText(/IN A DRAWER|NOT IN A DRAWER|FINISHED/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Filed|Saved/)).not.toBeInTheDocument();

    // The window that was two features is one: no tabs, no rail, no rack.
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Interview/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Interview" })).not.toBeInTheDocument();
  });

  it("keeps an idle ready note plain and puts Ask in the foot", async () => {
    engineMock.useEngine.mockReturnValue({ state: "set", model: "Thought Qwen", place: "LAN" });
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    expect(await screen.findByRole("button", { name: "Ask about this" })).toBeEnabled();
    expect(screen.queryByRole("region", { name: "Ask about this note" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(useDesk.getState().askOpen).toBe(true));
    // Betterment Q5: Ask about this puts the note in About.
    expect(useDesk.getState().askThread?.about?.map((chip) => chip.ref)).toEqual(["note:note-1"]);
  });

  it("opens no Ask when the authoritative Note save fails", async () => {
    const body = "First line\nA selected passage";
    const selected = { ...thought, working_note: { ...thought.working_note, body_markdown: "First line" } };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({ thought: selected }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockRejectedValue(new Error("offline"));
    render(<ThoughtWorkspaceWindow object={object} thought={selected} onClose={vi.fn()} />);

    const noteBody = await screen.findByRole("textbox", { name: "Note body" });
    fireEvent.change(noteBody, { target: { value: body } });
    fireEvent.click(screen.getByTestId("select-second-line"));
    fireEvent.click(screen.getByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1));
    expect(useDesk.getState().askOpen).toBe(false);
  });

  it("hands Ask the canonical Note and the selected passage after a successful save", async () => {
    const body = "First line\nAsk about this exact passage";
    const selected = { ...thought, working_note: { ...thought.working_note, body_markdown: "First line" } };
    const saved = { ...selected, aggregate_revision: 4, working_revision: 3, working_note: { ...selected.working_note, body_markdown: body } };
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({ thought: selected }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(async (current, patch) => ({ thought: { ...current, ...saved, working_note: { ...current.working_note, ...saved.working_note, body_markdown: patch.body_markdown ?? current.working_note.body_markdown } }, workbench: projection({ thought: saved }) }));
    render(<ThoughtWorkspaceWindow object={object} thought={selected} onClose={vi.fn()} />);

    const noteBody = await screen.findByRole("textbox", { name: "Note body" });
    fireEvent.change(noteBody, { target: { value: body } });
    fireEvent.click(screen.getByTestId("select-second-line"));
    fireEvent.click(screen.getByRole("button", { name: "Ask about this" }));

    await waitFor(() => expect(useDesk.getState().askOpen).toBe(true));
    // Betterment Q5: Ask about this puts the note in About.
    expect(useDesk.getState().askThread?.about?.map((chip) => chip.ref)).toEqual(["note:note-1"]);
    expect(takeAskSelection()).toEqual({ noteRef: "note:note-1", text: "Ask about this exact passage", source: { id: "note-1", kind: "note", ref: "note:note-1", title: saved.working_note.title || "Note" } });
  });

  it("hands Ask the saved Note source when no passage is selected", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(useDesk.getState().askOpen).toBe(true));
    expect(takeAskSelection()).toEqual({
      noteRef: `note:${thought.working_note.id}`,
      text: "",
      source: { id: thought.working_note.id, kind: "note", ref: `note:${thought.working_note.id}`, title: thought.working_note.title || "Note" },
    });
  });

  it("never renders a heading over an empty question", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("   "));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    await screen.findByRole("region", { name: "Note" });
    // The defect the owner shot: a kicker over an h2 that renders nothing.
    const headings = [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")];
    expect(headings.filter((node) => !node.textContent?.trim())).toHaveLength(0);
    expect(headings).toHaveLength(0);
    expect(screen.queryByRole("region", { name: "Ask about this note" })).not.toBeInTheDocument();
    const texts = document.querySelectorAll(".thought-note-ask-text");
    expect(texts).toHaveLength(0);
    for (const node of document.querySelectorAll(".thought-note-ask *")) {
      expect(node.textContent?.trim().length === 0 && node.children.length === 0 && node.tagName !== "IMG").toBe(false);
    }
  });

  it("shows an older thought's open question with one verb", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Who is misunderstanding what?"));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const band = await screen.findByRole("region", { name: "Ask about this note" });
    expect(band).toHaveTextContent("Who is misunderstanding what?");
    expect(band.querySelector(".gadget-chip-egress")).toBeNull();
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

    const band = await screen.findByRole("region", { name: "Ask about this note" });
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
    await waitFor(() => expect(screen.getByRole("button", { name: "Ask about this" })).toBeEnabled());
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

/* The window's name follows the draft at once, ALSO after an autosave
 * (Astra, #821): the save gives the thought the title `Ask Priya` (its first
 * words); the owner types on, and the name must follow. The fence renders the
 * real window and the real writer; the hub's save is the double. */
describe("ThoughtWorkspaceWindow: the name follows the draft across a save", () => {
  it("type, save, type again: the name is the first words each time", async () => {
    vi.useFakeTimers();
    const fresh = { ...thought, working_note: { ...thought.working_note, title: "Thought", body_markdown: "" } } as Thought;
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection({ thought: fresh }));
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(async (current, patch) => {
      const saved = { ...current, aggregate_revision: current.aggregate_revision + 1, working_revision: current.working_revision + 1,
        working_note: { ...current.working_note, title: patch.title ?? current.working_note.title, body_markdown: patch.body_markdown ?? "" } } as Thought;
      return { thought: saved, workbench: projection({ thought: saved, workspace_cursor: { ...cursor, aggregate_revision: saved.aggregate_revision } }) };
    });
    render(<ThoughtWorkspaceWindow object={object} thought={fresh} onClose={vi.fn()} />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    const name = () => screen.getByRole("region", { name: "Thought" }).getAttribute("data-window-name");
    expect(name()).toBe("New note");

    const body = screen.getByRole("textbox", { name: "Note body" });
    fireEvent.change(body, { target: { value: "Ask Priya" } });
    expect(name()).toBe("Ask Priya");

    await act(async () => { await vi.advanceTimersByTimeAsync(600); await Promise.resolve(); await Promise.resolve(); });
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1);
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[0][1].title).toBe("Ask Priya");
    expect(screen.getByTestId("note-title")).toHaveTextContent("Ask Priya");
    expect(name()).toBe("Ask Priya");

    // The owner types on BEFORE the next save: the name follows at once.
    fireEvent.change(body, { target: { value: "Ask Priya about the freeze window" } });
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1);
    expect(name()).toBe("Ask Priya about the freeze window");
  });
});

describe("ThoughtWorkspaceWindow — PHILO-17 U08: the thought is sendable", () => {
  it("lets Send own the body and returns through Back to the same note and Send focus", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    const send = await screen.findByRole("button", { name: "Send…" });
    expect(screen.queryByTestId("send-well")).not.toBeInTheDocument();

    fireEvent.click(send);
    const well = await screen.findByTestId("send-well");
    expect(well).toHaveAttribute("data-doc", "note:note-1");
    expect(well).toHaveAttribute("data-version", "2");
    expect(screen.queryByRole("textbox", { name: "Note body" })).not.toBeInTheDocument();
    expect(document.querySelector(".thought-note-foot")).toBeNull();
    expect(screen.queryByRole("button", { name: "Done" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send…" })).not.toBeInTheDocument();
    expect(document.querySelector(".thought-send-foot")).toHaveTextContent("Back");
    expect(screen.getByRole("region", { name: "Thought" })).toHaveAttribute("data-frame-min-height", "520");
    expect(well.closest(".thought-send-body")).not.toHaveAttribute("inert");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    await waitFor(() => expect(screen.queryByTestId("send-well")).not.toBeInTheDocument());
    expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue(thought.working_note.body_markdown);
    expect(screen.getByRole("region", { name: "Thought" })).toHaveAttribute("data-frame-min-height", "360");
    await waitFor(() => expect(screen.getByRole("button", { name: "Send…" })).toHaveFocus());
  });

  it("Back, edit, reopen waits for the saved revision before mounting the send body", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    const save = deferred<Awaited<ReturnType<typeof saveThoughtWorkingInWorkspace>>>();
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(() => save.promise);
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: "Send…" }));
    const well = await screen.findByTestId("send-well");
    expect(well).toHaveAttribute("data-version", "2");
    fireEvent.click(screen.getByRole("button", { name: "Back" }));

    fireEvent.change(screen.getByRole("textbox", { name: "Note body" }), { target: { value: "The revised words" } });
    fireEvent.click(screen.getByRole("button", { name: "Send…" }));
    await waitFor(() => expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("send-well")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("The revised words");

    await act(async () => {
      save.resolve({ thought: { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: "The revised words" } } });
    });
    expect(await screen.findByTestId("send-well")).toHaveAttribute("data-version", "3");
    expect(screen.getByTestId("send-well").closest(".thought-send-body")).not.toHaveAttribute("inert");
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("The revised words");
  });

  it("a failed save refuses Send and Close while keeping the draft and repair verb", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockRejectedValue(new Error("offline"));
    const onClose = vi.fn();
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={onClose} />);
    expect(screen.getByRole("button", { name: "Close window" }).closest("section")).toHaveAttribute("data-frame-close-guard", "true");

    fireEvent.click(await screen.findByRole("button", { name: "Send…" }));
    await screen.findByTestId("send-well");
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Note body" }), { target: { value: "An edit that cannot land" } });
    fireEvent.click(screen.getByRole("button", { name: "Send…" }));
    await screen.findByRole("button", { name: "Retry" });
    expect(screen.queryByTestId("send-well")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Note body" })).toHaveValue("An edit that cannot land");
    fireEvent.click(screen.getByRole("button", { name: "Close window" }));
    expect(onClose).not.toHaveBeenCalled();
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(1);
  });

  it("keyboard Send focuses its region without firing hidden Note commands", async () => {
    const user = userEvent.setup();
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    (await screen.findByRole("button", { name: "Send…" })).focus();
    await user.keyboard("{Enter}");
    const send = await screen.findByRole("region", { name: "Send note" });
    await waitFor(() => expect(send).toHaveFocus());
    expect(screen.queryByRole("textbox", { name: "Note body" })).not.toBeInTheDocument();
    await user.keyboard("{Meta>}{Enter}{/Meta}");
    expect(completeThought).not.toHaveBeenCalled();
    expect(refineThought).not.toHaveBeenCalled();
    expect(send).toHaveFocus();
  });

  it("frame Back returns from Send without closing or firing hidden Note shortcuts", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    const onClose = vi.fn();
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={onClose} />);

    fireEvent.click(await screen.findByRole("button", { name: "Send…" }));
    const well = await screen.findByTestId("send-well");
    fireEvent.keyDown(well, { key: "Enter", metaKey: true });
    expect(completeThought).not.toHaveBeenCalled();
    expect(refineThought).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Frame Back" }));
    expect(await screen.findByRole("textbox", { name: "Note body" })).toHaveValue(thought.working_note.body_markdown);
    expect(onClose).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByRole("button", { name: "Send…" })).toHaveFocus());

    fireEvent.click(screen.getByRole("button", { name: "Send…" }));
    await screen.findByTestId("send-well");
    fireEvent.click(screen.getByRole("button", { name: "Close window" }));
    await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
  });

  it("unmounts engine and answer bands during Send and retains the answer on Back", async () => {
    engineMock.useEngine.mockReturnValue({ state: "set", model: "Thought Qwen", place: "LAN" });
    vi.mocked(thoughtWorkbench).mockResolvedValue(questionProjection("Which report?"));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Your answer" }), { target: { value: "Tuesday report" } });
    fireEvent.click(screen.getByRole("button", { name: "Send…" }));
    await screen.findByTestId("send-well");
    expect(screen.queryByRole("textbox", { name: "Your answer" })).not.toBeInTheDocument();
    expect(document.querySelector(".thought-note-ask")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("textbox", { name: "Your answer" })).toHaveValue("Tuesday report");
  });

  it("phone frame Back finds the portaled More door and returns with its Send menu closed", async () => {
    vi.stubGlobal("matchMedia", () => ({ matches: true, media: "(max-width: 720px)", addEventListener: () => {}, removeEventListener: () => {} }));
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    const onClose = vi.fn();
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={onClose} />);

    fireEvent.click(await screen.findByRole("button", { name: "More actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Send…" }));
    await screen.findByTestId("send-well");
    expect(screen.queryByRole("button", { name: "Done" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Frame Back" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "More actions" })).toHaveFocus());
    expect(screen.getByRole("button", { name: "More actions" }).closest(".thought-note-window")).toBeNull();
    expect(screen.getByTestId("frame-foot")).toContainElement(screen.getByRole("button", { name: "More actions" }));
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "More actions" })).toHaveAttribute("aria-expanded", "false");
    expect(onClose).not.toHaveBeenCalled();
  });

});

/* Betterment Q8 (one note): Done closes the window and changes nothing else;
 * a note that grew in Ask (Add to note) reads again. */
describe("ThoughtWorkspaceWindow — Betterment Q8: one note", () => {
  it("Done saves the dirty note, then closes; it finishes nothing", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValue(projection());
    vi.mocked(saveThoughtWorkingInWorkspace).mockImplementation(async (current, patch) => ({ thought: { ...current, aggregate_revision: 4, working_revision: 3, working_note: { ...current.working_note, body_markdown: patch.body_markdown ?? "" } } }));
    const onClose = vi.fn();
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={onClose} />);

    fireEvent.change(await screen.findByRole("textbox", { name: "Note body" }), { target: { value: "Words kept before Done" } });
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[0][1].body_markdown).toBe("Words kept before Done");
    expect(completeThought).not.toHaveBeenCalled();
  });

  it("a note that grew in Ask reads again, and an unsaved draft is never replaced", async () => {
    const grown = { ...thought, aggregate_revision: 4, working_revision: 3, working_note: { ...thought.working_note, body_markdown: `${thought.working_note.body_markdown}\n\nThe answer Ask added.` } };
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(projection()).mockResolvedValue(projection({ thought: grown, workspace_cursor: { ...cursor, aggregate_revision: 4 } }));
    render(<ThoughtWorkspaceWindow object={object} thought={thought} onClose={vi.fn()} />);
    const body = await screen.findByRole("textbox", { name: "Note body" });

    // Another note grew: this window does not read again.
    act(() => { window.dispatchEvent(new CustomEvent(NOTE_GREW_EVENT, { detail: { noteId: "note-other" } })); });
    expect(thoughtWorkbench).toHaveBeenCalledTimes(1);

    act(() => { window.dispatchEvent(new CustomEvent(NOTE_GREW_EVENT, { detail: { noteId: "note-1" } })); });
    await waitFor(() => expect(body).toHaveValue(grown.working_note.body_markdown));
  });
});
