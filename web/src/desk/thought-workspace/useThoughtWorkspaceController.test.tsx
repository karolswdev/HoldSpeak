import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { thoughtWorkbench, type Thought, type ThoughtWorkspaceProjection } from "../thoughts";
import { useThoughtWorkspaceController } from "./useThoughtWorkspaceController";

vi.mock("../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../thoughts")>()),
  thoughtWorkbench: vi.fn(),
}));

const thought: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
  aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 0,
  working_note: { id: "note-1", title: "Restart", body_markdown: "Body", tags: [] }, filing_status: "filed",
};

function workbench(hub_id: string): ThoughtWorkspaceProjection {
  return {
    schema_version: 1,
    process_scope: { kind: "hub_local", hub_id, state: "available" },
    workspace_cursor: { hub_id, thought_id: thought.id, aggregate_revision: 1, continuity_revision: 1 },
    thought, workspace_state: "idle",
    actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["update_working"] },
    review: null, context_status: { summary: "None", state: "empty", repair_ref: null },
    inference: { availability: "ready", continuation_admission: "ready", intended_placement: null }, terminal_status: null,
  };
}

afterEach(() => vi.clearAllMocks());

describe("useThoughtWorkspaceController hub epoch", () => {
  it("fences a restarted hub until an explicit reload adopts it", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(workbench("hub-a"));
    const { result } = renderHook(() => useThoughtWorkspaceController(thought));
    await waitFor(() => expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-a"));

    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(workbench("hub-b"));
    await act(async () => { await result.current.reload(false); });
    expect(result.current.restartDetected).toBe(true);
    expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-a");

    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(workbench("hub-b"));
    await act(async () => { await result.current.reload(true); });
    expect(result.current.restartDetected).toBe(false);
    expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-b");
  });

  it("turns a foreign-hub mutation projection into the same explicit restart gate", async () => {
    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(workbench("hub-a"));
    const { result } = renderHook(() => useThoughtWorkspaceController(thought));
    await waitFor(() => expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-a"));

    act(() => { expect(result.current.install(workbench("hub-b"))).toBe(false); });
    expect(result.current.restartDetected).toBe(true);
    expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-a");

    vi.mocked(thoughtWorkbench).mockResolvedValueOnce(workbench("hub-b"));
    await act(async () => { await result.current.reload(true); });
    expect(result.current.projection?.workspace_cursor.hub_id).toBe("hub-b");
  });
});
