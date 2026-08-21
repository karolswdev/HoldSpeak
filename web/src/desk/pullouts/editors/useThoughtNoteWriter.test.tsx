import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { saveThoughtWorking, saveThoughtWorkingInWorkspace, type Thought, type ThoughtWorkspaceCursor, type ThoughtWorkspaceProjection } from "../../thoughts";
import { useThoughtNoteWriter } from "./useThoughtNoteWriter";

vi.mock("../../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../thoughts")>()),
  saveThoughtWorking: vi.fn(),
  saveThoughtWorkingInWorkspace: vi.fn(),
}));

const thought: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
  aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 1,
  working_note: { id: "note-1", title: "Before", body_markdown: "Body", tags: [] }, filing_status: "filed",
};
const cursor: ThoughtWorkspaceCursor = { hub_id: "hub-1", thought_id: thought.id, aggregate_revision: 1, continuity_revision: 1 };

function workbench(nextThought: Thought, nextCursor: ThoughtWorkspaceCursor): ThoughtWorkspaceProjection {
  return {
    schema_version: 1, process_scope: { kind: "hub_local", hub_id: nextCursor.hub_id, state: "available" }, workspace_cursor: nextCursor,
    thought: nextThought, workspace_state: "idle", actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["update_working", "attach_context", "complete"] },
    review: null, context_status: { summary: "None", state: "empty", repair_ref: null },
    inference: { availability: "ready", continuation_admission: "ready", intended_placement: null }, terminal_status: null,
  };
}

function Harness() {
  const writer = useThoughtNoteWriter({ thought, workspaceCursor: cursor, onThought: vi.fn(), onProjection: vi.fn() });
  return <input aria-label="Title" value={writer.draft.title} onChange={(event) => writer.edit({ title: event.target.value })} />;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

describe("useThoughtNoteWriter workspace cursor", () => {
  it("installs A's returned cursor synchronously before queued B drains", async () => {
    vi.useFakeTimers();
    const first = deferred<{ thought: Thought; workbench: ThoughtWorkspaceProjection }>();
    const afterA = { ...thought, aggregate_revision: 2, working_revision: 2, working_note: { ...thought.working_note, title: "A" } };
    const cursorA = { ...cursor, aggregate_revision: 2, continuity_revision: 2 };
    const afterB = { ...afterA, aggregate_revision: 3, working_revision: 3, working_note: { ...afterA.working_note, title: "B" } };
    vi.mocked(saveThoughtWorkingInWorkspace).mockReturnValueOnce(first.promise).mockResolvedValueOnce({ thought: afterB, workbench: workbench(afterB, { ...cursorA, aggregate_revision: 3, continuity_revision: 3 }) });
    render(<Harness />);

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "B" } });
    await act(async () => { first.resolve({ thought: afterA, workbench: workbench(afterA, cursorA) }); await Promise.resolve(); await vi.advanceTimersByTimeAsync(1); });

    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(2);
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[1][0]).toMatchObject({ aggregate_revision: 2, working_revision: 2 });
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[1][2]).toEqual(cursorA);
    expect(saveThoughtWorking).not.toHaveBeenCalled();
  });

  it("uses the hydrated same-authority cursor conflict and retries the retained draft once", async () => {
    vi.useFakeTimers();
    const advanced = thought;
    const advancedCursor = { ...cursor, continuity_revision: 3 };
    const advancedWorkbench = workbench(advanced, advancedCursor);
    const saved = { ...advanced, aggregate_revision: 2, working_revision: 2, working_note: { ...thought.working_note, title: "After race" } };
    const onCursorConflict = vi.fn().mockResolvedValue(advancedWorkbench);
    vi.mocked(saveThoughtWorkingInWorkspace)
      .mockRejectedValueOnce(new ApiError(409, "conflict", { error: "workspace_cursor_conflict", workbench: advancedWorkbench }))
      .mockResolvedValueOnce({ thought: saved, workbench: workbench(saved, { ...advancedCursor, aggregate_revision: 2, continuity_revision: 4 }) });
    function RaceHarness() {
      const writer = useThoughtNoteWriter({ thought, workspaceCursor: cursor, onThought: vi.fn(), onProjection: vi.fn(), onCursorConflict });
      return <input aria-label="Race title" value={writer.draft.title} onChange={(event) => writer.edit({ title: event.target.value })} />;
    }
    render(<RaceHarness />);
    fireEvent.change(screen.getByLabelText("Race title"), { target: { value: "After race" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(451); });

    expect(onCursorConflict).not.toHaveBeenCalled();
    expect(saveThoughtWorkingInWorkspace).toHaveBeenCalledTimes(2);
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[1][0]).toEqual(advanced);
    expect(vi.mocked(saveThoughtWorkingInWorkspace).mock.calls[1][2]).toEqual(advancedCursor);
  });
});
